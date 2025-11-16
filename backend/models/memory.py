"""Persistent memory models for user- and conversation-level preferences.

This provides a minimal per-user/per-conversation key-value store that can be
used by ChatWorkflow and Design Studio to persist long-term preferences and
project context.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base, JSONType


class UserMemory(Base):
    """Long-lived memory entry associated with a user and/or conversation.

    This is intentionally simple and schema-stable: each row captures a single
    "fact" or preference about the user, grouped by a coarse-grained topic.

    Example topics (non-exhaustive):
    - design_preferences
    - project_info
    - budget
    - home_constraints
    - feedback
    """

    __tablename__ = "user_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Ownership / scoping
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)

    # Memory content
    topic = Column(String(50), nullable=False)  # e.g. "design_preferences", "budget"
    key = Column(String(100), nullable=False)   # e.g. "style", "currency", "max_budget"
    value = Column(JSONType, nullable=False)    # Arbitrary JSON payload describing the fact

    # Provenance / quality
    source = Column(String(50), nullable=False, default="chat")  # chat | design_studio | system | other
    confidence = Column(Float, nullable=False, default=0.9)
    data_metadata = Column(JSONType, nullable=True)

    # Timestamps (duplicated here instead of TimestampMixin to keep Base import simple)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships (kept lightweight; we rarely traverse from memory back to user)
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        # Efficient lookups for a user's memories in a given topic / home
        Index("idx_user_memories_user_topic", "user_id", "topic"),
        Index("idx_user_memories_user_home_topic", "user_id", "home_id", "topic"),
        Index("idx_user_memories_conversation", "conversation_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return a prompt-friendly dictionary representation."""

        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "home_id": str(self.home_id) if self.home_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "topic": self.topic,
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "confidence": float(self.confidence) if self.confidence is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

