"""
Database configuration and session management.

This module provides database connectivity and session management
for both synchronous and asynchronous operations.
"""

# Import everything from base for backward compatibility
from backend.models.base import (
    Base,
    engine,
    async_engine,
    SessionLocal,
    AsyncSessionLocal,
    get_db,
    get_async_db,
    init_db,
    init_db_async,
    DATABASE_URL,
    DATABASE_URL_ASYNC,
    USE_SQLITE,
    JSONType
)

__all__ = [
    "Base",
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db",
    "get_async_db",
    "init_db",
    "init_db_async",
    "DATABASE_URL",
    "DATABASE_URL_ASYNC",
    "USE_SQLITE",
    "JSONType"
]

