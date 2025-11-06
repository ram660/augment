"""Room Analysis Agent - Analyzes room photos for materials, fixtures, products, and conditions."""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.integrations.gemini import GeminiClient
from backend.utils.room_type_normalizer import normalize_room_type
from backend.utils.enum_normalizer import normalize_material_category, normalize_fixture_type

logger = logging.getLogger(__name__)


class RoomAnalysisAgent(BaseAgent):
    """
    Agent specialized in analyzing room photographs to extract:
    - Materials (flooring, walls, countertops, etc.)
    - Fixtures (lights, faucets, hardware)
    - Products and furniture
    - Room condition and quality
    - Style and design elements
    - Dimensions and spatial data
    """

    def __init__(self):
        config = AgentConfig(
            name="room_analysis_agent",
            role=AgentRole.HOME_PROFILE,
            description="Analyzes room photos to extract materials, fixtures, products, and condition data",
            model_name="gemini-2.5-flash",
            temperature=0.3,
            enable_memory=False
        )
        super().__init__(config)
        self.gemini_client = GeminiClient()

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process a room image and extract detailed information.

        Args:
            input_data: {
                "image": str,  # Path to room image or base64 encoded
                "room_type": Optional[str],  # Known room type if available
                "analysis_type": Optional[str],  # 'materials', 'products', 'condition', 'comprehensive'
                "focus_areas": Optional[List[str]]  # Specific areas to focus on
            }

        Returns:
            AgentResponse with extracted room data
        """
        try:
            image_path = input_data.get("image")
            if not image_path:
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role,
                    success=False,
                    error="No image provided for room analysis"
                )

            room_type = input_data.get("room_type", "unknown")
            analysis_type = input_data.get("analysis_type", "comprehensive")
            focus_areas = input_data.get("focus_areas", [])

            # Build the analysis prompt
            prompt = self._build_analysis_prompt(room_type, analysis_type, focus_areas)

            # Analyze the room using Gemini Vision
            logger.info(f"Analyzing room image: {image_path} (type: {analysis_type})")
            start_time = datetime.utcnow()

            analysis_result = await self.gemini_client.analyze_image(
                image=image_path,
                prompt=prompt,
                temperature=0.3
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Parse the AI response
            parsed_data = self._parse_analysis_response(analysis_result, analysis_type)

            # Add metadata
            parsed_data["metadata"] = {
                "room_type": room_type,
                "analysis_type": analysis_type,
                "focus_areas": focus_areas,
                "model_used": "gemini-2.5-flash",
                "processing_time_ms": processing_time,
                "analyzed_at": datetime.utcnow().isoformat()
            }

            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=True,
                data=parsed_data,
                message=f"Successfully analyzed room image ({analysis_type} analysis)"
            )

        except Exception as e:
            logger.error(f"Error in room analysis: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=False,
                error=f"Room analysis failed: {str(e)}"
            )

    def _build_analysis_prompt(self, room_type: str, analysis_type: str, focus_areas: List[str]) -> str:
        """Build the analysis prompt based on requirements."""
        
        base_prompt = f"""Analyze this room photograph in comprehensive detail.
Room type: {room_type if room_type != "unknown" else "identify from image"}

Provide a detailed JSON analysis with the following structure:

{{
    "room_identification": {{
        "room_type": "kitchen|bathroom|bedroom|living_room|etc",
        "room_style": "modern|traditional|farmhouse|industrial|etc",
        "confidence": 0.0 to 1.0
    }},
    "dimensions": {{
        "estimated_length_ft": estimated length,
        "estimated_width_ft": estimated width,
        "estimated_height_ft": ceiling height,
        "estimated_area_sqft": calculated area,
        "confidence": "high|medium|low"
    }},
    "materials": [
        {{
            "category": "flooring|wall|ceiling|countertop|cabinet|etc",
            "material_type": "hardwood|tile|granite|quartz|etc",
            "color": "primary color",
            "finish": "matte|glossy|satin|etc",
            "condition": "excellent|good|fair|poor",
            "coverage_area": "percentage or description",
            "brand_detected": "if visible",
            "confidence": 0.0 to 1.0
        }}
    ],
    "fixtures": [
        {{
            "fixture_type": "light|faucet|sink|toilet|etc",
            "style": "modern|traditional|etc",
            "finish": "chrome|brushed_nickel|etc",
            "location": "ceiling|wall|countertop|etc",
            "condition": "excellent|good|fair|poor",
            "brand_detected": "if visible",
            "model_detected": "if visible",
            "confidence": 0.0 to 1.0
        }}
    ],
    "products": [
        {{
            "product_category": "furniture|appliance|decor|etc",
            "product_type": "sofa|refrigerator|lamp|etc",
            "style": "modern|traditional|etc",
            "color": "primary color",
            "material": "wood|metal|fabric|etc",
            "brand_detected": "if visible",
            "estimated_dimensions": {{"length": 0, "width": 0, "height": 0}},
            "condition": "excellent|good|fair|poor",
            "confidence": 0.0 to 1.0
        }}
    ],
    "visual_characteristics": {{
        "dominant_colors": ["color1", "color2", "color3"],
        "color_palette": {{"primary": "hex", "secondary": "hex", "accent": "hex"}},
        "lighting_type": "natural|artificial|mixed",
        "lighting_quality": "bright|dim|balanced",
        "natural_light_sources": number of windows visible
    }},
    "condition_assessment": {{
        "overall_condition": "excellent|good|fair|poor",
        "defects_detected": [
            {{
                "type": "crack|stain|damage|wear|etc",
                "location": "description",
                "severity": "minor|moderate|severe"
            }}
        ],
        "maintenance_issues": ["list of issues requiring attention"],
        "renovation_priority": "high|medium|low",
        "estimated_age_years": estimated age of room/finishes
    }},
    "improvement_suggestions": [
        {{
            "category": "cosmetic|functional|structural",
            "suggestion": "description of improvement",
            "priority": "high|medium|low",
            "estimated_cost_range": "low|medium|high"
        }}
    ],
    "spatial_features": {{
        "doors": [{{"type": "entry|closet|etc", "count": 1}}],
        "windows": [{{"type": "standard|bay|etc", "count": 1}}],
        "built_ins": ["closets|shelving|etc"],
        "ceiling_type": "flat|vaulted|tray|etc",
        "architectural_features": ["crown_molding|wainscoting|etc"]
    }},
    "confidence_metrics": {{
        "overall_confidence": 0.0 to 1.0,
        "material_detection_confidence": 0.0 to 1.0,
        "product_detection_confidence": 0.0 to 1.0,
        "condition_assessment_confidence": 0.0 to 1.0,
        "notes": "any limitations or uncertainties"
    }}
}}

