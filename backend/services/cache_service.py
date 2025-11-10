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

    # Default TTLs by cache type (seconds)
    DEFAULT_TTLS = {
        "rag_query": 300,           # 5 minutes
        "vision_analysis": 3600,    # 1 hour
        "product_search": 900,      # 15 minutes
        "contractor_search": 3600,  # 1 hour
        "youtube_search": 3600,     # 1 hour
        "design_analysis": 3600,    # 1 hour
        "embeddings": 86400,        # 24 hours
        "default": 300,             # 5 minutes
    }

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL (optional)
        """
        self.redis_client = None
        self.memory_cache = InMemoryCache()
        self.use_redis = False

        # Metrics
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0

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
                    self.hits += 1
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(value)
                else:
                    self.misses += 1
                    logger.debug(f"Cache MISS (Redis): {key}")
                    return None
            else:
                value = self.memory_cache.get(key)
                if value is not None:
                    self.hits += 1
                    logger.debug(f"Cache HIT (memory): {key}")
                else:
                    self.misses += 1
                    logger.debug(f"Cache MISS (memory): {key}")
                return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.misses += 1
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

            self.sets += 1
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
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

            self.deletes += 1
            logger.debug(f"Cache DELETE: {key}")
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

    def get_ttl_for_type(self, cache_type: str) -> int:
        """
        Get TTL for a specific cache type.

        Args:
            cache_type: Type of cache (rag_query, vision_analysis, etc.)

        Returns:
            TTL in seconds
        """
        return self.DEFAULT_TTLS.get(cache_type, self.DEFAULT_TTLS["default"])

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "rag_query:*")
        """
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis keys matching: {pattern}")

            # For memory cache, we'd need to iterate (not efficient, but works)
            # This is a limitation of the simple in-memory implementation
            logger.warning("Pattern invalidation not fully supported for in-memory cache")

        except Exception as e:
            logger.error(f"Error invalidating pattern: {e}")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        redis_info = {}
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info("stats")
                redis_info = {
                    "connected": True,
                    "total_keys": self.redis_client.dbsize(),
                    "used_memory": info.get("used_memory_human", "N/A"),
                }
            except Exception:
                redis_info = {"connected": False}

        return {
            "backend": "redis" if self.use_redis else "memory",
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache._cache),
            "redis": redis_info
        }


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

