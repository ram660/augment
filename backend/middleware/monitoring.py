"""
Monitoring middleware for HomeView AI API.

Automatically tracks request metrics and performance.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request metrics.
    
    Records:
    - Request duration
    - Status codes
    - Error rates
    - Endpoint-specific metrics
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and record metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Record start time
        start_time = time.time()
        
        # Get user ID if available
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        
        # Process request
        error_message = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request error: {e}", exc_info=True)
            status_code = 500
            error_message = str(e)
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            monitoring = get_monitoring_service()
            monitoring.record_request(
                path=request.url.path,
                method=request.method,
                status_code=status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                error=error_message
            )
            
            # Log slow requests
            if duration_ms > 1000:  # > 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration_ms:.2f}ms"
                )
        
        return response

