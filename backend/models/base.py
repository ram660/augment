"""Base database configuration and utilities."""

import os
from datetime import datetime
from typing import Any, Generator, AsyncGenerator
from sqlalchemy import create_engine, Column, DateTime, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv

load_dotenv()

# Database URLs
# Railway provides DATABASE_URL automatically for PostgreSQL
# Use SQLite for local development if DATABASE_URL is not set or is SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

# Check if we should use SQLite or PostgreSQL
if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
    # Production: Use PostgreSQL (Railway provides this)
    USE_SQLITE = False
    JSONType = JSONB

    # Railway provides postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Create async URL by replacing postgresql:// with postgresql+asyncpg://
    DATABASE_URL_ASYNC = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # Development: Use SQLite
    USE_SQLITE = True
    JSONType = JSON

    # Use SQLite URL from env or default
    if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./homevision.db")

    # Use absolute path for async SQLite to avoid issues
    import pathlib
    db_path = pathlib.Path("./homevision.db").absolute()
    DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC", f"sqlite+aiosqlite:///{db_path}")

# Create engines
if USE_SQLITE:
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
    # For SQLite async, we need to ensure aiosqlite is available
    try:
        import aiosqlite
        async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=True, connect_args={"check_same_thread": False})
    except ImportError:
        print("Warning: aiosqlite not installed. Async operations will not be available.")
        async_engine = None
else:
    engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
    async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=True, pool_pre_ping=True)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Only create async session factory if async_engine is available
if async_engine is not None:
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
else:
    AsyncSessionLocal = None

# Base class for all models
Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def get_db() -> Generator[Session, None, None]:
    """Get synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)


async def init_db_async():
    """Initialize database asynchronously - create all tables."""
    async with async_engine.begin() as conn:
        # Enable pgvector extension when using Postgres
        if not USE_SQLITE:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception:
                # Extension may not be available or permissions missing; continue gracefully
                pass
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight schema evolutions for dev SQLite to avoid manual migrations
        if USE_SQLITE:
            try:
                res = await conn.exec_driver_sql("PRAGMA table_info(rooms)")
                cols = [row[1] for row in res.all()]
                if "floor_plan_id" not in cols:
                    await conn.exec_driver_sql("ALTER TABLE rooms ADD COLUMN floor_plan_id TEXT")
            except Exception:
                # Best-effort; if it fails, the API may still work where the column isn't used
                pass
        # Create ANN index for embeddings when pgvector is available (best-effort)
        if not USE_SQLITE:
            try:
                # ivfflat index for cosine distance; 'lists' can be tuned
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)"
                ))
            except Exception:
                # Safe to ignore if column type isn't pgvector or extension/index not available
                pass
            try:
                # Functional GIN index for full-text search on chunk text
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_text_fts ON knowledge_chunks USING GIN (to_tsvector('english', text))"
                ))
            except Exception:
                # Safe to ignore on non-Postgres or if permissions are missing
                pass

