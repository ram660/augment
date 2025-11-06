"""Knowledge and RAG-related models.

These tables support an agentic RAG workflow without assuming a specific
vector database. Embeddings are stored as JSON arrays (float list) for
maximum portability (SQLite/Postgres). Later, a pgvector migration can be
added if desired.
"""

import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin, JSONType, USE_SQLITE

try:
    # Optional pgvector support when using Postgres
    from pgvector.sqlalchemy import Vector as PgVector  # type: ignore
except Exception:
    PgVector = None


class FileAsset(Base, TimestampMixin):
    """Represents a file or URL used as a source (image, floor plan, doc)."""
    __tablename__ = "file_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Optional links back to domain entities
    home_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    room_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    floor_plan_id = Column(UUID(as_uuid=True), index=True, nullable=True)

    # Path/URL and metadata
    uri = Column(String(1024), nullable=False)  # local path or URL
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    checksum = Column(String(128))  # e.g., sha256
    # Use attribute name 'meta' to avoid clashing with SQLAlchemy's reserved 'metadata'
    meta = Column("metadata", JSONType, default={})


class KnowledgeDocument(Base, TimestampMixin):
    """Logical document aggregated from domain rows (e.g., a room summary)."""
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Scoping/filters
    home_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    room_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    floor_plan_id = Column(UUID(as_uuid=True), index=True, nullable=True)

    # Provenance
    source_type = Column(String(50), nullable=False)  # room|image_analysis|floor_plan|material|fixture|product
    source_id = Column(String(64), nullable=True)     # UUID as string for cross-db safety

    # Content
    title = Column(String(255))
    text = Column(JSONType, default={})  # {"format": "markdown|plain", "content": "..."}
    meta = Column("metadata", JSONType, default={})

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base, TimestampMixin):
    """Chunked text for embedding and retrieval."""
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index = Column(Integer, default=0)
    text = Column(String)  # raw text for retrieval
    meta = Column("metadata", JSONType, default={})

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class Embedding(Base, TimestampMixin):
    """Stores embeddings as JSON arrays by default; uses pgvector when available."""
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), index=True, nullable=False)
    model = Column(String(100), default="stub-embedding-v1")
    # Use pgvector when not on SQLite and pgvector is available; else JSON
    if not USE_SQLITE and PgVector is not None:
        vector = Column(PgVector(256))  # default dimension 256; adjust if using a different model
        dim = Column(Integer, default=256)
    else:
        vector = Column(JSONType, default=[])
        dim = Column(Integer, default=0)

    # Relationships
    chunk = relationship("KnowledgeChunk", back_populates="embedding")


class AgentTask(Base, TimestampMixin):
    """Track agent tasks and outcomes for transparency and reuse."""
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    room_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # pending|running|succeeded|failed
    params = Column(JSONType, default={})
    result = Column(JSONType, default={})


class AgentTrace(Base, TimestampMixin):
    """Fine-grained trace of agent tool calls and steps."""
    __tablename__ = "agent_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("agent_tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    step = Column(Integer, default=0)
    tool_name = Column(String(100))
    input = Column(JSONType, default={})
    output = Column(JSONType, default={})
    meta = Column("metadata", JSONType, default={})


class RetrievalLog(Base, TimestampMixin):
    """Log retrievals for analysis and evaluation."""
    __tablename__ = "retrieval_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(String)
    filters = Column(JSONType, default={})
    top_k = Column(Integer, default=5)
    results = Column(JSONType, default=[])  # [{chunk_id, score, document_id, source_type, source_id}, ...]
