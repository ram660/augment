"""
Feature flag service for gradual rollouts, A/B testing, and emergency feature disabling.

Features:
- Boolean flags (on/off)
- Percentage rollouts (0-100%)
- User-based targeting
- Environment-based flags
- A/B test variants
- Emergency kill switches
- Flag change history
"""
import logging
import os
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random

logger = logging.getLogger(__name__)


class FlagType(Enum):
    """Type of feature flag."""
    BOOLEAN = "boolean"           # Simple on/off
    PERCENTAGE = "percentage"     # Gradual rollout (0-100%)
    USER_LIST = "user_list"       # Specific users
    AB_TEST = "ab_test"           # A/B test variants
    ENVIRONMENT = "environment"   # Environment-specific


@dataclass
class FeatureFlag:
    """Feature flag configuration."""
    name: str
    flag_type: FlagType
    enabled: bool = True
    description: str = ""
    
    # Percentage rollout (0-100)
    rollout_percentage: int = 100
    
    # User targeting
    enabled_users: Set[str] = field(default_factory=set)
    disabled_users: Set[str] = field(default_factory=set)
    
    # A/B test variants
    variants: Dict[str, int] = field(default_factory=dict)  # variant_name -> percentage
    
    # Environment targeting
    enabled_environments: Set[str] = field(default_factory=set)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)


