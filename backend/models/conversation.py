"""Conversation models for chat history and memory management."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Conversation(Base):
    """
    Conversation thread model.
    
    Represents a conversation session between a user and the AI assistant.
    """
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id"), nullable=True, index=True)
    
    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    summary = Column(Text, nullable=True)  # AI-generated summary
    persona = Column(String(20), nullable=True)  # 'homeowner' | 'diy_worker' | 'contractor'
    scenario = Column(String(50), nullable=True)  # 'contractor_quotes' | 'diy_project_plan'

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[user_id])
    home = relationship("Home", foreign_keys=[home_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_conversations_user_active", "user_id", "is_active"),
        Index("idx_conversations_home_active", "home_id", "is_active"),
        Index("idx_conversations_updated", "updated_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "home_id": str(self.home_id) if self.home_id else None,
            "title": self.title,
            "summary": self.summary,
            "persona": self.persona,
            "scenario": self.scenario,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }


class ConversationMessage(Base):
    """
    Individual message in a conversation.
    
    Stores both user messages and AI responses with metadata.
    """
    
    __tablename__ = "conversation_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Metadata
    intent = Column(String(50), nullable=True)  # Classified intent
    message_metadata = Column(JSON, nullable=True)  # Additional metadata (sources, actions, etc.)
    
    # Context used for this message
    context_sources = Column(JSON, nullable=True)  # List of context sources used
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_messages_role", "role"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "metadata": self.message_metadata,
            "context_sources": self.context_sources,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ConversationSummary(Base):
    """
    Periodic summaries of conversations for long-term memory.
    
    Used to maintain context in long conversations without loading all messages.
    """
    
    __tablename__ = "conversation_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Summary content
    summary_text = Column(Text, nullable=False)
    
    # Range of messages summarized
    start_message_id = Column(UUID(as_uuid=True), nullable=False)
    end_message_id = Column(UUID(as_uuid=True), nullable=False)
    message_count = Column(Integer, nullable=False)
    
    # Key topics and entities extracted
    key_topics = Column(JSON, nullable=True)  # List of main topics discussed
    entities_mentioned = Column(JSON, nullable=True)  # Rooms, materials, products mentioned
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_summaries_conversation", "conversation_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "summary_text": self.summary_text,
            "start_message_id": str(self.start_message_id),
            "end_message_id": str(self.end_message_id),
            "message_count": self.message_count,
            "key_topics": self.key_topics,
            "entities_mentioned": self.entities_mentioned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

