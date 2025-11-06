"""
Product models for HomeView AI.

Models for products, dimensions, and product matching.
"""

import uuid
import enum
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin, JSONType


class ProductCategory(str, enum.Enum):
    """Product category enumeration."""
    FURNITURE = "furniture"
    APPLIANCE = "appliance"
    FIXTURE = "fixture"
    FLOORING = "flooring"
    PAINT = "paint"
    LIGHTING = "lighting"
    DECOR = "decor"
    HARDWARE = "hardware"
    MATERIAL = "material"
    OTHER = "other"


class DimensionUnit(str, enum.Enum):
    """Dimension unit enumeration."""
    INCHES = "inches"
    FEET = "feet"
    CENTIMETERS = "cm"
    METERS = "m"


class ProductCatalog(Base, TimestampMixin):
    """Product catalog model with dimensions and specifications for matching."""
    __tablename__ = "product_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    model_number = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    
    # Category and classification
    category = Column(SQLEnum(ProductCategory), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSONType, default=[])  # List of tags for search
    
    # Dimensions (all in inches for consistency)
    width = Column(Float, nullable=True)  # Width in inches
    height = Column(Float, nullable=True)  # Height in inches
    depth = Column(Float, nullable=True)  # Depth in inches
    weight = Column(Float, nullable=True)  # Weight in pounds
    dimension_unit = Column(SQLEnum(DimensionUnit), default=DimensionUnit.INCHES)
    
    # Pricing
    price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    
    # Availability
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, nullable=True)
    
    # URLs and images
    product_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    additional_images = Column(JSONType, default=[])  # List of image URLs
    
    # Specifications and features
    specifications = Column(JSONType, default={})  # Detailed specs
    features = Column(JSONType, default=[])  # List of features
    
    # Room compatibility
    suitable_rooms = Column(JSONType, default=[])  # List of room types
    style_tags = Column(JSONType, default=[])  # Design styles (modern, traditional, etc.)
    
    # Installation and requirements
    installation_required = Column(Boolean, default=False)
    clearance_required = Column(Float, nullable=True)  # Clearance in inches

    # Additional metadata
    product_metadata = Column(JSONType, default={})
    
    # Relationships
    matches = relationship("ProductMatch", back_populates="product", cascade="all, delete-orphan")


class ProductMatch(Base, TimestampMixin):
    """Product match results for rooms."""
    __tablename__ = "product_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    product_id = Column(UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id", ondelete="CASCADE"), nullable=False)
    
    # Match scores
    dimension_fit_score = Column(Float, nullable=False)  # 0.0 to 1.0
    style_match_score = Column(Float, nullable=False)  # 0.0 to 1.0
    overall_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Fit analysis
    will_fit = Column(Boolean, nullable=False)
    fit_analysis = Column(JSONType, default={})  # Detailed fit analysis
    
    # Recommendations
    is_recommended = Column(Boolean, default=False)
    recommendation_reason = Column(Text, nullable=True)
    
    # Alternative suggestions
    alternatives = Column(JSONType, default=[])  # List of alternative product IDs
    
    # Metadata
    match_metadata = Column(JSONType, default={})
    
    # Relationships
    product = relationship("ProductCatalog", back_populates="matches")


class ProductReview(Base, TimestampMixin):
    """Product reviews and ratings."""
    __tablename__ = "product_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    product_id = Column(UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Rating
    rating = Column(Integer, nullable=False)  # 1-5 stars
    
    # Review content
    title = Column(String(255), nullable=True)
    review_text = Column(Text, nullable=True)
    
    # Verification
    verified_purchase = Column(Boolean, default=False)
    
    # Helpful votes
    helpful_count = Column(Integer, default=0)
    
    # Images
    review_images = Column(JSONType, default=[])  # List of image URLs
    
    # Metadata
    review_metadata = Column(JSONType, default={})


class ProductCollection(Base, TimestampMixin):
    """Product collections and bundles."""
    __tablename__ = "product_collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Collection information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Collection type
    collection_type = Column(String(50), nullable=True)  # bundle, set, room_package, etc.
    
    # Products in collection
    product_ids = Column(JSONType, default=[])  # List of product IDs
    
    # Pricing
    total_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)
    
    # Metadata
    collection_metadata = Column(JSONType, default={})

