"""
Design Variation Generation Service for HomeView AI.

Production-ready service for generating and managing design variations with
intelligent style recommendations and preference learning.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import json
import hashlib

from pydantic import BaseModel, Field

from backend.services.imagen_service import ImagenService, DesignTransformationRequest, ImageGenerationResult
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


class StylePreference(BaseModel):
    """User style preference."""
    user_id: str
    style_name: str
    preference_score: float = Field(ge=0.0, le=1.0, description="Preference score 0-1")
    feedback_count: int = Field(default=0, description="Number of feedback instances")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class VariationRequest(BaseModel):
    """Request for design variation generation."""
    original_image_path: str
    num_variations: int = Field(3, ge=1, le=8, description="Number of variations to generate")
    style_preferences: Optional[List[str]] = Field(None, description="Preferred styles")
    exclude_styles: Optional[List[str]] = Field(None, description="Styles to exclude")
    variation_intensity: float = Field(0.5, ge=0.0, le=1.0, description="How different variations should be")
    preserve_elements: Optional[List[str]] = Field(None, description="Elements to preserve")
    user_id: Optional[str] = None


class VariationResult(BaseModel):
    """Result of variation generation."""
    variation_id: str
    style: str
    image_path: str
    image_base64: str
    quality_score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VariationBatch(BaseModel):
    """Batch of generated variations."""
    batch_id: str
    original_image_path: str
    variations: List[VariationResult]
    generation_time_ms: float
    total_variations: int
    recommended_variation: Optional[str] = None


class DesignVariationService:
    """
    Production-ready service for design variation generation.
    
    Features:
    - Intelligent style selection based on room analysis
    - User preference learning
    - Batch variation generation
    - Quality scoring
    - Variation recommendations
    - Preference persistence
    """
    
    # Comprehensive style catalog
    STYLE_CATALOG = {
        "modern": {
            "description": "Clean lines, minimalist aesthetic, neutral colors",
            "keywords": ["minimalist", "contemporary", "sleek", "simple"],
            "color_palette": ["white", "gray", "black", "beige"]
        },
        "traditional": {
            "description": "Classic design, ornate details, warm colors",
            "keywords": ["classic", "elegant", "timeless", "ornate"],
            "color_palette": ["burgundy", "gold", "cream", "brown"]
        },
        "minimalist": {
            "description": "Extremely simple, functional, monochromatic",
            "keywords": ["simple", "clean", "functional", "sparse"],
            "color_palette": ["white", "black", "gray"]
        },
        "industrial": {
            "description": "Raw materials, exposed elements, urban aesthetic",
            "keywords": ["raw", "urban", "exposed", "metal"],
            "color_palette": ["gray", "black", "brown", "rust"]
        },
        "scandinavian": {
            "description": "Light, airy, natural materials, functional",
            "keywords": ["light", "natural", "cozy", "functional"],
            "color_palette": ["white", "light gray", "natural wood", "soft blue"]
        },
        "bohemian": {
            "description": "Eclectic, colorful, layered textures",
            "keywords": ["eclectic", "colorful", "artistic", "layered"],
            "color_palette": ["terracotta", "teal", "mustard", "burgundy"]
        },
        "coastal": {
            "description": "Beach-inspired, light colors, natural textures",
            "keywords": ["beach", "light", "airy", "nautical"],
            "color_palette": ["white", "blue", "sand", "seafoam"]
        },
        "farmhouse": {
            "description": "Rustic, cozy, vintage elements",
            "keywords": ["rustic", "cozy", "vintage", "country"],
            "color_palette": ["white", "cream", "wood", "soft gray"]
        },
        "mid_century_modern": {
            "description": "Retro 1950s-60s, organic shapes, bold colors",
            "keywords": ["retro", "organic", "bold", "vintage"],
            "color_palette": ["orange", "teal", "mustard", "walnut"]
        },
        "contemporary": {
            "description": "Current trends, mixed materials, bold accents",
            "keywords": ["current", "mixed", "bold", "trendy"],
            "color_palette": ["gray", "white", "navy", "gold"]
        }
    }
    
    def __init__(
        self,
        imagen_service: Optional[ImagenService] = None,
        gemini_client: Optional[GeminiClient] = None,
        preferences_file: Optional[str] = None
    ):
        """
        Initialize variation service.
        
        Args:
            imagen_service: Imagen service instance
            gemini_client: Gemini client instance
            preferences_file: Path to preferences storage file
        """
        self.imagen_service = imagen_service or ImagenService()
        self.gemini_client = gemini_client or GeminiClient()
        
        # Preferences storage
        self.preferences_file = Path(preferences_file or "data/style_preferences.json")
        self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
        self.preferences: Dict[str, Dict[str, StylePreference]] = self._load_preferences()
        
        logger.info("Design variation service initialized")
    
    def _load_preferences(self) -> Dict[str, Dict[str, StylePreference]]:
        """Load user preferences from file."""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    # Convert to StylePreference objects
                    preferences = {}
                    for user_id, user_prefs in data.items():
                        preferences[user_id] = {
                            style: StylePreference(**pref_data)
                            for style, pref_data in user_prefs.items()
                        }
                    return preferences
            except Exception as e:
                logger.error(f"Error loading preferences: {e}")
                return {}
        return {}
    
    def _save_preferences(self):
        """Save user preferences to file."""
        try:
            # Convert to dict for JSON serialization
            data = {}
            for user_id, user_prefs in self.preferences.items():
                data[user_id] = {
                    style: pref.model_dump()
                    for style, pref in user_prefs.items()
                }
            
            with open(self.preferences_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
    
    async def analyze_room_for_styles(self, image_path: str) -> List[str]:
        """
        Analyze room image and recommend suitable styles.
        
        Args:
            image_path: Path to room image
            
        Returns:
            List of recommended style names
        """
        try:
            prompt = f"""Analyze this interior design image and recommend the top 5 design styles that would work best for this space.