"""

        # Add specific instructions based on analysis type
        if analysis_type == "materials":
            base_prompt += "\nFOCUS PRIMARILY on materials - provide extremely detailed material analysis.\n"
        elif analysis_type == "products":
            base_prompt += "\nFOCUS PRIMARILY on products and furniture - identify brands and models where possible.\n"
        elif analysis_type == "condition":
            base_prompt += "\nFOCUS PRIMARILY on condition assessment - look for defects, wear, and maintenance issues.\n"

        if focus_areas:
            base_prompt += f"\nPay special attention to: {', '.join(focus_areas)}\n"

        base_prompt += """
IMPORTANT:
1. Provide ONLY valid JSON in your response
2. Be specific and detailed in descriptions
3. Estimate dimensions based on visible reference objects
4. Identify brands and models when visible
5. Note any defects or maintenance issues
6. Provide realistic condition assessments
7. Include confidence scores for all detections

Return ONLY the JSON object, no additional text."""

        return base_prompt

    def _parse_analysis_response(self, ai_response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            # Clean up the response
            response_text = ai_response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            parsed = json.loads(response_text)

            # Normalize room type
            raw_room_type = parsed.get("room_identification", {}).get("room_type", "unknown")
            normalized_room_type = normalize_room_type(raw_room_type)
            if raw_room_type != normalized_room_type:
                logger.info(f"Normalized room type: '{raw_room_type}' -> '{normalized_room_type}'")

            # Normalize materials
            materials = parsed.get("materials", [])
            for material in materials:
                if "category" in material:
                    original_cat = material["category"]
                    material["category"] = normalize_material_category(original_cat)

            # Normalize fixtures
            fixtures = parsed.get("fixtures", [])
            for fixture in fixtures:
                if "type" in fixture:
                    original_type = fixture["type"]
                    fixture["type"] = normalize_fixture_type(original_type)

            # Normalize the structure
            result = {
                "room_type": normalized_room_type,
                "room_style": parsed.get("room_identification", {}).get("room_style", "unknown"),
                "dimensions": parsed.get("dimensions", {}),
                "detected_materials": materials,
                "detected_fixtures": fixtures,
                "detected_products": parsed.get("products", []),
                "visual_characteristics": parsed.get("visual_characteristics", {}),
                "condition_assessment": parsed.get("condition_assessment", {}),
                "improvement_suggestions": parsed.get("improvement_suggestions", []),
                "spatial_features": parsed.get("spatial_features", {}),
                "confidence_score": parsed.get("confidence_metrics", {}).get("overall_confidence", 0.0),
                "completeness_score": self._calculate_completeness(parsed),
                "raw_response": parsed
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response was: {ai_response[:500]}")
            
            return {
                "room_type": "unknown",
                "room_style": "unknown",
                "dimensions": {},
                "detected_materials": [],
                "detected_fixtures": [],
                "detected_products": [],
                "visual_characteristics": {},
                "condition_assessment": {},
                "improvement_suggestions": [],
                "spatial_features": {},
                "confidence_score": 0.0,
                "completeness_score": 0.0,
                "raw_response": {"error": "Failed to parse JSON", "raw_text": ai_response},
                "parse_error": str(e)
            }

    def _calculate_completeness(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate how complete the analysis is."""
        score = 0.0
        max_score = 8.0
        
        if parsed_data.get("room_identification"):
            score += 1.0
        if parsed_data.get("dimensions"):
            score += 1.0
        if parsed_data.get("materials"):
            score += 1.5
        if parsed_data.get("fixtures"):
            score += 1.0
        if parsed_data.get("products"):
            score += 1.0
        if parsed_data.get("visual_characteristics"):
            score += 1.0
        if parsed_data.get("condition_assessment"):
            score += 1.0
        if parsed_data.get("spatial_features"):
            score += 0.5
        
        return round(score / max_score, 2)

