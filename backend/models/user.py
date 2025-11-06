"""User models for HomeVision AI."""

import uuid
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from backend.models.base import Base, TimestampMixin, JSONType


class UserType(str, enum.Enum):
    """User type enumeration."""
    HOMEOWNER = "homeowner"
    CONTRACTOR = "contractor"
    DIY_WORKER = "diy_worker"
    ADMIN = "admin"


class SubscriptionTier(str, enum.Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class User(Base, TimestampMixin):
    """User model - represents both homeowners and contractors."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    user_type = Column(SQLEnum(UserType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Password hash (for authentication)
    password_hash = Column(String(255), nullable=True)
    
    # Relationships
    homeowner_profile = relationship("HomeownerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    contractor_profile = relationship("ContractorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    homes = relationship("Home", back_populates="owner", cascade="all, delete-orphan")


class HomeownerProfile(Base, TimestampMixin):
    """Homeowner profile with subscription and preferences."""
    __tablename__ = "homeowner_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Personal information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Subscription
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)

    # Preferences and metadata
    preferences = Column(JSONType, default={})  # Design preferences, notification settings, etc.
    
    # Relationships
    user = relationship("User", back_populates="homeowner_profile")


class ContractorProfile(Base, TimestampMixin):
    """Contractor profile with business information."""
    __tablename__ = "contractor_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Business information
    business_name = Column(String(255), nullable=False)
    license_number = Column(String(100))
    insurance_number = Column(String(100))
    phone = Column(String(20))
    
    # Service areas and specialties
    service_areas = Column(JSONType, default=[])  # List of postal codes or cities
    specialties = Column(JSONType, default=[])  # ['kitchen', 'bathroom', 'flooring', etc.]

    # Verification and ratings
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_date = Column(DateTime, nullable=True)
    average_rating = Column(String(10), default="0.0")  # Stored as string to avoid precision issues
    total_reviews = Column(String(10), default="0")

    # Business metadata
    business_data = Column(JSONType, default={})  # Portfolio, certifications, team size, etc.
    
    # Subscription
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="contractor_profile")

