"""
Monitoring and metrics service for HomeView AI API.

Tracks API metrics, performance, and errors.
"""

import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    path: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    user_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class EndpointStats:
    """Statistics for an endpoint."""
    total_requests: int = 0
    total_errors: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration."""
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests


class MonitoringService:
    """
    Service for monitoring API metrics and performance.
    
    Tracks:
    - Request counts and durations
    - Error rates
    - Status code distributions
    - Endpoint-specific metrics
    """
    
    def __init__(self):
        """Initialize monitoring service."""
        self.start_time = time.time()
        self.endpoint_stats: Dict[str, EndpointStats] = defaultdict(EndpointStats)
        self.global_stats = EndpointStats()
        self.recent_errors: deque = deque(maxlen=100)
    
    def record_request(
        self,
        path: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Record a request metric.
        
        Args:
            path: Request path
            method: HTTP method
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            user_id: Optional user ID
            error: Optional error message
        """
        # Create metric
        metric = RequestMetrics(
            path=path,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            error=error
        )
        
        # Update endpoint stats
        endpoint_key = f"{method} {path}"
        stats = self.endpoint_stats[endpoint_key]
        
        stats.total_requests += 1
        stats.total_duration_ms += duration_ms
        stats.min_duration_ms = min(stats.min_duration_ms, duration_ms)
        stats.max_duration_ms = max(stats.max_duration_ms, duration_ms)
        stats.status_codes[status_code] += 1
        stats.recent_requests.append(metric)
        
        if status_code >= 400:
            stats.total_errors += 1
        
        # Update global stats
        self.global_stats.total_requests += 1
        self.global_stats.total_duration_ms += duration_ms
        self.global_stats.min_duration_ms = min(self.global_stats.min_duration_ms, duration_ms)
        self.global_stats.max_duration_ms = max(self.global_stats.max_duration_ms, duration_ms)
        self.global_stats.status_codes[status_code] += 1
        
        if status_code >= 400:
            self.global_stats.total_errors += 1
            self.recent_errors.append(metric)
    
    def get_metrics(self) -> Dict:
        """
        Get all metrics.
        
        Returns:
            Dictionary of metrics
        """
        uptime_seconds = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime_seconds,
            "global": {
                "total_requests": self.global_stats.total_requests,
                "total_errors": self.global_stats.total_errors,
                "error_rate": self.global_stats.error_rate,
                "avg_duration_ms": self.global_stats.avg_duration_ms,
                "min_duration_ms": self.global_stats.min_duration_ms if self.global_stats.min_duration_ms != float('inf') else 0,
                "max_duration_ms": self.global_stats.max_duration_ms,
                "status_codes": dict(self.global_stats.status_codes),
                "requests_per_second": self.global_stats.total_requests / uptime_seconds if uptime_seconds > 0 else 0
            },
            "endpoints": {
                endpoint: {
                    "total_requests": stats.total_requests,
                    "total_errors": stats.total_errors,
                    "error_rate": stats.error_rate,
                    "avg_duration_ms": stats.avg_duration_ms,
                    "min_duration_ms": stats.min_duration_ms if stats.min_duration_ms != float('inf') else 0,
                    "max_duration_ms": stats.max_duration_ms,
                    "status_codes": dict(stats.status_codes)
                }
                for endpoint, stats in self.endpoint_stats.items()
            },
            "recent_errors": [
                {
                    "path": error.path,
                    "method": error.method,
                    "status_code": error.status_code,
                    "duration_ms": error.duration_ms,
                    "timestamp": error.timestamp.isoformat(),
                    "error": error.error
                }
                for error in list(self.recent_errors)[-10:]  # Last 10 errors
            ]
        }
    
    def get_endpoint_metrics(self, path: str, method: str) -> Optional[Dict]:
        """
        Get metrics for a specific endpoint.
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            Endpoint metrics or None
        """
        endpoint_key = f"{method} {path}"
        
        if endpoint_key not in self.endpoint_stats:
            return None
        
        stats = self.endpoint_stats[endpoint_key]
        
        return {
            "endpoint": endpoint_key,
            "total_requests": stats.total_requests,
            "total_errors": stats.total_errors,
            "error_rate": stats.error_rate,
            "avg_duration_ms": stats.avg_duration_ms,
            "min_duration_ms": stats.min_duration_ms if stats.min_duration_ms != float('inf') else 0,
            "max_duration_ms": stats.max_duration_ms,
            "status_codes": dict(stats.status_codes),
            "recent_requests": [
                {
                    "status_code": req.status_code,
                    "duration_ms": req.duration_ms,
                    "timestamp": req.timestamp.isoformat()
                }
                for req in list(stats.recent_requests)[-10:]  # Last 10 requests
            ]
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.start_time = time.time()
        self.endpoint_stats.clear()
        self.global_stats = EndpointStats()
        self.recent_errors.clear()


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """
    Get global monitoring service instance.
    
    Returns:
        Monitoring service instance
    """
    global _monitoring_service
    
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    
    return _monitoring_service


class StructuredLogger:
    """
    Structured logging utility.
    
    Provides consistent logging format with context.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
    
    def log(
        self,
        level: str,
        message: str,
        **context
    ):
        """
        Log message with structured context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **context: Additional context fields
        """
        # Build structured log message
        log_data = {
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **context
        }
        
        # Format as JSON-like string
        log_message = f"{message} | " + " | ".join(
            f"{k}={v}" for k, v in context.items()
        )
        
        # Log at appropriate level
        log_method = getattr(self.logger, level.lower())
        log_method(log_message)
    
    def debug(self, message: str, **context):
        """Log debug message."""
        self.log("debug", message, **context)
    
    def info(self, message: str, **context):
        """Log info message."""
        self.log("info", message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message."""
        self.log("warning", message, **context)
    
    def error(self, message: str, **context):
        """Log error message."""
        self.log("error", message, **context)
    
    def critical(self, message: str, **context):
        """Log critical message."""
        self.log("critical", message, **context)

