"""
Caching service for HomeView AI API.

Supports both Redis and in-memory caching with automatic fallback.
"""

import json
import logging
import pickle
from typing import Any, Optional
from datetime import timedelta
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache implementation."""
    
    def __init__(self):
        """Initialize in-memory cache."""
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        import time
        
        if key not in self._cache:
            return None
        
        # Check expiry
        if key in self._expiry and self._expiry[key] < time.time():
            del self._cache[key]
            del self._expiry[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        import time
        
        self._cache[key] = value
        if ttl > 0:
            self._expiry[key] = time.time() + ttl
    
    def delete(self, key: str):
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    def clear(self):
        """Clear all cached values."""
        self._cache.clear()
        self._expiry.clear()
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and not expired
        """
        return self.get(key) is not None


class CacheService:
    """
    Caching service with Redis and in-memory fallback.
    
    Automatically falls back to in-memory cache if Redis is not available.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL (optional)
        """
        self.redis_client = None
        self.memory_cache = InMemoryCache()
        self.use_redis = False
        
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory cache: {e}")
                self.use_redis = False
        else:
            logger.info("Using in-memory cache (Redis URL not provided)")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                self.memory_cache.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def clear(self):
        """Clear all cached values."""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.exists(key) > 0
            else:
                return self.memory_cache.exists(key)
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def get_or_set(self, key: str, factory, ttl: int = 300) -> Any:
        """
        Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds
            
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get global cache service instance.
    
    Returns:
        Cache service instance
    """
    global _cache_service
    
    if _cache_service is None:
        import os
        redis_url = os.getenv("REDIS_URL")
        _cache_service = CacheService(redis_url)
    
    return _cache_service


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    
    # Hash long keys
    if len(key_string) > 200:
        return hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            # Compute value
            logger.debug(f"Cache miss: {key}")
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            # Compute value
            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

