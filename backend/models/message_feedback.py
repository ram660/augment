"""Message feedback model for Agent Lightning integration."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base


class MessageFeedback(Base):
    """
    User feedback on chat messages for reinforcement learning.
    
    Stores explicit user feedback (thumbs up/down, ratings) to improve
    agent responses through Agent Lightning.
    """
    
    __tablename__ = "message_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Message being rated
    message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # User who provided feedback
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Feedback type
    feedback_type = Column(String(50), nullable=False)  # thumbs_up, thumbs_down, rating_1-5, regenerate, copy, etc.
    
    # Rating (1-5 stars, optional)
    rating = Column(Integer, nullable=True)
    
    # Calculated reward score (0.0 to 1.0)
    reward_score = Column(Float, nullable=True)
    
    # Text feedback/comment
    comment = Column(Text, nullable=True)
    
    # Specific feedback flags
    helpful = Column(Boolean, nullable=True)
    accurate = Column(Boolean, nullable=True)
    complete = Column(Boolean, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("ConversationMessage", foreign_keys=[message_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    user = relationship("User", foreign_keys=[user_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "feedback_type": self.feedback_type,
            "rating": self.rating,
            "reward_score": self.reward_score,
            "comment": self.comment,
            "helpful": self.helpful,
            "accurate": self.accurate,
            "complete": self.complete,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

