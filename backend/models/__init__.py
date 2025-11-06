"""Database models for HomeVision AI."""

from backend.models.base import Base
from backend.models.user import User, HomeownerProfile, ContractorProfile, UserType, SubscriptionTier
from backend.models.home import (
    Home,
    Room,
    RoomImage,
    FloorPlan,
    SpatialData,
    Material,
    Fixture,
    Product,
    HomeType,
    RoomType,
    MaterialCategory
)
from backend.models.analysis import (
    FloorPlanAnalysis,
    RoomAnalysis,
    ImageAnalysis
)
from backend.models.knowledge import (
    FileAsset,
    KnowledgeDocument,
    KnowledgeChunk,
    Embedding,
    AgentTask,
    AgentTrace,
    RetrievalLog,
)
from backend.models.transformation import (
    Transformation,
    TransformationImage,
    TransformationFeedback,
    TransformationTemplate,
    TransformationType,
    TransformationStatus,
)
from backend.models.conversation import (
    Conversation,
    ConversationMessage,
    ConversationSummary,
)
from backend.models.design import (
    DesignProject,
    DesignTransformation,
    DesignVariation,
    DesignComparison,
    StylePreferenceModel,
    DesignHistory,
)
from backend.models.product import (
    ProductCatalog,
    ProductMatch,
    ProductReview,
    ProductCollection,
    ProductCategory,
    DimensionUnit,
)

__all__ = [
    "Base",
    "User",
    "UserType",
    "SubscriptionTier",
    "HomeownerProfile",
    "ContractorProfile",
    "Home",
    "HomeType",
    "Room",
    "RoomType",
    "RoomImage",
    "FloorPlan",
    "SpatialData",
    "Material",
    "MaterialCategory",
    "Fixture",
    "Product",
    "FloorPlanAnalysis",
    "RoomAnalysis",
    "ImageAnalysis",
    "FileAsset",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "Embedding",
    "AgentTask",
    "AgentTrace",
    "RetrievalLog",
    "Transformation",
    "TransformationImage",
    "TransformationFeedback",
    "TransformationTemplate",
    "TransformationType",
    "TransformationStatus",
    "Conversation",
    "ConversationMessage",
    "ConversationSummary",
    "DesignProject",
    "DesignTransformation",
    "DesignVariation",
    "DesignComparison",
    "StylePreferenceModel",
    "DesignHistory",
    "ProductCatalog",
    "ProductMatch",
    "ProductReview",
    "ProductCollection",
    "ProductCategory",
    "DimensionUnit",
]

