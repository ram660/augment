"""
Database models for design studio features.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.models.base import Base


class DesignProject(Base):
    """Design project model."""
    
    __tablename__ = "design_projects"
    
    id = Column(String, primary_key=True)
    home_id = Column(String, ForeignKey("homes.id"), nullable=False)
    user_id = Column(String, nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    room_type = Column(String)  # kitchen, bedroom, living_room, etc.
    
    original_image_path = Column(String, nullable=False)
    original_image_url = Column(String)
    
    status = Column(String, default="draft")  # draft, in_progress, completed, archived
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transformations = relationship("DesignTransformation", back_populates="project", cascade="all, delete-orphan")
    variations = relationship("DesignVariation", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DesignProject(id={self.id}, name={self.name}, status={self.status})>"


class DesignTransformation(Base):
    """Design transformation model."""
    
    __tablename__ = "design_transformations"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("design_projects.id"), nullable=False)
    
    transformation_type = Column(String, nullable=False)  # style_transfer, room_redesign, etc.
    transformation_params = Column(JSON)
    
    original_image_path = Column(String, nullable=False)
    transformed_image_path = Column(String)
    transformed_image_url = Column(String)
    
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # AI analysis results
    design_analysis = Column(JSON)  # AI-generated design analysis
    quality_score = Column(Float)
    
    # Generation metadata
    generation_time_ms = Column(Float)
    model_used = Column(String)
    prompt_used = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("DesignProject", back_populates="transformations")
    
    def __repr__(self):
        return f"<DesignTransformation(id={self.id}, type={self.transformation_type}, status={self.status})>"


class DesignVariation(Base):
    """Design variation model."""
    
    __tablename__ = "design_variations"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("design_projects.id"), nullable=False)
    batch_id = Column(String)  # Group variations from same generation
    
    style = Column(String, nullable=False)
    style_description = Column(Text)
    
    image_path = Column(String, nullable=False)
    image_url = Column(String)
    
    quality_score = Column(Float)
    is_recommended = Column(Boolean, default=False)
    
    # User feedback
    user_rating = Column(Integer)  # 1-5 stars
    user_liked = Column(Boolean)
    user_feedback = Column(Text)
    
    # Generation metadata
    generation_params = Column(JSON)
    generation_time_ms = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("DesignProject", back_populates="variations")
    
    def __repr__(self):
        return f"<DesignVariation(id={self.id}, style={self.style}, score={self.quality_score})>"


class DesignComparison(Base):
    """Design comparison model for before/after visualizations."""
    
    __tablename__ = "design_comparisons"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("design_projects.id"), nullable=False)
    
    comparison_type = Column(String, nullable=False)  # side_by_side, stacked, grid, slider, timeline
    
    before_image_path = Column(String, nullable=False)
    after_image_path = Column(String, nullable=False)
    comparison_image_path = Column(String)
    comparison_image_url = Column(String)
    
    layout_config = Column(JSON)  # Layout configuration used
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DesignComparison(id={self.id}, type={self.comparison_type})>"


class StylePreferenceModel(Base):
    """User style preference model."""
    
    __tablename__ = "style_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    style_name = Column(String, nullable=False)
    
    preference_score = Column(Float, default=0.5)  # 0.0 to 1.0
    feedback_count = Column(Integer, default=0)
    
    # Context
    room_type = Column(String)  # If preference is room-specific
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<StylePreference(user={self.user_id}, style={self.style_name}, score={self.preference_score})>"


class DesignHistory(Base):
    """Design history timeline model."""
    
    __tablename__ = "design_history"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("design_projects.id"), nullable=False)
    
    event_type = Column(String, nullable=False)  # transformation, variation, comparison, feedback
    event_data = Column(JSON)
    
    image_path = Column(String)
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DesignHistory(id={self.id}, type={self.event_type})>"