class FeatureFlagService:
    """
    Service for managing feature flags.
    
    Features:
    - Multiple flag types (boolean, percentage, user-based, A/B test)
    - Environment-based flags
    - User targeting
    - Gradual rollouts
    - Emergency kill switches
    """
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize feature flag service.
        
        Args:
            environment: Current environment (dev, staging, prod)
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")
        self.flags: Dict[str, FeatureFlag] = {}
        self.evaluation_cache: Dict[str, Any] = {}
        
        # Metrics
        self.evaluations = 0
        self.cache_hits = 0
        
        # Setup default flags
        self._setup_default_flags()
    
    def _setup_default_flags(self):
        """Setup default feature flags."""
        # DeepSeek VL2 integration
        self.flags["deepseek_vision"] = FeatureFlag(
            name="deepseek_vision",
            flag_type=FlagType.PERCENTAGE,
            enabled=True,
            description="Use DeepSeek VL2 for vision analysis (cost optimization)",
            rollout_percentage=0,  # Start at 0%, gradually increase
            tags=["vision", "cost-optimization", "ai-model"]
        )
        
        # Google Search grounding
        self.flags["google_search_grounding"] = FeatureFlag(
            name="google_search_grounding",
            flag_type=FlagType.BOOLEAN,
            enabled=True,
            description="Enable Google Search grounding for product recommendations",
            tags=["search", "grounding", "products"]
        )
        
        # YouTube search
        self.flags["youtube_tutorials"] = FeatureFlag(
            name="youtube_tutorials",
            flag_type=FlagType.BOOLEAN,
            enabled=True,
            description="Enable YouTube tutorial search for DIY projects",
            tags=["search", "youtube", "diy"]
        )
        
        # Contractor search
        self.flags["contractor_search"] = FeatureFlag(
            name="contractor_search",
            flag_type=FlagType.BOOLEAN,
            enabled=True,
            description="Enable contractor search via Google Maps grounding",
            tags=["search", "contractors", "grounding"]
        )
        
        # PDF export
        self.flags["pdf_export"] = FeatureFlag(
            name="pdf_export",
            flag_type=FlagType.BOOLEAN,
            enabled=True,
            description="Enable PDF export for project plans",
            tags=["export", "pdf"]
        )
        
        # RAG caching
        self.flags["rag_caching"] = FeatureFlag(
            name="rag_caching",
            flag_type=FlagType.PERCENTAGE,
            enabled=True,
            description="Cache RAG query results to reduce costs",
            rollout_percentage=100,
            tags=["caching", "cost-optimization", "rag"]
        )
        
        # Vision caching
        self.flags["vision_caching"] = FeatureFlag(
            name="vision_caching",
            flag_type=FlagType.PERCENTAGE,
            enabled=True,
            description="Cache vision analysis results to reduce costs",
            rollout_percentage=100,
            tags=["caching", "cost-optimization", "vision"]
        )
        
        # Advanced design features
        self.flags["advanced_design_features"] = FeatureFlag(
            name="advanced_design_features",
            flag_type=FlagType.USER_LIST,
            enabled=True,
            description="Advanced design transformation features (beta)",
            enabled_users=set(),  # Add beta users here
            tags=["design", "beta"]
        )
        
        # A/B test: Prompt strategy
        self.flags["prompt_strategy"] = FeatureFlag(
            name="prompt_strategy",
            flag_type=FlagType.AB_TEST,
            enabled=True,
            description="A/B test for different prompt strategies",
            variants={
                "control": 50,      # Original prompts
                "detailed": 50,     # More detailed prompts
            },
            tags=["ab-test", "prompts"]
        )
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            user_id: User ID for user-based targeting
            context: Additional context for evaluation
            
        Returns:
            True if flag is enabled, False otherwise
        """
        self.evaluations += 1
        
        # Check cache
        cache_key = f"{flag_name}:{user_id or 'anonymous'}"
        if cache_key in self.evaluation_cache:
            self.cache_hits += 1
            return self.evaluation_cache[cache_key]
        
        # Get flag
        flag = self.flags.get(flag_name)
        if not flag:
            logger.warning(f"Feature flag '{flag_name}' not found, defaulting to False")
            return False
        
        # Check if flag is globally disabled
        if not flag.enabled:
            self.evaluation_cache[cache_key] = False
            return False
        
        # Check environment targeting
        if flag.enabled_environments and self.environment not in flag.enabled_environments:
            self.evaluation_cache[cache_key] = False
            return False
        
        # Check user-based targeting
        if user_id:
            if user_id in flag.disabled_users:
                self.evaluation_cache[cache_key] = False
                return False
            
            if flag.enabled_users and user_id in flag.enabled_users:
                self.evaluation_cache[cache_key] = True
                return True
        
        # Check percentage rollout
        if flag.flag_type == FlagType.PERCENTAGE:
            # Use consistent hashing for user-based rollout
            if user_id:
                hash_value = hash(f"{flag_name}:{user_id}") % 100
                result = hash_value < flag.rollout_percentage
            else:
                # Random for anonymous users
                result = random.randint(0, 99) < flag.rollout_percentage
            
            self.evaluation_cache[cache_key] = result
            return result
        
        # Default to enabled
        self.evaluation_cache[cache_key] = True
        return True
    
    def get_variant(self, flag_name: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Get A/B test variant for a flag.
        
        Args:
            flag_name: Name of the feature flag
            user_id: User ID for consistent variant assignment
            
        Returns:
            Variant name or None
        """
        flag = self.flags.get(flag_name)
        if not flag or flag.flag_type != FlagType.AB_TEST:
            return None
        
        if not flag.enabled or not flag.variants:
            return None
        
        # Use consistent hashing for user-based variant assignment
        if user_id:
            hash_value = hash(f"{flag_name}:{user_id}") % 100
        else:
            hash_value = random.randint(0, 99)
        
        # Assign variant based on percentage ranges
        cumulative = 0
        for variant_name, percentage in flag.variants.items():
            cumulative += percentage
            if hash_value < cumulative:
                return variant_name
        
        # Fallback to first variant
        return list(flag.variants.keys())[0] if flag.variants else None
    
    def set_flag(self, flag_name: str, enabled: bool):
        """
        Enable or disable a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            enabled: Whether to enable the flag
        """
        if flag_name in self.flags:
            self.flags[flag_name].enabled = enabled
            self.flags[flag_name].updated_at = datetime.utcnow()
            self.evaluation_cache.clear()  # Clear cache
            logger.info(f"Feature flag '{flag_name}' set to {enabled}")
        else:
            logger.warning(f"Feature flag '{flag_name}' not found")
    
    def set_rollout_percentage(self, flag_name: str, percentage: int):
        """
        Set rollout percentage for a flag.
        
        Args:
            flag_name: Name of the feature flag
            percentage: Rollout percentage (0-100)
        """
        if flag_name in self.flags:
            flag = self.flags[flag_name]
            if flag.flag_type == FlagType.PERCENTAGE:
                flag.rollout_percentage = max(0, min(100, percentage))
                flag.updated_at = datetime.utcnow()
                self.evaluation_cache.clear()
                logger.info(f"Feature flag '{flag_name}' rollout set to {percentage}%")
            else:
                logger.warning(f"Feature flag '{flag_name}' is not a percentage flag")
        else:
            logger.warning(f"Feature flag '{flag_name}' not found")
    
    def add_user(self, flag_name: str, user_id: str):
        """
        Add user to enabled users list.
        
        Args:
            flag_name: Name of the feature flag
            user_id: User ID to add
        """
        if flag_name in self.flags:
            self.flags[flag_name].enabled_users.add(user_id)
            self.flags[flag_name].updated_at = datetime.utcnow()
            self.evaluation_cache.clear()
            logger.info(f"User '{user_id}' added to feature flag '{flag_name}'")
        else:
            logger.warning(f"Feature flag '{flag_name}' not found")
    
    def remove_user(self, flag_name: str, user_id: str):
        """
        Remove user from enabled users list.
        
        Args:
            flag_name: Name of the feature flag
            user_id: User ID to remove
        """
        if flag_name in self.flags:
            self.flags[flag_name].enabled_users.discard(user_id)
            self.flags[flag_name].updated_at = datetime.utcnow()
            self.evaluation_cache.clear()
            logger.info(f"User '{user_id}' removed from feature flag '{flag_name}'")
        else:
            logger.warning(f"Feature flag '{flag_name}' not found")
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Get all feature flags."""
        return {
            name: {
                "enabled": flag.enabled,
                "type": flag.flag_type.value,
                "description": flag.description,
                "rollout_percentage": flag.rollout_percentage if flag.flag_type == FlagType.PERCENTAGE else None,
                "variants": flag.variants if flag.flag_type == FlagType.AB_TEST else None,
                "tags": flag.tags,
                "updated_at": flag.updated_at.isoformat()
            }
            for name, flag in self.flags.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feature flag service statistics."""
        cache_hit_rate = (self.cache_hits / self.evaluations * 100) if self.evaluations > 0 else 0
        
        return {
            "total_flags": len(self.flags),
            "enabled_flags": sum(1 for f in self.flags.values() if f.enabled),
            "evaluations": self.evaluations,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "environment": self.environment
        }


# Singleton instance
_feature_flag_service: Optional[FeatureFlagService] = None


def get_feature_flag_service() -> FeatureFlagService:
    """Get or create the feature flag service singleton."""
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service

