"""Product Matching Agent - Dimension-aware product matching and recommendations."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json

from backend.agents.base.agent import BaseAgent, AgentConfig, AgentResponse, AgentRole
from backend.integrations.gemini.client import GeminiClient

logger = logging.getLogger(__name__)


# Product dimension database (typical dimensions in inches)
PRODUCT_DIMENSIONS = {
    # Furniture
    "sofa": {"width": (72, 96), "depth": (32, 40), "height": (30, 36)},
    "loveseat": {"width": (52, 64), "depth": (32, 38), "height": (30, 36)},
    "armchair": {"width": (30, 40), "depth": (32, 38), "height": (30, 36)},
    "coffee_table": {"width": (36, 54), "depth": (18, 30), "height": (16, 20)},
    "dining_table_4": {"width": (36, 48), "depth": (36, 48), "height": (28, 30)},
    "dining_table_6": {"width": (60, 72), "depth": (36, 42), "height": (28, 30)},
    "dining_table_8": {"width": (84, 96), "depth": (36, 42), "height": (28, 30)},
    "queen_bed": {"width": 60, "depth": 80, "height": (50, 60)},
    "king_bed": {"width": 76, "depth": 80, "height": (50, 60)},
    "dresser": {"width": (48, 72), "depth": (18, 24), "height": (30, 40)},
    "nightstand": {"width": (18, 30), "depth": (16, 20), "height": (24, 30)},
    "desk": {"width": (48, 72), "depth": (24, 30), "height": (28, 30)},
    "bookshelf": {"width": (24, 48), "depth": (12, 16), "height": (60, 84)},
    
    # Appliances
    "refrigerator": {"width": (30, 36), "depth": (30, 36), "height": (66, 72)},
    "range": {"width": (30, 36), "depth": (24, 30), "height": (36, 48)},
    "dishwasher": {"width": (24, 24), "depth": (24, 24), "height": (34, 35)},
    "microwave": {"width": (24, 30), "depth": (15, 20), "height": (12, 18)},
    "washer": {"width": (27, 29), "depth": (30, 34), "height": (38, 43)},
    "dryer": {"width": (27, 29), "depth": (30, 34), "height": (38, 43)},
    
    # Fixtures
    "vanity_single": {"width": (24, 36), "depth": (18, 22), "height": (30, 36)},
    "vanity_double": {"width": (60, 72), "depth": (18, 22), "height": (30, 36)},
    "bathtub": {"width": (30, 32), "depth": (60, 72), "height": (14, 20)},
    "shower_stall": {"width": (32, 48), "depth": (32, 48), "height": (72, 84)},
}


# Clearance requirements (in inches)
CLEARANCE_REQUIREMENTS = {
    "walkway": 36,  # Minimum walkway width
    "doorway": 32,  # Minimum doorway clearance
    "furniture_front": 18,  # Space in front of furniture
    "appliance_front": 48,  # Space in front of appliances
    "bed_side": 24,  # Space on sides of bed
    "dining_chair": 36,  # Space for dining chair pullout
}


class ProductMatchingAgent(BaseAgent):
    """
    Production-ready agent for matching products to rooms with dimension validation.
    
    Features:
    - Dimension-aware product matching
    - Fit validation (will it physically fit?)
    - Clearance validation (enough space to use?)
    - Style compatibility analysis
    - Alternative recommendations
    - Confidence scoring
    """
    
    def __init__(self):
        config = AgentConfig(
            name="product_matching_agent",
            role=AgentRole.PRODUCT_DISCOVERY,
            description="Matches products to rooms with dimension validation and style compatibility",
            model_name="gemini-2.5-flash",
            temperature=0.3,
            enable_memory=False
        )
        super().__init__(config)
        self.gemini_client = GeminiClient()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Match products to a room with dimension and style validation.
        
        Args:
            input_data: {
                "product_type": str,  # Type of product to match
                "room_type": str,  # Type of room
                "room_dimensions": Dict,  # {"length_ft": float, "width_ft": float, "height_ft": float}
                "existing_products": Optional[List[Dict]],  # Existing products in room
                "style_preference": Optional[str],  # Desired style
                "budget_range": Optional[Dict],  # {"min": float, "max": float}
                "must_have_features": Optional[List[str]],  # Required features
                "room_image_url": Optional[str]  # Optional room image
            }
        
        Returns:
            AgentResponse with product matching data
        """
        try:
            product_type = input_data.get("product_type")
            room_type = input_data.get("room_type")
            room_dimensions = input_data.get("room_dimensions", {})
            
            if not product_type:
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role,
                    success=False,
                    error="product_type is required"
                )
            
            if not room_dimensions:
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role,
                    success=False,
                    error="room_dimensions are required for dimension validation"
                )
            
            existing_products = input_data.get("existing_products", [])
            style_preference = input_data.get("style_preference")
            budget_range = input_data.get("budget_range", {})
            must_have_features = input_data.get("must_have_features", [])
            room_image_url = input_data.get("room_image_url")
            
            logger.info(f"Matching {product_type} for {room_type} room")
            start_time = datetime.utcnow()
            
            # Step 1: Get product dimensions
            product_dims = self._get_product_dimensions(product_type)
            
            # Step 2: Validate fit
            fit_validation = self._validate_fit(
                product_type,
                product_dims,
                room_dimensions,
                existing_products
            )
            
            # Step 3: Analyze style compatibility
            style_analysis = await self._analyze_style_compatibility(
                product_type,
                room_type,
                style_preference,
                room_image_url
            )
            
            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(
                product_type,
                product_dims,
                fit_validation,
                style_analysis,
                budget_range,
                must_have_features
            )
            
            # Step 5: Calculate confidence score
            confidence_score = self._calculate_confidence(
                fit_validation,
                style_analysis,
                room_dimensions
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = {
                "product_type": product_type,
                "product_dimensions": product_dims,
                "fit_validation": fit_validation,
                "style_compatibility": style_analysis,
                "recommendations": recommendations,
                "confidence_score": confidence_score,
                "metadata": {
                    "room_type": room_type,
                    "room_dimensions": room_dimensions,
                    "processing_time_ms": processing_time,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
            
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=True,
                data=result,
                message=f"Product matching complete: {len(recommendations)} recommendations"
            )
        
        except Exception as e:
            logger.error(f"Error in product matching: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=False,
                error=f"Product matching failed: {str(e)}"
            )
    
    def _get_product_dimensions(self, product_type: str) -> Dict[str, Any]:
        """Get typical dimensions for a product type."""
        
        product_key = product_type.lower().replace(" ", "_")
        
        # Check exact match
        if product_key in PRODUCT_DIMENSIONS:
            dims = PRODUCT_DIMENSIONS[product_key]
            return self._normalize_dimensions(dims)
        
        # Check partial match
        for key, dims in PRODUCT_DIMENSIONS.items():
            if product_key in key or key in product_key:
                return self._normalize_dimensions(dims)
        
        # Return default dimensions
        logger.warning(f"No dimensions found for {product_type}, using defaults")
        return {
            "width_in": {"min": 24, "max": 48},
            "depth_in": {"min": 24, "max": 36},
            "height_in": {"min": 30, "max": 40}
        }
    
    def _normalize_dimensions(self, dims: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize dimension format."""
        result = {}
        
        for key, value in dims.items():
            if isinstance(value, tuple):
                result[f"{key}_in"] = {"min": value[0], "max": value[1]}
            else:
                result[f"{key}_in"] = {"min": value, "max": value}
        
        return result
    
    def _validate_fit(
        self,
        product_type: str,
        product_dims: Dict[str, Any],
        room_dimensions: Dict[str, float],
        existing_products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate if product will fit in the room."""
        
        # Convert room dimensions to inches
        room_length_in = room_dimensions.get("length_ft", 0) * 12
        room_width_in = room_dimensions.get("width_ft", 0) * 12
        room_height_in = room_dimensions.get("height_ft", 8) * 12
        
        # Get product dimensions
        product_width = product_dims.get("width_in", {})
        product_depth = product_dims.get("depth_in", {})
        product_height = product_dims.get("height_in", {})
        
        # Calculate available space
        occupied_space = self._calculate_occupied_space(existing_products)
        available_floor_space = (room_length_in * room_width_in) - occupied_space
        
        # Validate dimensions
        fits_width = product_width.get("max", 0) <= room_width_in
        fits_depth = product_depth.get("max", 0) <= room_length_in
        fits_height = product_height.get("max", 0) <= room_height_in
        
        # Calculate required clearance
        required_clearance = self._calculate_required_clearance(product_type)
        product_footprint = (
            product_width.get("max", 0) * product_depth.get("max", 0)
        ) + required_clearance
        
        fits_with_clearance = product_footprint <= available_floor_space
        
        # Overall fit assessment
        will_fit = fits_width and fits_depth and fits_height and fits_with_clearance
        
        return {
            "will_fit": will_fit,
            "fits_width": fits_width,
            "fits_depth": fits_depth,
            "fits_height": fits_height,
            "fits_with_clearance": fits_with_clearance,
            "available_floor_space_sqin": round(available_floor_space, 2),
            "required_space_sqin": round(product_footprint, 2),
            "clearance_required_in": required_clearance,
            "warnings": self._generate_fit_warnings(
                fits_width, fits_depth, fits_height, fits_with_clearance
            )
        }

    def _calculate_occupied_space(self, existing_products: List[Dict[str, Any]]) -> float:
        """Calculate total occupied floor space."""
        total = 0.0

        for product in existing_products:
            dims = product.get("dimensions", {})
            width = dims.get("width_in", 0)
            depth = dims.get("depth_in", 0)
            total += width * depth

        return total

    def _calculate_required_clearance(self, product_type: str) -> float:
        """Calculate required clearance space for product."""

        product_lower = product_type.lower()

        if "bed" in product_lower:
            # Beds need clearance on sides
            return CLEARANCE_REQUIREMENTS["bed_side"] * 2 * 80  # Both sides
        elif "dining" in product_lower or "table" in product_lower:
            # Dining tables need chair pullout space
            return CLEARANCE_REQUIREMENTS["dining_chair"] * 4  # All sides
        elif any(x in product_lower for x in ["refrigerator", "range", "dishwasher"]):
            # Appliances need front clearance
            return CLEARANCE_REQUIREMENTS["appliance_front"] * 30  # Front space
        else:
            # Default furniture clearance
            return CLEARANCE_REQUIREMENTS["furniture_front"] * 30

    def _generate_fit_warnings(
        self,
        fits_width: bool,
        fits_depth: bool,
        fits_height: bool,
        fits_with_clearance: bool
    ) -> List[str]:
        """Generate warnings for fit issues."""
        warnings = []

        if not fits_width:
            warnings.append("Product width exceeds room width")
        if not fits_depth:
            warnings.append("Product depth exceeds room length")
        if not fits_height:
            warnings.append("Product height exceeds room height")
        if not fits_with_clearance:
            warnings.append("Insufficient clearance space for comfortable use")

        return warnings

    async def _analyze_style_compatibility(
        self,
        product_type: str,
        room_type: str,
        style_preference: Optional[str],
        room_image_url: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze style compatibility using AI."""

        prompt = f"""Analyze style compatibility for this product and room.

Product Type: {product_type}
Room Type: {room_type}
Style Preference: {style_preference or 'Not specified'}

Provide a JSON response with:
{{
    "style_match_score": <0.0-1.0>,
    "recommended_styles": ["style1", "style2", "style3"],
    "color_recommendations": ["color1", "color2"],
    "material_recommendations": ["material1", "material2"],
    "design_notes": "Brief notes on style compatibility"
}}

Return only valid JSON."""

        try:
            if room_image_url:
                analysis_result = await self.gemini_client.analyze_image(
                    image=room_image_url,
                    prompt=prompt,
                    temperature=0.3
                )
            else:
                analysis_result = await self.gemini_client.generate_text(
                    prompt=prompt,
                    temperature=0.3
                )

            parsed = self._parse_json_response(analysis_result)
            return parsed

        except Exception as e:
            logger.error(f"Error analyzing style compatibility: {e}")
            return {
                "style_match_score": 0.7,
                "recommended_styles": ["modern", "transitional"],
                "color_recommendations": ["neutral", "white"],
                "material_recommendations": ["wood", "metal"],
                "design_notes": "Style analysis unavailable"
            }

    def _generate_recommendations(
        self,
        product_type: str,
        product_dims: Dict[str, Any],
        fit_validation: Dict[str, Any],
        style_analysis: Dict[str, Any],
        budget_range: Dict[str, float],
        must_have_features: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate product recommendations."""

        recommendations = []

        # If product doesn't fit, recommend smaller alternatives
        if not fit_validation.get("will_fit"):
            recommendations.append({
                "recommendation_type": "size_alternative",
                "title": f"Smaller {product_type}",
                "reason": "Original size doesn't fit - consider compact version",
                "suggested_dimensions": self._suggest_smaller_dimensions(product_dims),
                "priority": "high"
            })

        # Style recommendations
        for style in style_analysis.get("recommended_styles", [])[:3]:
            recommendations.append({
                "recommendation_type": "style_match",
                "title": f"{style.title()} {product_type}",
                "reason": f"Matches {style} aesthetic",
                "style": style,
                "priority": "medium"
            })

        # Budget-conscious recommendations
        if budget_range:
            recommendations.append({
                "recommendation_type": "budget_option",
                "title": f"Budget-Friendly {product_type}",
                "reason": f"Within ${budget_range.get('min', 0)}-${budget_range.get('max', 0)} range",
                "budget_tier": "low" if budget_range.get("max", 0) < 500 else "mid",
                "priority": "medium"
            })

        # Feature-based recommendations
        if must_have_features:
            recommendations.append({
                "recommendation_type": "feature_match",
                "title": f"{product_type} with Required Features",
                "reason": f"Includes: {', '.join(must_have_features[:3])}",
                "features": must_have_features,
                "priority": "high"
            })

        return recommendations

    def _suggest_smaller_dimensions(self, original_dims: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest smaller dimensions (80% of original)."""
        smaller = {}

        for key, value in original_dims.items():
            if isinstance(value, dict):
                smaller[key] = {
                    "min": round(value.get("min", 0) * 0.8, 1),
                    "max": round(value.get("max", 0) * 0.8, 1)
                }
            else:
                smaller[key] = round(value * 0.8, 1)

        return smaller

    def _calculate_confidence(
        self,
        fit_validation: Dict[str, Any],
        style_analysis: Dict[str, Any],
        room_dimensions: Dict[str, float]
    ) -> float:
        """Calculate confidence score for recommendations."""

        confidence = 0.5  # Base confidence

        # Increase confidence if product fits
        if fit_validation.get("will_fit"):
            confidence += 0.3

        # Increase confidence if we have room dimensions
        if room_dimensions and all(k in room_dimensions for k in ["length_ft", "width_ft"]):
            confidence += 0.1

        # Increase confidence based on style match
        style_score = style_analysis.get("style_match_score", 0.5)
        confidence += style_score * 0.1

        return min(max(confidence, 0.0), 1.0)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}

