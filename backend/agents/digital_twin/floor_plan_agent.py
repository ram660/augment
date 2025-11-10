"""Floor Plan Analysis Agent - Extracts room layouts, dimensions, and spatial relationships from floor plans."""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.services.vision_service import UnifiedVisionService
from backend.utils.floor_type_normalizer import normalize_floor_type, floor_level_from_type
from backend.utils.room_type_normalizer import normalize_room_type

logger = logging.getLogger(__name__)


class FloorPlanAnalysisAgent(BaseAgent):
    """
    Agent specialized in analyzing floor plans to extract:
    - Room layouts and types
    - Dimensions and measurements
    - Spatial relationships
    - Doors, windows, and architectural features
    - Overall floor area and layout type
    """

    def __init__(self):
        config = AgentConfig(
            name="floor_plan_analysis_agent",
            role=AgentRole.HOME_PROFILE,
            description="Analyzes floor plans to extract room layouts, dimensions, and spatial data",
            model_name="gemini-2.5-flash",
            temperature=0.3,  # Lower temperature for more precise analysis
            enable_memory=False  # Floor plan analysis is stateless
        )
        super().__init__(config)
        self.vision = UnifiedVisionService()

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process a floor plan image and extract spatial data.

        Args:
            input_data: {
                "image": str,  # Path to floor plan image or base64 encoded
                "scale": Optional[str],  # Scale information if available (e.g., "1/4 inch = 1 foot")
                "floor_level": Optional[int],  # Which floor this represents
                "analysis_depth": Optional[str]  # 'basic', 'detailed', 'comprehensive'
            }

        Returns:
            AgentResponse with extracted floor plan data
        """
        try:
            image_path = input_data.get("image")
            if not image_path:
                return AgentResponse(
                    agent_name=self.config.name,
                    agent_role=self.config.role,
                    success=False,
                    error="No image provided for floor plan analysis"
                )

            scale = input_data.get("scale", "unknown")
            floor_level = input_data.get("floor_level", 1)
            analysis_depth = input_data.get("analysis_depth", "comprehensive")

            # Build the analysis prompt based on depth
            prompt = self._build_analysis_prompt(scale, floor_level, analysis_depth)

            # Analyze the floor plan using Gemini Vision
            logger.info(f"Analyzing floor plan: {image_path}")
            start_time = datetime.utcnow()

            analysis_result = await self.vision.analyze_floor_plan(
                image=image_path,
                prompt=prompt,
                temperature=0.3
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Parse the AI response
            parsed_data = self._parse_analysis_response(analysis_result, analysis_depth)

            # Add metadata
            parsed_data["metadata"] = {
                "scale": scale,
                "floor_level": floor_level,
                "analysis_depth": analysis_depth,
                "model_used": "gemini-2.5-flash",
                "processing_time_ms": processing_time,
                "analyzed_at": datetime.utcnow().isoformat()
            }

            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=True,
                data=parsed_data,
                message=f"Successfully analyzed floor plan with {len(parsed_data.get('detected_rooms', []))} rooms detected"
            )

        except Exception as e:
            logger.error(f"Error in floor plan analysis: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                agent_role=self.config.role,
                success=False,
                error=f"Floor plan analysis failed: {str(e)}"
            )

    def _build_analysis_prompt(self, scale: str, floor_level: int, analysis_depth: str) -> str:
        """Build the analysis prompt based on requirements without f-string interpolation in JSON blocks."""
        parts: List[str] = []
        parts.append("Analyze this floor plan image in detail.\n\n")
        parts.append(f"Scale information: {scale}\n")
        parts.append(f"Hinted floor level (from client): {floor_level}\n\n")
        parts.append(
            """
Return ONLY valid JSON. If the sheet contains multiple distinct floor sections, return the multi-floor form described below; otherwise use the single-floor form.

// Multi-floor form (preferred when multiple sections are present)
// floors[] items follow the same schema as the single-floor form, but nested per floor
{
    "multi_floor": true,
    "floors": [ { } ]
}

// Single-floor form