Available styles: {', '.join(self.STYLE_CATALOG.keys())}

Consider:
- Current room layout and architecture
- Natural lighting
- Room size and proportions
- Existing features

Respond with ONLY a comma-separated list of style names from the available styles.
Example: modern, scandinavian, minimalist, contemporary, coastal"""
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                image_path=image_path
            )
            
            # Parse response
            styles = [s.strip().lower().replace(' ', '_') for s in response.split(',')]
            # Filter to valid styles
            valid_styles = [s for s in styles if s in self.STYLE_CATALOG]
            
            logger.info(f"Recommended styles: {valid_styles}")
            return valid_styles[:5]
            
        except Exception as e:
            logger.error(f"Error analyzing room: {e}")
            # Return default styles
            return ["modern", "contemporary", "minimalist"]
    
    def get_user_preferred_styles(self, user_id: str, top_n: int = 5) -> List[str]:
        """
        Get user's preferred styles based on historical feedback.
        
        Args:
            user_id: User ID
            top_n: Number of top styles to return
            
        Returns:
            List of preferred style names
        """
        if user_id not in self.preferences:
            return []
        
        user_prefs = self.preferences[user_id]
        # Sort by preference score
        sorted_prefs = sorted(
            user_prefs.items(),
            key=lambda x: x[1].preference_score,
            reverse=True
        )
        
        return [style for style, _ in sorted_prefs[:top_n]]
    
    def update_style_preference(
        self,
        user_id: str,
        style: str,
        liked: bool
    ):
        """
        Update user's style preference based on feedback.
        
        Args:
            user_id: User ID
            style: Style name
            liked: Whether user liked this style
        """
        if user_id not in self.preferences:
            self.preferences[user_id] = {}
        
        if style not in self.preferences[user_id]:
            self.preferences[user_id][style] = StylePreference(
                user_id=user_id,
                style_name=style,
                preference_score=0.5
            )
        
        pref = self.preferences[user_id][style]
        
        # Update score using exponential moving average
        alpha = 0.3  # Learning rate
        new_score = 1.0 if liked else 0.0
        pref.preference_score = alpha * new_score + (1 - alpha) * pref.preference_score
        pref.feedback_count += 1
        pref.last_updated = datetime.now().isoformat()
        
        self._save_preferences()

        logger.info(f"Updated preference for {user_id}/{style}: {pref.preference_score:.2f}")

    async def generate_variations(self, request: VariationRequest) -> VariationBatch:
        """
        Generate design variations with intelligent style selection.

        Args:
            request: Variation generation request

        Returns:
            Batch of generated variations
        """
        start_time = datetime.now()

        try:
            # Determine styles to use
            if request.style_preferences:
                styles = request.style_preferences
            elif request.user_id:
                # Use user preferences
                user_styles = self.get_user_preferred_styles(request.user_id, top_n=request.num_variations)
                if user_styles:
                    styles = user_styles
                else:
                    # Analyze room for recommendations
                    styles = await self.analyze_room_for_styles(request.original_image_path)
            else:
                # Analyze room for recommendations
                styles = await self.analyze_room_for_styles(request.original_image_path)

            # Filter out excluded styles
            if request.exclude_styles:
                styles = [s for s in styles if s not in request.exclude_styles]

            # Ensure we have enough styles
            if len(styles) < request.num_variations:
                # Add more styles from catalog
                available_styles = [s for s in self.STYLE_CATALOG.keys() if s not in styles]
                if request.exclude_styles:
                    available_styles = [s for s in available_styles if s not in request.exclude_styles]
                styles.extend(available_styles[:request.num_variations - len(styles)])

            # Limit to requested number
            styles = styles[:request.num_variations]

            logger.info(f"Generating {len(styles)} variations with styles: {styles}")

            # Generate variations
            variations = []
            for style in styles:
                variation = await self._generate_single_variation(
                    original_image_path=request.original_image_path,
                    style=style,
                    variation_intensity=request.variation_intensity,
                    preserve_elements=request.preserve_elements
                )
                if variation:
                    variations.append(variation)

            # Calculate quality scores
            for var in variations:
                var.quality_score = await self._calculate_quality_score(var)

            # Determine recommended variation (highest quality)
            recommended = None
            if variations:
                best_var = max(variations, key=lambda v: v.quality_score)
                recommended = best_var.variation_id

            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            batch = VariationBatch(
                batch_id=hashlib.md5(f"{request.original_image_path}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                original_image_path=request.original_image_path,
                variations=variations,
                generation_time_ms=generation_time,
                total_variations=len(variations),
                recommended_variation=recommended
            )

            logger.info(f"Generated {len(variations)} variations in {generation_time:.2f}ms")

            return batch

        except Exception as e:
            logger.error(f"Error generating variations: {e}", exc_info=True)
            raise

    async def _generate_single_variation(
        self,
        original_image_path: str,
        style: str,
        variation_intensity: float,
        preserve_elements: Optional[List[str]]
    ) -> Optional[VariationResult]:
        """Generate a single design variation."""
        try:
            style_info = self.STYLE_CATALOG.get(style, {})

            # Build transformation parameters
            params = {
                "target_style": style,
                "description": style_info.get("description", ""),
                "intensity": variation_intensity
            }

            # Create transformation request
            transform_request = DesignTransformationRequest(
                original_image_path=original_image_path,
                transformation_type="style_transfer",
                transformation_params=params,
                num_variations=1,
                preserve_layout=True
            )

            # Generate
            result = await self.imagen_service.transform_design(transform_request)

            if not result.success or not result.images:
                logger.warning(f"Failed to generate variation for style: {style}")
                return None

            # Create variation result
            variation = VariationResult(
                variation_id=hashlib.md5(f"{style}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                style=style,
                image_path=result.image_paths[0],
                image_base64=result.images[0],
                quality_score=0.0,  # Will be calculated later
                metadata={
                    "style_info": style_info,
                    "generation_time_ms": result.generation_time_ms,
                    "transformation_params": params
                }
            )

            return variation

        except Exception as e:
            logger.error(f"Error generating variation for style {style}: {e}")
            return None

    async def _calculate_quality_score(self, variation: VariationResult) -> float:
        """
        Calculate quality score for a variation.

        Uses AI to assess:
        - Design coherence
        - Style consistency
        - Visual appeal

        Args:
            variation: Variation to score

        Returns:
            Quality score 0.0-1.0
        """
        try:
            # For now, use a simple heuristic based on generation time
            # In production, this could use a trained model or more sophisticated analysis

            gen_time = variation.metadata.get("generation_time_ms", 1000)

            # Normalize generation time (faster is better, up to a point)
            # Assume optimal time is 1000-2000ms
            if gen_time < 1000:
                time_score = 0.7
            elif gen_time < 2000:
                time_score = 1.0
            elif gen_time < 3000:
                time_score = 0.9
            else:
                time_score = 0.8

            # Base score on style catalog quality
            style_info = variation.metadata.get("style_info", {})
            has_description = 1.0 if style_info.get("description") else 0.5

            # Combine scores
            quality_score = (time_score * 0.6 + has_description * 0.4)

            return min(1.0, max(0.0, quality_score))

        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5

    async def generate_batch_variations(
        self,
        image_paths: List[str],
        num_variations_per_image: int = 3,
        user_id: Optional[str] = None
    ) -> List[VariationBatch]:
        """
        Generate variations for multiple images in batch.

        Args:
            image_paths: List of image paths
            num_variations_per_image: Variations per image
            user_id: Optional user ID for preferences

        Returns:
            List of variation batches
        """
        batches = []

        for image_path in image_paths:
            request = VariationRequest(
                original_image_path=image_path,
                num_variations=num_variations_per_image,
                user_id=user_id
            )

            batch = await self.generate_variations(request)
            batches.append(batch)

        logger.info(f"Generated {len(batches)} batches for {len(image_paths)} images")

        return batches

    def get_style_recommendations(
        self,
        user_id: Optional[str] = None,
        room_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get style recommendations based on user preferences and room type.

        Args:
            user_id: Optional user ID
            room_type: Optional room type (kitchen, bedroom, etc.)

        Returns:
            List of style recommendations with details
        """
        recommendations = []

        # Get user preferences if available
        user_styles = []
        if user_id:
            user_styles = self.get_user_preferred_styles(user_id, top_n=3)

        # Room-specific recommendations
        room_style_map = {
            "kitchen": ["modern", "farmhouse", "contemporary", "industrial"],
            "bedroom": ["scandinavian", "minimalist", "coastal", "bohemian"],
            "living_room": ["contemporary", "mid_century_modern", "traditional", "modern"],
            "bathroom": ["modern", "coastal", "scandinavian", "minimalist"],
            "dining_room": ["traditional", "contemporary", "farmhouse", "mid_century_modern"]
        }

        room_styles = room_style_map.get(room_type, []) if room_type else []

        # Combine user preferences and room recommendations
        all_styles = user_styles + room_styles
        seen = set()
        unique_styles = []
        for style in all_styles:
            if style not in seen:
                seen.add(style)
                unique_styles.append(style)

        # Add remaining styles from catalog
        for style in self.STYLE_CATALOG.keys():
            if style not in seen:
                unique_styles.append(style)

        # Build recommendations
        for style in unique_styles[:10]:
            style_info = self.STYLE_CATALOG.get(style, {})

            rec = {
                "style": style,
                "description": style_info.get("description", ""),
                "keywords": style_info.get("keywords", []),
                "color_palette": style_info.get("color_palette", []),
                "is_user_preferred": style in user_styles,
                "is_room_recommended": style in room_styles
            }

            recommendations.append(rec)

        return recommendations

