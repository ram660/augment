"""
Transformation models for storing design transformation history.

These models track all design transformations performed on room images,
including the parameters used and the resulting images.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from backend.models.base import Base, TimestampMixin


class TransformationType(str, enum.Enum):
    """Types of design transformations."""
    PAINT = "paint"
    FLOORING = "flooring"
    CABINETS = "cabinets"
    COUNTERTOPS = "countertops"
    BACKSPLASH = "backsplash"
    LIGHTING = "lighting"
    FURNITURE = "furniture"
    MULTI = "multi"  # Multiple transformations combined


class TransformationStatus(str, enum.Enum):
    """Status of a transformation request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transformation(Base, TimestampMixin):
    """
    Represents a design transformation request and its results.
    
    A transformation takes an original room image and applies AI-powered
    changes (paint, flooring, cabinets, etc.) while preserving unchanged elements.
    """
    __tablename__ = "transformations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source image
    room_image_id = Column(UUID(as_uuid=True), ForeignKey("room_images.id"), nullable=False)
    
    # Transformation details
    transformation_type = Column(SQLEnum(TransformationType), nullable=False)
    status = Column(SQLEnum(TransformationStatus), default=TransformationStatus.PENDING, nullable=False)
    
    # Parameters used for transformation (stored as JSON)
    # Example for paint: {"target_color": "soft gray", "target_finish": "matte", "walls_only": true}
    parameters = Column(JSON, nullable=False)
    
    # Number of variations requested
    num_variations = Column(Integer, default=4, nullable=False)
    
    # User who requested the transformation
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Optional for now
    
    # Error message if failed
    error_message = Column(String, nullable=True)
    
    # Processing time in seconds
    processing_time_seconds = Column(Integer, nullable=True)
    
    # Relationships
    room_image = relationship("RoomImage", back_populates="transformations")
    result_images = relationship(
        "TransformationImage",
        back_populates="transformation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Transformation {self.id} - {self.transformation_type.value} - {self.status.value}>"


class TransformationImage(Base, TimestampMixin):
    """
    Represents a single generated image from a transformation.
    
    Each transformation can generate 1-4 variations. This model stores
    each variation along with metadata.
    """
    __tablename__ = "transformation_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parent transformation
    transformation_id = Column(UUID(as_uuid=True), ForeignKey("transformations.id"), nullable=False)
    
    # Image storage
    image_url = Column(String, nullable=False)  # URL to stored image (S3/GCS)
    
    # Variation number (1-4)
    variation_number = Column(Integer, nullable=False)
    
    # User selection
    is_selected = Column(Boolean, default=False)  # User's favorite variation
    is_applied = Column(Boolean, default=False)  # User applied this transformation
    
    # Image metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Quality metrics (optional, for future use)
    quality_score = Column(Integer, nullable=True)  # 0-100
    
    # Relationships
    transformation = relationship("Transformation", back_populates="result_images")
    
    def __repr__(self):
        return f"<TransformationImage {self.id} - Variation {self.variation_number}>"


class TransformationFeedback(Base, TimestampMixin):
    """
    User feedback on transformation quality.
    
    Helps improve prompt engineering and transformation quality over time.
    """
    __tablename__ = "transformation_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transformation being rated
    transformation_id = Column(UUID(as_uuid=True), ForeignKey("transformations.id"), nullable=False)
    transformation_image_id = Column(UUID(as_uuid=True), ForeignKey("transformation_images.id"), nullable=True)
    
    # User who provided feedback
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Rating (1-5 stars)
    rating = Column(Integer, nullable=False)
    
    # Specific feedback categories
    accuracy_score = Column(Integer, nullable=True)  # How well it matched request (1-5)
    preservation_score = Column(Integer, nullable=True)  # How well unchanged elements preserved (1-5)
    realism_score = Column(Integer, nullable=True)  # How photorealistic (1-5)
    
    # Text feedback
    comment = Column(String, nullable=True)
    
    # Issues reported
    changed_wrong_elements = Column(Boolean, default=False)
    unrealistic_result = Column(Boolean, default=False)
    poor_quality = Column(Boolean, default=False)
    
    # Relationships
    transformation = relationship("Transformation")
    transformation_image = relationship("TransformationImage")
    
    def __repr__(self):
        return f"<TransformationFeedback {self.id} - Rating: {self.rating}/5>"


class TransformationTemplate(Base, TimestampMixin):
    """
    Pre-defined transformation packages for common scenarios.
    
    Examples:
    - "Modern Kitchen Refresh" (cabinets + countertops + backsplash)
    - "Living Room Makeover" (paint + flooring + furniture)
    - "Bathroom Update" (paint + fixtures + lighting)
    """
    __tablename__ = "transformation_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Room types this template applies to
    applicable_room_types = Column(JSON, nullable=False)  # ["kitchen", "bathroom"]
    
    # Transformation steps (ordered list)
    # Example: [
    #   {"type": "paint", "parameters": {...}},
    #   {"type": "flooring", "parameters": {...}}
    # ]
    transformation_steps = Column(JSON, nullable=False)
    
    # Popularity metrics
    usage_count = Column(Integer, default=0)
    average_rating = Column(Integer, nullable=True)
    
    # Visibility
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Creator
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    def __repr__(self):
        return f"<TransformationTemplate {self.name}>"