{
    "floor_level_number": <int>,
    "floor_level_name": "basement|main|second|third|attic|other",
    "section_bbox": { "x_min": <int>, "y_min": <int>, "x_max": <int>, "y_max": <int> },
    "pixel_to_unit": { "pixels_per_foot": <float|null>, "pixels_per_meter": <float|null>, "inferred_from": "scale_text|door|tub|stair|bed|unknown" },
    "units": {
        "system": "imperial|metric",
        "length_unit": "ft|in|m|mm",
        "area_unit": "sqft|sqm",
        "scale_text": "<raw scale text or null>"
    },
    "detected_rooms": [
        {
            "room_type": "kitchen|living_room|bedroom|bathroom|...",
            "name": "suggested name like 'Primary Bedroom'",
            "dimensions": {
                "length_ft": <float|null>,
                "width_ft": <float|null>,
                "area_sqft": <float|null>,
                "source": "ocr|scale|estimate"
            },
            "location": { "x": <int>, "y": <int> },
            "features": ["island","pantry","double_sink","walk_in_closet"],
            "confidence": <0.0-1.0>
        }
    ],
    "doors": [{"type": "entry|interior|sliding|french|pocket|other", "location": "<desc>", "connects": ["room1","room2"], "width_ft": <float|null>}],
    "windows": [{"type": "standard|bay|picture|casement|other", "location": "<desc>", "room": "<room>", "count": <int>}],
    "walls": [{"type": "exterior|interior|load_bearing", "length_ft": <float|null>, "location": "<desc>"}],
    "stairs": [{"type": "straight|L-shaped|U-shaped|spiral", "location": "<desc>", "connects_to": "<floor label or number>", "direction": "up|down|both"}],
    "layout_analysis": {
        "layout_type": "open_concept|traditional|split_level|other",
        "total_area_sqft": <float|null>,
        "room_count": <int>,
        "circulation_quality": "excellent|good|fair|poor",
        "notes": "<string>"
    },
    "spatial_relationships": {
        "room_adjacency": {"room1": ["adjacent_room1", "adjacent_room2"]},
        "circulation_paths": ["<desc>"],
        "zones": ["<desc>"]
    },
    "confidence_metrics": {
        "overall_confidence": <0.0-1.0>,
        "room_detection_confidence": <0.0-1.0>,
        "notes": "<string>"
    }
}

STRICT:
- If multiple distinct floor sections are present, return the multi-floor form with an entry per floor.
- Include floor_level_number and floor_level_name based on plan labels (e.g., "Basement", "Main Floor", "Second").
- If scale text is visible (title block/legend), populate units.scale_text.
- Prefer OCR for room dimensions when present; otherwise compute via scale; otherwise estimate.
- Return only JSON.
"""
        )

        if analysis_depth == "comprehensive":
            parts.append(
                """
Additionally provide:
- Detailed measurements for each room
- Precise door and window locations
- Wall thickness estimates
- Ceiling height if indicated
- Built-in features (closets, pantries, etc.)
- Electrical and plumbing fixture locations if visible
- Architectural features (columns, beams, etc.)
"""
            )

        parts.append(
            """
IMPORTANT:
1. Provide ONLY valid JSON in your response
2. Use realistic measurements based on typical residential standards
3. If scale is unknown, estimate based on standard room sizes
4. Mark low-confidence detections clearly
5. Include all visible rooms, even small ones like closets
6. Identify room types based on fixtures, layout, and typical placement
7. Note any unusual or custom features

