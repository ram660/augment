"""
Rate limiting middleware for HomeView AI API.

Implements token bucket algorithm for rate limiting.
"""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_retry_after(self) -> int:
        """
        Get seconds until next token is available.
        
        Returns:
            Seconds to wait
        """
        if self.tokens >= 1:
            return 0
        
        tokens_needed = 1 - self.tokens
        return int(tokens_needed / self.refill_rate) + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.
    
    Different rate limits for different user types:
    - Anonymous: 10 requests/minute
    - Authenticated: 60 requests/minute
    - Admin: 120 requests/minute
    """
    
    # Rate limits: (capacity, refill_rate per second)
    RATE_LIMITS = {
        "anonymous": (100, 100 / 60),      # 100 requests per minute (increased for development)
        "authenticated": (200, 200 / 60),  # 200 requests per minute
        "admin": (500, 500 / 60),          # 500 requests per minute
    }
    
    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/health/ready",
        "/health/live",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    def __init__(self, app):
        """Initialize rate limiter."""
        super().__init__(app)
        self.buckets: Dict[str, TokenBucket] = {}
        self.cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get user type from request
        user_type = self._get_user_type(request)
        
        # Get or create token bucket
        bucket_key = f"{client_id}:{user_type}"
        if bucket_key not in self.buckets:
            capacity, refill_rate = self.RATE_LIMITS[user_type]
            self.buckets[bucket_key] = TokenBucket(capacity, refill_rate)
        
        bucket = self.buckets[bucket_key]
        
        # Try to consume token
        if not bucket.consume():
            retry_after = bucket.get_retry_after()
            
            logger.warning(
                f"Rate limit exceeded for {client_id} ({user_type}). "
                f"Retry after {retry_after} seconds"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": self.RATE_LIMITS[user_type][0],
                    "window": "1 minute"
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.RATE_LIMITS[user_type][0]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        capacity, _ = self.RATE_LIMITS[user_type]
        response.headers["X-RateLimit-Limit"] = str(capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(bucket.last_refill + 60))
        
        # Periodic cleanup of old buckets
        self._cleanup_old_buckets()
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.
        
        Args:
            request: Incoming request
            
        Returns:
            Client identifier (IP address or user ID)
        """
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _get_user_type(self, request: Request) -> str:
        """
        Get user type from request.
        
        Args:
            request: Incoming request
            
        Returns:
            User type (anonymous, authenticated, admin)
        """
        # Check if user is authenticated
        if hasattr(request.state, "user_type"):
            user_type = request.state.user_type
            if user_type == "admin":
                return "admin"
            return "authenticated"
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return "authenticated"
        
        return "anonymous"
    
    def _cleanup_old_buckets(self):
        """Remove old token buckets to prevent memory leaks."""
        now = time.time()
        
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets that haven't been used in 10 minutes
        cutoff_time = now - 600
        old_buckets = [
            key for key, bucket in self.buckets.items()
            if bucket.last_refill < cutoff_time
        ]
        
        for key in old_buckets:
            del self.buckets[key]
        
        if old_buckets:
            logger.info(f"Cleaned up {len(old_buckets)} old rate limit buckets")
        
        self.last_cleanup = now


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple IP-based rate limiting middleware.
    
    Limits requests per IP address regardless of authentication.
    Useful for preventing DDoS attacks.
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize IP rate limiter.
        
        Args:
            app: FastAPI application
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with IP-based rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(',')[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Get current time
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"IP rate limit exceeded for {client_ip}")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests from this IP address",
                    "retry_after": self.window_seconds
                },
                headers={
                    "Retry-After": str(self.window_seconds)
                }
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        return await call_next(request)

