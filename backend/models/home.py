"""Home and room models for HomeVision AI."""

import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from backend.models.base import Base, TimestampMixin, JSONType


class HomeType(str, enum.Enum):
    """Home type enumeration."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    APARTMENT = "apartment"
    MULTI_FAMILY = "multi_family"
    OTHER = "other"


class RoomType(str, enum.Enum):
    """Room type enumeration."""
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    LIVING_AREA = "living_area"  # Variant of living room
    DINING_ROOM = "dining_room"
    DINING_AREA = "dining_area"  # Variant of dining room
    OFFICE = "office"
    LAUNDRY = "laundry"
    LAUNDRY_ROOM = "laundry_room"  # Variant
    GARAGE = "garage"
    BASEMENT = "basement"
    ATTIC = "attic"
    HALLWAY = "hallway"
    HALL = "hall"  # Variant of hallway
    CORRIDOR = "corridor"  # Another variant
    CLOSET = "closet"
    WALK_IN_CLOSET = "walk_in_closet"  # Variant
    FOYER = "foyer"
    ENTRYWAY = "entryway"
    ENTRY = "entry"  # Common variant of entryway
    MUDROOM = "mudroom"
    PANTRY = "pantry"
    UTILITY_ROOM = "utility_room"
    UTILITY = "utility"  # Variant
    SUNROOM = "sunroom"
    PORCH = "porch"
    BALCONY = "balcony"
    DECK = "deck"
    PATIO = "patio"  # Similar to deck
    FAMILY_ROOM = "family_room"
    DEN = "den"
    STUDY = "study"  # Similar to office/den
    LIBRARY = "library"
    GYM = "gym"
    EXERCISE_ROOM = "exercise_room"  # Variant of gym
    MEDIA_ROOM = "media_room"
    PLAYROOM = "playroom"
    GAME_ROOM = "game_room"  # Similar to playroom
    FLEX_ROOM = "flex_room"  # Generic flexible space
    FLEX = "flex"  # Short variant sometimes present in data
    STORAGE = "storage"
    STORAGE_ROOM = "storage_room"  # Variant
    MECHANICAL_ROOM = "mechanical_room"
    WINE_CELLAR = "wine_cellar"
    WORKSHOP = "workshop"
    GUEST_ROOM = "guest_room"  # Common room type
    MASTER_BEDROOM = "master_bedroom"  # Variant of bedroom
    POWDER_ROOM = "powder_room"  # Half bathroom
    NOOK = "nook"  # Breakfast nook, reading nook, etc.
    LOFT = "loft"  # Open upper floor area
    CONSERVATORY = "conservatory"  # Glass room
    OTHER = "other"


class MaterialCategory(str, enum.Enum):
    """Material category enumeration."""
    FLOORING = "flooring"
    WALL = "wall"
    CEILING = "ceiling"
    COUNTERTOP = "countertop"
    BACKSPLASH = "backsplash"
    CABINETRY = "cabinetry"
    TRIM = "trim"
    DOOR = "door"
    WINDOW = "window"
    OTHER = "other"


class Home(Base, TimestampMixin):
    """Home model - represents a physical home."""
    __tablename__ = "homes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=False)
    address = Column(JSONType, nullable=False)  # {street, city, province, postal_code, country}
    home_type = Column(SQLEnum(HomeType), default=HomeType.SINGLE_FAMILY, nullable=False)

    # Physical characteristics
    year_built = Column(Integer)
    square_footage = Column(Integer)
    num_bedrooms = Column(Integer)
    num_bathrooms = Column(Float)
    num_floors = Column(Integer, default=1)

    # Digital twin metadata
    digital_twin_completeness = Column(Float, default=0.0)  # 0.0 to 1.0
    last_updated_at = Column(String(50))  # ISO timestamp of last analysis
    extra_data = Column(JSONType, default={})  # Additional home characteristics

    # Relationships
    owner = relationship("User", back_populates="homes")
    rooms = relationship("Room", back_populates="home", cascade="all, delete-orphan")
    floor_plans = relationship("FloorPlan", back_populates="home", cascade="all, delete-orphan")


class Room(Base, TimestampMixin):
    """Room model - represents a room within a home."""
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=False)
    # Store as plain string for maximum compatibility with existing data (handles values like
    # "kitchen", "flex_room", as well as legacy uppercase names like "LIVING_ROOM")
    room_type = Column(String(50), default=RoomType.OTHER.value, nullable=False)
    floor_level = Column(Integer, default=1)
    # Optional direct link to originating floor plan for joins/filters
    floor_plan_id = Column(UUID(as_uuid=True), ForeignKey("floor_plans.id", ondelete="SET NULL"), nullable=True, index=True)

    # Dimensions
    length = Column(Float)  # in feet
    width = Column(Float)  # in feet
    height = Column(Float)  # in feet
    area = Column(Float)  # in square feet

    # Condition and quality
    condition_score = Column(Float)  # 0.0 to 1.0
    style = Column(String(100))  # modern, traditional, etc.

    # Metadata
    extra_data = Column(JSONType, default={})  # Additional room characteristics

    # Relationships
    home = relationship("Home", back_populates="rooms")
    images = relationship("RoomImage", back_populates="room", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="room", cascade="all, delete-orphan")
    fixtures = relationship("Fixture", back_populates="room", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="room", cascade="all, delete-orphan")
    spatial_data = relationship("SpatialData", back_populates="room", uselist=False, cascade="all, delete-orphan")
    analyses = relationship("RoomAnalysis", back_populates="room", cascade="all, delete-orphan")


class RoomImage(Base, TimestampMixin):
    """Room image model - stores photos of rooms."""
    __tablename__ = "room_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Image information
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(50), default="original")  # original, edited, rendered
    view_angle = Column(String(100))  # front, corner, ceiling, etc.

    # Analysis status
    is_analyzed = Column(Boolean, default=False)
    analysis_date = Column(String(50))  # ISO timestamp
    analysis_metadata = Column(JSONType, default={})  # Analysis configuration and results summary

    # Metadata
    file_size = Column(Integer)  # in bytes
    dimensions = Column(JSONType, default={})  # {width, height} in pixels

    # Relationships
    room = relationship("Room", back_populates="images")
    analyses = relationship("ImageAnalysis", back_populates="room_image", cascade="all, delete-orphan")
    transformations = relationship("Transformation", back_populates="room_image", cascade="all, delete-orphan")


class FloorPlan(Base, TimestampMixin):
    """Floor plan model - stores floor plan images."""
    __tablename__ = "floor_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Floor plan information
    name = Column(String(255))
    floor_level = Column(Integer, default=1)
    image_url = Column(String(500), nullable=False)
    scale = Column(String(100))  # e.g., "1/4 inch = 1 foot"

    # Analysis status
    is_analyzed = Column(Boolean, default=False)
    analysis_date = Column(String(50))  # ISO timestamp
    analysis_metadata = Column(JSONType, default={})  # Analysis configuration and results summary

    # Metadata
    file_size = Column(Integer)
    dimensions = Column(JSONType, default={})  # {width, height} in pixels

    # Relationships
    home = relationship("Home", back_populates="floor_plans")
    analyses = relationship("FloorPlanAnalysis", back_populates="floor_plan", cascade="all, delete-orphan")


class SpatialData(Base, TimestampMixin):
    """Spatial data model - stores detailed spatial information for rooms."""
    __tablename__ = "spatial_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Spatial relationships
    adjacent_rooms = Column(JSONType, default=[])  # List of room IDs
    spatial_relationships = Column(JSONType, default={})  # Detailed spatial relationships
    boundaries = Column(JSONType, default={})  # Room boundaries and coordinates

    # Detailed dimensions
    wall_dimensions = Column(JSONType, default={})  # Individual wall measurements
    ceiling_details = Column(JSONType, default={})  # Height variations, features
    floor_details = Column(JSONType, default={})  # Level changes, features

    # Features
    windows = Column(JSONType, default=[])  # Window locations and sizes
    doors = Column(JSONType, default=[])  # Door locations and types
    built_ins = Column(JSONType, default=[])  # Built-in features

    # Relationships
    room = relationship("Room", back_populates="spatial_data")


class Material(Base, TimestampMixin):
    """Material model - represents materials used in rooms."""
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Material information
    category = Column(SQLEnum(MaterialCategory), default=MaterialCategory.OTHER, nullable=False)
    material_type = Column(String(100), nullable=False)  # hardwood, tile, granite, etc.
    brand = Column(String(100))
    color = Column(String(100))
    finish = Column(String(100))  # matte, glossy, textured, etc.

    # Condition
    condition = Column(String(50))  # excellent, good, fair, poor
    age_years = Column(Integer)

    # Metadata
    extra_data = Column(JSONType, default={})  # Pattern, texture, installation date, etc.

    # Relationships
    room = relationship("Room", back_populates="materials")


class Fixture(Base, TimestampMixin):
    """Fixture model - represents fixtures in rooms."""
    __tablename__ = "fixtures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Fixture information
    fixture_type = Column(String(100), nullable=False)  # faucet, light, outlet, etc.
    brand = Column(String(100))
    model = Column(String(100))
    style = Column(String(100))
    finish = Column(String(100))
    location = Column(String(200))  # Description of where in the room

    # Condition
    condition = Column(String(50))  # excellent, good, fair, poor, needs_replacement
    installation_date = Column(String(50))  # ISO date

    # Metadata
    extra_data = Column(JSONType, default={})  # Specifications, features, etc.

    # Relationships
    room = relationship("Room", back_populates="fixtures")


class Product(Base, TimestampMixin):
    """Product model - represents identified products in rooms."""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Product information
    product_category = Column(String(100), nullable=False)  # appliance, furniture, decor, etc.
    product_type = Column(String(100), nullable=False)  # refrigerator, sofa, lamp, etc.
    brand = Column(String(100))
    model = Column(String(100))
    style = Column(String(100))
    color = Column(String(100))
    material = Column(String(100))

    # Dimensions and details
    dimensions = Column(JSONType, default={})  # {length, width, height}
    confidence_score = Column(Float)  # AI confidence in identification

    # Condition and value
    condition = Column(String(50))  # new, excellent, good, fair, poor
    estimated_age_years = Column(Integer)
    estimated_value = Column(Float)

    # Metadata
    extra_data = Column(JSONType, default={})  # Additional product characteristics

    # Relationships
    room = relationship("Room", back_populates="products")
