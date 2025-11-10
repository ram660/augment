"""Journey models for tracking user progress through home improvement projects."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON, Boolean, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from backend.models.base import Base, TimestampMixin, JSONType


class JourneyStatus(str, enum.Enum):
    """Status of a journey."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class StepStatus(str, enum.Enum):
    """Status of a journey step."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    NEEDS_ATTENTION = "needs_attention"


class Journey(Base, TimestampMixin):
    """
    User journey instance.
    
    Represents a user's progress through a home improvement project
    (e.g., kitchen renovation, bathroom upgrade, DIY project).
    """
    
    __tablename__ = "journeys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # Journey identification
    template_id = Column(String(100), nullable=False, index=True)  # e.g., "kitchen_renovation"
    title = Column(String(255), nullable=False)  # e.g., "Kitchen Renovation"
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(JourneyStatus), default=JourneyStatus.NOT_STARTED, nullable=False, index=True)
    current_step_id = Column(String(100), nullable=True)  # ID of current step
    
    # Progress tracking
    completed_steps = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=0, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    estimated_completion_date = Column(DateTime, nullable=True)
    
    # Metadata
    journey_metadata = Column(JSONType, default={})  # Additional journey-specific data
    
    # Collected data across all steps
    collected_data = Column(JSONType, default={})  # {images: [], decisions: [], budget: {}, etc.}
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    home = relationship("Home", foreign_keys=[home_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    steps = relationship("JourneyStep", back_populates="journey", cascade="all, delete-orphan", order_by="JourneyStep.step_number")
    
    # Indexes
    __table_args__ = (
        Index("idx_journeys_user_status", "user_id", "status"),
        Index("idx_journeys_template", "template_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "home_id": str(self.home_id) if self.home_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "current_step_id": self.current_step_id,
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "progress_percentage": self.progress_percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "estimated_completion_date": self.estimated_completion_date.isoformat() if self.estimated_completion_date else None,
            "metadata": self.journey_metadata,  # Fixed: use journey_metadata instead of metadata
            "collected_data": self.collected_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class JourneyStep(Base, TimestampMixin):
    """
    Individual step in a journey.
    
    Represents a single step in the user's journey with its own state,
    data, and images.
    """
    
    __tablename__ = "journey_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id"), nullable=False, index=True)
    
    # Step identification
    step_id = Column(String(100), nullable=False)  # e.g., "initial_consultation"
    step_number = Column(Integer, nullable=False)  # Order in journey (1, 2, 3, ...)
    name = Column(String(255), nullable=False)  # e.g., "Initial Consultation"
    description = Column(Text, nullable=True)
    
    # Step configuration
    required = Column(Boolean, default=True, nullable=False)
    estimated_duration_minutes = Column(Integer, default=10, nullable=False)
    
    # Dependencies
    depends_on = Column(JSONType, default=[])  # List of step_ids that must be completed first
    required_actions = Column(JSONType, default=[])  # List of actions required (e.g., ["upload_photos", "describe_goals"])
    
    # Status
    status = Column(SQLEnum(StepStatus), default=StepStatus.NOT_STARTED, nullable=False, index=True)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Data collected in this step
    step_data = Column(JSONType, default={})  # Step-specific data
    
    # Sub-steps
    sub_steps = Column(JSONType, default=[])  # List of sub-step objects
    
    # Relationships
    journey = relationship("Journey", back_populates="steps")
    images = relationship("JourneyImage", back_populates="step", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_journey_steps_journey_number", "journey_id", "step_number"),
        Index("idx_journey_steps_status", "status"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "journey_id": str(self.journey_id),
            "step_id": self.step_id,
            "step_number": self.step_number,
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "depends_on": self.depends_on,
            "required_actions": self.required_actions,
            "status": self.status.value if self.status else None,
            "progress_percentage": self.progress_percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "step_data": self.step_data,
            "sub_steps": self.sub_steps,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class JourneyImage(Base, TimestampMixin):
    """
    Image attached to a journey step.
    
    Stores images uploaded or generated during a journey step,
    with AI analysis and user annotations.
    """
    
    __tablename__ = "journey_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journeys.id"), nullable=False, index=True)
    step_id = Column(UUID(as_uuid=True), ForeignKey("journey_steps.id"), nullable=False, index=True)
    
    # Image storage
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path from uploads root
    url = Column(String(500), nullable=False)  # Public URL
    thumbnail_url = Column(String(500), nullable=True)  # Thumbnail URL
    
    # File metadata
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    width = Column(Integer, nullable=True)  # Image width in pixels
    height = Column(Integer, nullable=True)  # Image height in pixels
    
    # Image type
    is_generated = Column(Boolean, default=False, nullable=False)  # AI-generated vs uploaded
    image_type = Column(String(50), nullable=True)  # "original", "mockup", "product", "comparison"
    
    # AI Analysis
    analysis = Column(JSONType, default={})  # {description, detectedMaterials, detectedFixtures, style, condition}
    
    # User annotations
    label = Column(String(255), nullable=True)  # User-provided label
    notes = Column(Text, nullable=True)  # User notes
    tags = Column(JSONType, default=[])  # User tags

    # Display order
    display_order = Column(Integer, nullable=False, default=1)  # Order within step (1-based)

    # Relationships
    related_image_ids = Column(JSONType, default=[])  # IDs of related images (before/after pairs)
    replaced_by_id = Column(UUID(as_uuid=True), nullable=True)  # ID of image that replaced this one
    
    # Relationships
    journey = relationship("Journey", foreign_keys=[journey_id])
    step = relationship("JourneyStep", back_populates="images")
    
    # Indexes
    __table_args__ = (
        Index("idx_journey_images_journey", "journey_id"),
        Index("idx_journey_images_step", "step_id"),
        Index("ix_journey_images_step_order", "step_id", "display_order"),  # For efficient ordering
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "journey_id": str(self.journey_id),
            "step_id": str(self.step_id),
            "filename": self.filename,
            "file_path": self.file_path,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "is_generated": self.is_generated,
            "image_type": self.image_type,
            "analysis": self.analysis,
            "label": self.label,
            "notes": self.notes,
            "tags": self.tags,
            "display_order": self.display_order,
            "related_image_ids": self.related_image_ids,
            "replaced_by_id": str(self.replaced_by_id) if self.replaced_by_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