Return ONLY the JSON object, no additional text.
"""
        )

        return "".join(parts)

    def _parse_analysis_response(self, ai_response: str, analysis_depth: str) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            # Try to extract JSON from the response
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
            # Normalize floor typing for single-floor or multi-floor shapes
            if isinstance(parsed, dict) and isinstance(parsed.get("floors"), list) and parsed.get("floors"):
                for fl in parsed["floors"]:
                    fname = fl.get("floor_level_name")
                    fnum = fl.get("floor_level_number")
                    # If number is present, make name consistent with the number
                    if fnum is not None:
                        if fnum == 0:
                            fl["floor_level_name"] = "basement"
                        elif fnum == 1:
                            fl["floor_level_name"] = "main"
                        elif fnum == 2:
                            fl["floor_level_name"] = "second"
                        elif fnum >= 3:
                            fl["floor_level_name"] = "third"
                        else:
                            fl["floor_level_name"] = "other"
                    elif fname:
                        canon = normalize_floor_type(fname)
                        fl["floor_level_name"] = canon
                        fl["floor_level_number"] = floor_level_from_type(canon)
            else:
                floor_name = parsed.get("floor_level_name")
                floor_num = parsed.get("floor_level_number")
                if floor_num is not None:
                    if floor_num == 0:
                        parsed["floor_level_name"] = "basement"
                    elif floor_num == 1:
                        parsed["floor_level_name"] = "main"
                    elif floor_num == 2:
                        parsed["floor_level_name"] = "second"
                    elif floor_num >= 3:
                        parsed["floor_level_name"] = "third"
                    else:
                        parsed["floor_level_name"] = "other"
                elif floor_name:
                    canon = normalize_floor_type(floor_name)
                    parsed["floor_level_name"] = canon
                    parsed["floor_level_number"] = floor_level_from_type(canon)
            
            # Normalize per-floor room types if multi-floor (support both 'rooms' and 'detected_rooms')
            if isinstance(parsed, dict) and isinstance(parsed.get("floors"), list) and parsed.get("floors"):
                for fl in parsed["floors"]:
                    for key in ("rooms", "detected_rooms"):
                        room_list = fl.get(key) or []
                        if isinstance(room_list, list):
                            for room in room_list:
                                if "room_type" in room:
                                    original_type = room["room_type"]
                                    normalized_type = normalize_room_type(original_type)
                                    room["room_type"] = normalized_type
                    # Optionally mirror detected_rooms into rooms for downstream simplicity
                    if not fl.get("rooms") and fl.get("detected_rooms"):
                        fl["rooms"] = fl.get("detected_rooms")

            # Normalize room types in detected rooms
            detected_rooms = parsed.get("detected_rooms", [])
            for room in detected_rooms:
                if "room_type" in room:
                    original_type = room["room_type"]
                    normalized_type = normalize_room_type(original_type)
                    room["room_type"] = normalized_type
                    if original_type != normalized_type:
                        logger.info(f"Normalized room type: '{original_type}' -> '{normalized_type}'")

            # Validate and normalize the structure
            # Build a compact scale_info payload combining units/pixel_to_unit/section_bbox
            scale_info = {
                "units": parsed.get("units", {}),
                "pixel_to_unit": parsed.get("pixel_to_unit"),
                "section_bbox": parsed.get("section_bbox"),
            }
            if isinstance(parsed, dict) and isinstance(parsed.get("floors"), list) and parsed["floors"]:
                # Multi-floor result: return as-is plus a light summary
                result = {
                    "multi_floor": True,
                    "floors": parsed["floors"],
                    "raw_response": parsed,
                }
            else:
                # Single-floor: build a normalized result like before
                scale_info = {
                    "units": parsed.get("units", {}),
                    "pixel_to_unit": parsed.get("pixel_to_unit"),
                    "section_bbox": parsed.get("section_bbox"),
                }
                result = {
                    "multi_floor": False,
                    "detected_rooms": detected_rooms,
                    "room_count": len(detected_rooms),
                    "doors": parsed.get("doors", []),
                    "windows": parsed.get("windows", []),
                    "walls": parsed.get("walls", []),
                    "stairs": parsed.get("stairs", []),
                    "layout_type": parsed.get("layout_analysis", {}).get("layout_type", "unknown"),
                    "total_area": parsed.get("layout_analysis", {}).get("total_area_sqft", 0),
                    "dimensions": {"total_area_sqft": parsed.get("layout_analysis", {}).get("total_area_sqft", 0)},
                    "room_adjacency": parsed.get("spatial_relationships", {}).get("room_adjacency", {}),
                    "circulation_paths": parsed.get("spatial_relationships", {}).get("circulation_paths", []),
                    "confidence_score": parsed.get("confidence_metrics", {}).get("overall_confidence", 0.0),
                    "completeness_score": self._calculate_completeness(parsed),
                    "floor_level_number": parsed.get("floor_level_number"),
                    "floor_level_name": parsed.get("floor_level_name"),
                    "units": parsed.get("units", {}),
                    "section_bbox": parsed.get("section_bbox"),
                    "pixel_to_unit": parsed.get("pixel_to_unit"),
                    "scale_info": scale_info,
                    "raw_response": parsed,
                }
            
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response was: {ai_response[:500]}")
            
            # Return a minimal structure with the raw response
            return {
                "detected_rooms": [],
                "room_count": 0,
                "doors": [],
                "windows": [],
                "walls": [],
                "stairs": [],
                "layout_type": "unknown",
                "total_area": 0,
                "dimensions": {},
                "room_adjacency": {},
                "circulation_paths": [],
                "confidence_score": 0.0,
                "completeness_score": 0.0,
                "raw_response": {"error": "Failed to parse JSON", "raw_text": ai_response},
                "parse_error": str(e)
            }

    def _calculate_completeness(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate how complete the analysis is."""
        score = 0.0
        max_score = 7.0
        
        # Check for presence of key data
        if parsed_data.get("detected_rooms"):
            score += 2.0  # Most important
        if parsed_data.get("doors"):
            score += 1.0
        if parsed_data.get("windows"):
            score += 1.0
        if parsed_data.get("layout_analysis"):
            score += 1.0
        if parsed_data.get("spatial_relationships"):
            score += 1.0
        if parsed_data.get("confidence_metrics"):
            score += 1.0
        
        return round(score / max_score, 2)

