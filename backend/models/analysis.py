"""Analysis models for storing AI-generated insights."""

import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin, JSONType


class FloorPlanAnalysis(Base, TimestampMixin):
    """Floor plan analysis results from AI."""
    __tablename__ = "floor_plan_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_plan_id = Column(UUID(as_uuid=True), ForeignKey("floor_plans.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Detected rooms
    detected_rooms = Column(JSONType, default=[])  # Array of room objects with type, dimensions, location
    room_count = Column(Integer, default=0)

    # Spatial analysis
    total_area = Column(Float)  # Total square footage
    layout_type = Column(String(100))  # open_concept, traditional, split_level, etc.
    spatial_efficiency = Column(Float)  # 0.0 to 1.0

    # Architectural features
    architectural_style = Column(String(100))  # modern, traditional, craftsman, etc.
    features = Column(JSONType, default=[])  # List of notable features

    # Dimensions and scale
    scale_info = Column(JSONType, default={})  # Scale information extracted from plan
    overall_dimensions = Column(JSONType, default={})  # Overall building dimensions

    # Analysis metadata
    confidence_score = Column(Float)  # Overall confidence in analysis
    analysis_notes = Column(Text)  # Additional notes from AI

    # Relationships
    floor_plan = relationship("FloorPlan", back_populates="analyses")


class RoomAnalysis(Base, TimestampMixin):
    """Room analysis results from AI."""
    __tablename__ = "room_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Room characteristics
    room_type_detected = Column(String(100))  # AI-detected room type
    style = Column(String(100))  # modern, traditional, farmhouse, etc.
    color_palette = Column(JSONType, default={})  # Dominant and accent colors

    # Condition assessment
    overall_condition = Column(String(50))  # excellent, good, fair, poor
    condition_score = Column(Float)  # 0.0 to 1.0
    condition_notes = Column(Text)  # Detailed condition observations

    # Detected elements
    materials_detected = Column(JSONType, default=[])  # List of detected materials
    fixtures_detected = Column(JSONType, default=[])  # List of detected fixtures
    products_detected = Column(JSONType, default=[])  # List of detected products

    # Recommendations
    improvement_suggestions = Column(JSONType, default=[])  # AI-generated suggestions
    estimated_renovation_priority = Column(String(50))  # low, medium, high, urgent

    # Analysis metadata
    confidence_score = Column(Float)  # Overall confidence in analysis
    analysis_notes = Column(Text)  # Additional notes from AI

    # Relationships
    room = relationship("Room", back_populates="analyses")


class ImageAnalysis(Base, TimestampMixin):
    """Image analysis results from AI."""
    __tablename__ = "image_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_image_id = Column(UUID(as_uuid=True), ForeignKey("room_images.id", ondelete="CASCADE"), nullable=False, index=True)

    # Visual analysis
    description = Column(Text)  # Natural language description of image
    keywords = Column(JSONType, default=[])  # Extracted keywords
    dominant_colors = Column(JSONType, default=[])  # Color analysis

    # Detected objects
    objects_detected = Column(JSONType, default=[])  # List of detected objects with bounding boxes
    materials_visible = Column(JSONType, default=[])  # Visible materials
    fixtures_visible = Column(JSONType, default=[])  # Visible fixtures

    # Quality assessment
    image_quality_score = Column(Float)  # 0.0 to 1.0
    lighting_quality = Column(String(50))  # excellent, good, fair, poor
    clarity = Column(String(50))  # sharp, acceptable, blurry

    # Spatial information
    view_angle = Column(String(100))  # front, corner, ceiling, detail, etc.
    estimated_coverage = Column(Float)  # Percentage of room visible (0.0 to 1.0)

    # Analysis metadata
    confidence_score = Column(Float)  # Overall confidence in analysis
    analysis_model = Column(String(100))  # Model used for analysis
    analysis_notes = Column(Text)  # Additional notes from AI

    # Relationships
    room_image = relationship("RoomImage", back_populates="analyses")
