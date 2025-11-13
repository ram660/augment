"""
Gemini API client wrapper for HomeView AI.

This module provides a unified interface to Google's Gemini models:
- Text generation (Gemini 2.5 Flash/Pro)
- Vision analysis (image understanding)
- Image generation and editing (Gemini 2.5 Flash Image)
- Embeddings (text-embedding-004)

Official Documentation (always use these for integrations):
- Core Gemini API: https://ai.google.dev/gemini-api/docs
- Thinking / Reasoning: https://ai.google.dev/gemini-api/docs/thinking
- Structured output (JSON): https://ai.google.dev/gemini-api/docs/structured-output
- Function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Long context: https://ai.google.dev/gemini-api/docs/long-context
- Google Search grounding: https://ai.google.dev/gemini-api/docs/google-search
- Maps grounding: https://ai.google.dev/gemini-api/docs/maps-grounding
- URL context: https://ai.google.dev/gemini-api/docs/url-context
- File search: https://ai.google.dev/gemini-api/docs/file-search
- Imagen (text-to-image): https://ai.google.dev/gemini-api/docs/imagen
- Image generation/editing (Gemini native): https://ai.google.dev/gemini-api/docs/image-generation
- Image understanding: https://ai.google.dev/gemini-api/docs/image-understanding
"""

import os
import logging
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from io import BytesIO

from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

from backend.services.cost_tracking_service import get_cost_tracking_service
from backend.services.event_bus import get_event_bus
from backend.services.grounding_cache import GroundingCache
from backend.services.grounding_monitor import GroundingMonitor, GroundingMetrics
from backend.services.query_optimizer import QueryOptimizer
from backend.utils.circuit_breaker import circuit_breaker, retry_async
from backend.types.tool_responses import ToolResponse, GroundingQuery

logger = logging.getLogger(__name__)
# Brand preferences and per-category constraints to guide PDP selection
CATEGORY_BRAND_PREFERENCES: Dict[str, List[str]] = {
    "paint": ["Behr", "Sherwin-Williams", "Benjamin Moore", "Valspar"],
    "flooring": ["LifeProof", "Pergo", "TrafficMaster", "Armstrong"],
    "lighting": ["Philips Hue", "GE", "Lutron", "Kichler"],
    "decor": ["Wayfair", "Target", "West Elm", "IKEA"],
    "cabinets": ["IKEA", "KraftMaid", "Thomasville", "Hampton Bay"],
    "countertops": ["Silestone", "Caesarstone", "Cambria"],
    "backsplash": ["Daltile", "MSI", "Merola Tile"],
    "furniture": ["IKEA", "Wayfair", "Ashley Furniture", "West Elm"],
}

CATEGORY_CONSTRAINT_HINTS: Dict[str, str] = {
    # Hints are enforced via prompt since JSON mode is incompatible with google_search tool per docs
    "paint": "Include brand, finish (matte/eggshell/satin/semi-gloss), color name or code, and SKU/model if available.",
    "flooring": "Include material type (vinyl/laminate/hardwood/tile), coverage per box, thickness if available, and SKU.",
    "lighting": "Include fixture type, finish, compatible bulb type, and SKU/model.",
    "decor": "Prefer items that match the described styles/colors; include size and material.",
    "cabinets": "Include door style (e.g., shaker), finish, and SKU if a ready-to-assemble option.",
    "countertops": "Include material (quartz/granite/marble), thickness, edge style if available, and SKU.",
    "backsplash": "Include tile size, material, pattern name, and SKU if available.",
    "furniture": "Include dimensions, material/finish, and SKU/model.",
}



class GeminiConfig(BaseModel):
    """Configuration for Gemini client."""
    api_key: str
    default_text_model: str = "gemini-2.5-flash"
    default_vision_model: str = "gemini-2.5-flash"
    # Use the native Gemini image model for generation + editing per official docs
    # https://ai.google.dev/gemini-api/docs/image-generation
    default_image_gen_model: str = "gemini-2.5-flash-image"
    default_embedding_model: str = "models/text-embedding-004"
    default_temperature: float = 0.7
    default_max_tokens: Optional[int] = None
    timeout_seconds: int = 60
    enable_safety_settings: bool = True


class GeminiClient:
    """
    Unified client for all Gemini API interactions.

    Provides methods for:
    - Text generation and chat
    - Image analysis and understanding
    - Image generation and editing
    - Text embeddings for semantic search
    """

    def __init__(self, config: Optional[GeminiConfig] = None):
        """
        Initialize Gemini client.

        Args:
            config: Gemini configuration. If None, uses environment variables.
        """
        if config is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set")
            config = GeminiConfig(api_key=api_key)

        self.config = config

        # Configure the API
        genai.configure(api_key=config.api_key)

        # Initialize models
        self._init_models()

        # Initialize services
        self.cost_service = get_cost_tracking_service()
        self.event_bus = get_event_bus()
        self.grounding_cache = GroundingCache()
        self.grounding_monitor = GroundingMonitor()
        self.query_optimizer = QueryOptimizer()

        logger.info("Gemini client initialized successfully")

    def _init_models(self):
        """Initialize Gemini models."""
        # Safety settings
        self.safety_settings = None
        if self.config.enable_safety_settings:
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }

        # Text model
        self.text_model = GenerativeModel(
            model_name=self.config.default_text_model,
            safety_settings=self.safety_settings
        )

        # Vision model (for complex visual reasoning)
        self.vision_model = GenerativeModel(
            model_name=self.config.default_vision_model,
            safety_settings=self.safety_settings
        )

        # Image generation model
        self.image_gen_model = GenerativeModel(
            model_name=self.config.default_image_gen_model,
            safety_settings=self.safety_settings
        )

    async def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_instruction: System instruction for the model
            user_id: User ID for cost tracking
            project_id: Project/home ID for cost tracking

        Returns:
            Generated text
        """
        start_time = time.time()

        try:
            generation_config = {
                "temperature": temperature or self.config.default_temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Create model with system instruction if provided
            model = self.text_model
            if system_instruction:
                model = GenerativeModel(
                    model_name=self.config.default_text_model,
                    safety_settings=self.safety_settings,
                    system_instruction=system_instruction
                )

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Track cost (estimate tokens)
            estimated_tokens = len(prompt.split()) * 1.3 + len(response.text.split()) * 1.3
            self.cost_service.track_cost(
                service="gemini",
                operation="generate_text_flash",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "model": self.config.default_text_model,
                    "tokens": int(estimated_tokens),
                    "duration_ms": int((time.time() - start_time) * 1000)
                }
            )

            return response.text

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    async def generate_text_stream(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None
    ):
        """
        Stream text generation using Gemini.

        Yields incremental text chunks as they arrive from the model.
        Based on the official Gemini API streaming pattern using google.generativeai.
        """
        try:
            generation_config = {
                "temperature": temperature or self.config.default_temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Create model with system instruction if provided
            model = self.text_model
            if system_instruction:
                model = GenerativeModel(
                    model_name=self.config.default_text_model,
                    safety_settings=self.safety_settings,
                    system_instruction=system_instruction,
                )

            # Start streaming
            stream = model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True,
            )

            for chunk in stream:
                try:
                    text = getattr(chunk, "text", None)
                    if text:
                        # Yield raw text chunk
                        yield text
                except Exception as ie:
                    logger.debug(f"Error parsing stream chunk: {ie}")

            # Ensure stream is fully resolved
            try:
                stream.resolve()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error streaming text: {str(e)}", exc_info=True)
            raise

    async def analyze_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Analyze an image with Gemini Vision.

        Args:
            image: Image as file path, PIL Image, or bytes
            prompt: Analysis prompt
            temperature: Sampling temperature
            user_id: User ID for cost tracking
            project_id: Project/home ID for cost tracking

        Returns:
            Analysis result as text
        """
        start_time = time.time()

        try:
            # Load image
            pil_image = self._load_image(image)

            generation_config = {
                "temperature": temperature or 0.3,  # Lower temp for analysis
            }

            response = self.vision_model.generate_content(
                [prompt, pil_image],
                generation_config=generation_config
            )

            # Track cost (per image)
            self.cost_service.track_cost(
                service="gemini",
                operation="analyze_image",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "model": self.config.default_vision_model,
                    "duration_ms": int((time.time() - start_time) * 1000)
                }
            )

            return response.text

        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            raise
    async def transform_and_analyze_with_gemini_2_5_flash_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        transformation_prompt: str,
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        🚀 ULTIMATE 2-IN-1 API using Gemini 2.5 Flash Image

        Uses the NEW Gemini 2.5 Flash Image model that can BOTH:
        1. Transform/edit the image (like Imagen)
        2. Analyze the result comprehensively (like Vision)

        This reduces API calls from 3 to 2:
        - OLD: Imagen (transform) + Vision (analyze) + Grounding (products) = 3 calls
        - NEW: Gemini 2.5 Flash Image (transform+analyze) + Grounding (products) = 2 calls

        Args:
            image: Input image to transform
            transformation_prompt: How to transform the image (e.g., "modern minimalist style")
            room_hint: Optional room type hint

        Returns:
            {
                "transformed_image": PIL.Image,
                "analysis": {...},  # Complete comprehensive analysis
                "api_calls": 1      # Only 1 call for both transform + analyze!
            }
        """
        try:
            import json
            from google import genai
            from io import BytesIO

            # Initialize Gemini 2.5 Flash Image client
            client = genai.Client(api_key=self.config.api_key)

            # Prepare image
            if isinstance(image, bytes):
                pil_image = Image.open(BytesIO(image))
            elif isinstance(image, (str, Path)):
                pil_image = Image.open(image)
            elif isinstance(image, Image.Image):
                pil_image = image
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")

            # Build comprehensive prompt that does BOTH transformation AND analysis
            comprehensive_prompt = f"""Transform this image with the following style: {transformation_prompt}

After transforming, analyze the RESULT comprehensively and return ONLY valid JSON with this schema:

{{
  "room_type": "kitchen|bedroom|bathroom|living_room|etc",
  "colors": [{{"name": str, "hex": str, "rgb": [int,int,int], "location": str, "coverage_percentage": number}}],
  "materials": [{{"name": str, "location": str, "condition": str, "estimated_age_years": number}}],
  "styles": [str],
  "description": "Professional 50-word description",
  "dimensions": {{"length_m": number, "width_m": number, "height_m": number, "ceiling_type": str}},
  "openings": {{"windows": {{"count": int, "type": str, "estimated_size_each": str}}, "doors": {{...}}}},
  "surfaces": {{"walls": {{...}}, "ceiling": {{...}}, "floor": {{...}}}},
  "fixtures": [{{...}}],
  "furniture": [{{...}}],
  "appliances": [{{...}}],
  "architectural_features": [str],
  "object_counts": {{"cabinets": int, "chairs": int, "lights": int, etc}},
  "lighting": {{"type": str, "count": int, "brightness": str}},
  "storage": [{{...}}],
  "condition_assessment": {{...}},
  "renovation_potential": {{...}},
  "estimated_costs": {{...}},
  "assumptions": [str],
  "confidence": "low|medium|high",
  "analysis_notes": str
}}

Room context: {room_hint or 'unknown'}

CRITICAL DIMENSION ESTIMATION GUIDELINES:
- Use reference objects for scale estimation:
  • Standard door height: ~2.0-2.1m (6.5-7ft)
  • Standard door width: ~0.8-0.9m (2.5-3ft)
  • Kitchen counter height: ~0.9m (3ft)
  • Kitchen counter depth: ~0.6m (2ft)
  • Standard ceiling height: ~2.4-2.7m (8-9ft)
  • Kitchen island: typically 1.2-2.4m long (4-8ft)
  • Base cabinets: ~0.6m deep, ~0.9m tall
  • Upper cabinets: ~0.3m deep, ~0.9m tall
- Estimate room dimensions by counting how many reference objects fit
- For kitchens: measure wall length by counting cabinets (each ~0.6-0.9m wide)
- ALWAYS provide numeric estimates, never null/None
- If uncertain, provide best estimate with lower confidence score

Be EXTREMELY detailed. Extract ALL visible information from the TRANSFORMED image.
Calculate realistic room dimensions using visible reference objects."""

            # Make single API call that does BOTH transform + analyze
            logger.info("🚀 Using Gemini 2.5 Flash Image for transform + analyze in ONE call")
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[comprehensive_prompt, pil_image],
            )

            # Extract transformed image and analysis
            transformed_image = None
            analysis_text = None

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    analysis_text = part.text
                elif part.inline_data is not None:
                    transformed_image = Image.open(BytesIO(part.inline_data.data))

            if not transformed_image:
                raise ValueError("No transformed image returned from Gemini 2.5 Flash Image")

            # Parse analysis JSON
            if analysis_text:
                # Extract JSON from markdown if present
                if "```json" in analysis_text:
                    analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_text:
                    analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

                data = json.loads(analysis_text)
            else:
                data = {}

            # Normalize and calculate quantities
            normalized = self._normalize_and_calculate(data, room_hint)

            return {
                "transformed_image": transformed_image,
                "analysis": normalized,
                "api_calls": 1,
                "model_used": "gemini-2.5-flash-image-preview"
            }

        except Exception as e:
            logger.error(f"Error in Gemini 2.5 Flash Image transform+analyze: {str(e)}")
            logger.warning("Falling back to separate transform + analyze calls")
            raise

    def _normalize_and_calculate(self, data: Dict[str, Any], room_hint: Optional[str] = None) -> Dict[str, Any]:
        """Helper to normalize analysis data and calculate derived quantities"""
        import json as json_module

        # Ensure all required keys exist with defaults - COMPREHENSIVE structure
        normalized = {
            # Core identification
            "room_type": data.get("room_type", "unknown"),

            # Design elements
            "colors": data.get("colors", []),
            "materials": data.get("materials", []),
            "styles": data.get("styles", []),
            "description": data.get("description", ""),

            # Spatial data
            "dimensions": data.get("dimensions", {}),
            "openings": data.get("openings", {}),
            "surfaces": data.get("surfaces", {}),

            # Objects and features
            "fixtures": data.get("fixtures", []),
            "furniture": data.get("furniture", []),
            "appliances": data.get("appliances", []),
            "architectural_features": data.get("architectural_features", []),
            "object_counts": data.get("object_counts", {}),

            # Lighting and storage
            "lighting": data.get("lighting", {}),
            "storage": data.get("storage", []),

            # Condition and potential
            "condition_assessment": data.get("condition_assessment", {}),
            "renovation_potential": data.get("renovation_potential", {}),
            "estimated_costs": data.get("estimated_costs", {}),

            # Metadata
            "assumptions": data.get("assumptions", []),
            "confidence": data.get("confidence", "medium"),
            "analysis_notes": data.get("analysis_notes", "")
        }

        # Calculate derived quantities (areas, material quantities) - COMPREHENSIVE
        dims = normalized["dimensions"]
        Lm = dims.get("length_m")
        Wm = dims.get("width_m")
        Hm = dims.get("height_m")
        openings = normalized["openings"]

        areas = {}
        quantities = {}

        if Lm and Wm:
            floor_m2 = float(Lm) * float(Wm)
            areas["floor_m2"] = round(floor_m2, 2)
            areas["floor_sqft"] = round(floor_m2 * 10.7639, 1)
            areas["ceiling_m2"] = areas["floor_m2"]
            areas["ceiling_sqft"] = areas["floor_sqft"]

            # FLOORING - Multiple material types
            flooring_m2_with_waste = floor_m2 * 1.1  # 10% waste
            quantities["flooring"] = {
                "hardwood": {
                    "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                    "m2": round(flooring_m2_with_waste, 2),
                    "boxes_needed": round((flooring_m2_with_waste * 10.7639) / 20, 1),
                    "estimated_cost_cad": {
                        "min": round(flooring_m2_with_waste * 10.7639 * 3, 0),
                        "max": round(flooring_m2_with_waste * 10.7639 * 12, 0)
                    }
                },
                "vinyl_plank": {
                    "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                    "m2": round(flooring_m2_with_waste, 2),
                    "boxes_needed": round((flooring_m2_with_waste * 10.7639) / 24, 1),
                    "estimated_cost_cad": {
                        "min": round(flooring_m2_with_waste * 10.7639 * 2, 0),
                        "max": round(flooring_m2_with_waste * 10.7639 * 6, 0)
                    }
                },
                "tile": {
                    "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                    "m2": round(flooring_m2_with_waste, 2),
                    "tiles_12x12_inch": int((flooring_m2_with_waste * 10.7639) / 1),
                    "tiles_12x24_inch": int((flooring_m2_with_waste * 10.7639) / 2),
                    "tiles_30x60_cm": int(flooring_m2_with_waste / 0.18),
                    "estimated_cost_cad": {
                        "min": round(flooring_m2_with_waste * 10.7639 * 4, 0),
                        "max": round(flooring_m2_with_waste * 10.7639 * 15, 0)
                    }
                }
            }

        if Lm and Wm and Hm:
            perimeter_m = 2.0 * (float(Lm) + float(Wm))
            walls_m2_raw = perimeter_m * float(Hm)

            # Subtract openings
            openings_m2 = 0.0
            window_data = openings.get("windows", {})
            door_data = openings.get("doors", {})

            if isinstance(window_data, dict):
                window_count = window_data.get("count", 0)
                openings_m2 += window_count * 1.5
            elif isinstance(window_data, int):
                openings_m2 += window_data * 1.5

            if isinstance(door_data, dict):
                door_count = door_data.get("count", 0)
                openings_m2 += door_count * 1.9
            elif isinstance(door_data, int):
                openings_m2 += door_data * 1.9

            walls_m2 = max(0.0, walls_m2_raw - openings_m2)
            areas["walls_m2"] = round(walls_m2, 2)
            areas["walls_sqft"] = round(walls_m2 * 10.7639, 1)
            areas["perimeter_m"] = round(perimeter_m, 2)
            areas["perimeter_ft"] = round(perimeter_m * 3.28084, 1)

            # PAINT - Comprehensive calculation
            paint_coverage_m2_per_liter = 10.0
            quantities["paint"] = {
                "walls_only": {
                    "two_coats": {
                        "liters": round((walls_m2 / paint_coverage_m2_per_liter) * 2, 1),
                        "gallons": round(((walls_m2 / paint_coverage_m2_per_liter) * 2) / 3.785, 2)
                    }
                }
            }

            # TRIM & MOLDING
            baseboard_m = perimeter_m * 1.1
            quantities["trim"] = {
                "baseboard": {
                    "linear_ft": round(baseboard_m * 3.28084, 1),
                    "linear_m": round(baseboard_m, 1)
                }
            }

        normalized["areas"] = areas
        normalized["quantities"] = quantities

        return normalized

    async def analyze_home_improvement_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        🏠 UNIFIED HOME IMPROVEMENT IMAGE ANALYSIS API

        Single comprehensive API that analyzes any home improvement image and returns
        ALL information needed for Design Studio, Chat, Virtual Staging, and other features.

        Returns complete analysis in ONE API call:
        {
            "colors": [{"name": str, "hex": str, "rgb": [int, int, int]}],
            "materials": [str],
            "styles": [str],
            "description": str,
            "dimensions": {"length_m": float, "width_m": float, "height_m": float},
            "openings": {"windows": int, "doors": int},
            "object_counts": {"sofa": int, "chair": int, ...},
            "areas": {"floor_m2": float, "walls_m2": float, "ceiling_m2": float},
            "quantities": {
                "paint_gallons_two_coats": float,
                "paint_liters_two_coats": float,
                "flooring_sqft": float,
                "flooring_m2": float,
                "baseboard_linear_ft": float,
                "tile_30x60cm_count": int
            },
            "assumptions": [str],
            "confidence": "low|medium|high"
        }

        This replaces the need for multiple separate API calls:
        - analyze_design() ❌ DEPRECATED
        - analyze_spatial_and_quantities() ❌ DEPRECATED
        """
        try:
            pil_image = self._load_image(image)

            # Single comprehensive prompt that gets EVERYTHING
            comprehensive_prompt = f"""You are a professional home improvement analysis AI. Analyze this interior photo and return ONLY a compact JSON object with ALL of the following information:

Room context: {room_hint or 'unknown'}

Return this EXACT JSON schema with MAXIMUM detail:
{{
  "room_type": "kitchen|bedroom|bathroom|living_room|dining_room|etc",
  "colors": [
    {{"name": "Color Name", "hex": "#RRGGBB", "rgb": [R, G, B], "location": "walls|ceiling|floor|cabinets|trim|etc", "coverage_percentage": number}}
  ],
  "materials": [
    {{"name": "material_name", "location": "where_used", "condition": "new|good|fair|poor", "estimated_age_years": number|null}}
  ],
  "styles": ["style1", "style2", "style3"],
  "description": "Professional 50-word description highlighting key features and design elements",
  "dimensions": {{
    "length_m": number,
    "width_m": number,
    "height_m": number,
    "ceiling_type": "flat|vaulted|tray|coffered"
  }},
  "openings": {{
    "windows": {{"count": integer, "type": "single_hung|double_hung|casement|picture", "estimated_size_each": "WxH in meters"}},
    "doors": {{"count": integer, "type": "standard|french|sliding|pocket", "estimated_size_each": "WxH in meters"}},
    "archways": integer
  }},
  "surfaces": {{
    "walls": {{"material": "drywall|plaster|brick|wood", "finish": "painted|wallpaper|tile|paneling", "condition": "excellent|good|fair|poor"}},
    "ceiling": {{"material": "drywall|plaster|wood", "finish": "painted|textured|exposed", "features": ["crown_molding", "recessed_lighting", "etc"]}},
    "floor": {{"material": "hardwood|tile|carpet|vinyl|laminate|concrete", "finish": "natural|stained|polished", "pattern": "straight|diagonal|herringbone|etc"}}
  }},
  "fixtures": [
    {{"type": "light_fixture|outlet|switch|vent|etc", "count": integer, "location": "ceiling|wall|floor", "style": "modern|traditional|etc"}}
  ],
  "furniture": [
    {{"type": "sofa|table|chair|bed|etc", "count": integer, "material": "wood|metal|fabric", "style": "modern|traditional|etc", "estimated_dimensions": "LxWxH in meters"}}
  ],
  "appliances": [
    {{"type": "refrigerator|stove|dishwasher|etc", "brand_visible": true|false, "finish": "stainless|white|black|etc", "estimated_age": "new|1-5yr|5-10yr|10+yr"}}
  ],
  "architectural_features": ["crown_molding", "baseboards", "wainscoting", "built_in_shelving", "fireplace", "etc"],
  "lighting": {{
    "natural_light": "excellent|good|moderate|poor",
    "artificial_fixtures": {{"count": integer, "types": ["recessed", "pendant", "chandelier", "sconce", "etc"]}},
    "estimated_brightness": "very_bright|bright|moderate|dim"
  }},
  "storage": [
    {{"type": "cabinets|closet|shelving|pantry", "count": integer, "material": "wood|metal|wire", "estimated_capacity": "description"}}
  ],
  "condition_assessment": {{
    "overall": "excellent|good|fair|poor|needs_renovation",
    "walls": "excellent|good|fair|poor",
    "floor": "excellent|good|fair|poor",
    "ceiling": "excellent|good|fair|poor",
    "visible_issues": ["cracks", "stains", "wear", "outdated", "etc"]
  }},
  "renovation_potential": {{
    "easy_updates": ["paint", "hardware", "lighting", "etc"],
    "medium_projects": ["flooring", "countertops", "backsplash", "etc"],
    "major_projects": ["layout_change", "structural", "plumbing", "electrical", "etc"]
  }},
  "estimated_costs": {{
    "paint_refresh": {{"min_cad": number, "max_cad": number}},
    "flooring_replacement": {{"min_cad": number, "max_cad": number}},
    "full_renovation": {{"min_cad": number, "max_cad": number}}
  }},
  "object_counts": {{"object_name": count}},
  "assumptions": ["assumption1", "assumption2", "etc"],
  "confidence": "low|medium|high",
  "analysis_notes": "Any additional observations or recommendations"
}}

CRITICAL INSTRUCTIONS:
1. Colors: Extract 7-10 colors with EXACT locations and coverage percentages
2. Materials: List ALL materials with location, condition, and estimated age
3. Surfaces: Detailed analysis of walls, ceiling, floor with materials and condition
4. Fixtures: Count and describe ALL visible fixtures (lights, outlets, vents, etc.)
5. Furniture: List ALL furniture with dimensions and materials
6. Appliances: Identify ALL appliances with finish and estimated age
7. Architectural Features: List ALL features (molding, baseboards, built-ins, etc.)
8. Lighting: Assess natural and artificial lighting comprehensively
9. Storage: Identify ALL storage solutions with capacity estimates
10. Condition: Assess overall condition and identify any visible issues
11. Renovation Potential: Categorize possible updates by difficulty
12. Estimated Costs: Provide realistic CAD price ranges for common projects
13. Dimensions: Use reference objects for accurate measurements
14. Be EXTREMELY detailed - customers need this for planning and budgeting

Return ONLY valid JSON, no markdown, no explanation."""

            response = self.vision_model.generate_content([
                comprehensive_prompt,
                pil_image,
            ], generation_config={"temperature": 0.2})

            text = getattr(response, "text", "") or "{}"

            # Parse JSON
            import json, re
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                logger.error("No JSON found in response")
                return {"error": "No JSON in response"}

            data = json.loads(match.group(0))

            # Validate and normalize structure
            if not isinstance(data, dict):
                return {"error": "Invalid JSON structure"}

            # Ensure all required keys exist with defaults - COMPREHENSIVE structure
            normalized = {
                # Core identification
                "room_type": data.get("room_type", "unknown"),

                # Design elements
                "colors": data.get("colors", []),
                "materials": data.get("materials", []),
                "styles": data.get("styles", []),
                "description": data.get("description", ""),

                # Spatial data
                "dimensions": data.get("dimensions", {}),
                "openings": data.get("openings", {}),
                "surfaces": data.get("surfaces", {}),

                # Objects and features
                "fixtures": data.get("fixtures", []),
                "furniture": data.get("furniture", []),
                "appliances": data.get("appliances", []),
                "architectural_features": data.get("architectural_features", []),
                "object_counts": data.get("object_counts", {}),

                # Lighting and storage
                "lighting": data.get("lighting", {}),
                "storage": data.get("storage", []),

                # Condition and potential
                "condition_assessment": data.get("condition_assessment", {}),
                "renovation_potential": data.get("renovation_potential", {}),
                "estimated_costs": data.get("estimated_costs", {}),

                # Metadata
                "assumptions": data.get("assumptions", []),
                "confidence": data.get("confidence", "medium"),
                "analysis_notes": data.get("analysis_notes", "")
            }

            # Calculate derived quantities (areas, material quantities) - COMPREHENSIVE
            dims = normalized["dimensions"]
            Lm = dims.get("length_m")
            Wm = dims.get("width_m")
            Hm = dims.get("height_m")
            openings = normalized["openings"]

            areas = {}
            quantities = {}

            if Lm and Wm:
                floor_m2 = float(Lm) * float(Wm)
                areas["floor_m2"] = round(floor_m2, 2)
                areas["floor_sqft"] = round(floor_m2 * 10.7639, 1)
                areas["ceiling_m2"] = areas["floor_m2"]
                areas["ceiling_sqft"] = areas["floor_sqft"]

                # FLOORING - Multiple material types
                flooring_m2_with_waste = floor_m2 * 1.1  # 10% waste
                quantities["flooring"] = {
                    "hardwood": {
                        "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                        "m2": round(flooring_m2_with_waste, 2),
                        "boxes_needed": round((flooring_m2_with_waste * 10.7639) / 20, 1),  # ~20 sqft per box
                        "estimated_cost_cad": {
                            "min": round(flooring_m2_with_waste * 10.7639 * 3, 0),  # $3/sqft
                            "max": round(flooring_m2_with_waste * 10.7639 * 12, 0)  # $12/sqft
                        }
                    },
                    "vinyl_plank": {
                        "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                        "m2": round(flooring_m2_with_waste, 2),
                        "boxes_needed": round((flooring_m2_with_waste * 10.7639) / 24, 1),  # ~24 sqft per box
                        "estimated_cost_cad": {
                            "min": round(flooring_m2_with_waste * 10.7639 * 2, 0),  # $2/sqft
                            "max": round(flooring_m2_with_waste * 10.7639 * 6, 0)  # $6/sqft
                        }
                    },
                    "tile": {
                        "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                        "m2": round(flooring_m2_with_waste, 2),
                        "tiles_12x12_inch": int((flooring_m2_with_waste * 10.7639) / 1),  # 1 sqft per tile
                        "tiles_12x24_inch": int((flooring_m2_with_waste * 10.7639) / 2),  # 2 sqft per tile
                        "tiles_30x60_cm": int(flooring_m2_with_waste / 0.18),  # 0.18 m² per tile
                        "estimated_cost_cad": {
                            "min": round(flooring_m2_with_waste * 10.7639 * 4, 0),  # $4/sqft
                            "max": round(flooring_m2_with_waste * 10.7639 * 15, 0)  # $15/sqft
                        }
                    },
                    "carpet": {
                        "sqft": round(flooring_m2_with_waste * 10.7639, 1),
                        "m2": round(flooring_m2_with_waste, 2),
                        "estimated_cost_cad": {
                            "min": round(flooring_m2_with_waste * 10.7639 * 2, 0),  # $2/sqft
                            "max": round(flooring_m2_with_waste * 10.7639 * 8, 0)  # $8/sqft
                        }
                    }
                }

            if Lm and Wm and Hm:
                perimeter_m = 2.0 * (float(Lm) + float(Wm))
                walls_m2_raw = perimeter_m * float(Hm)

                # Subtract openings - Enhanced calculation
                openings_m2 = 0.0
                window_data = openings.get("windows", {})
                door_data = openings.get("doors", {})

                if isinstance(window_data, dict):
                    window_count = window_data.get("count", 0)
                    openings_m2 += window_count * 1.5  # ~1.5 m² per window
                elif isinstance(window_data, int):
                    openings_m2 += window_data * 1.5

                if isinstance(door_data, dict):
                    door_count = door_data.get("count", 0)
                    openings_m2 += door_count * 1.9  # ~1.9 m² per door
                elif isinstance(door_data, int):
                    openings_m2 += door_data * 1.9

                walls_m2 = max(0.0, walls_m2_raw - openings_m2)
                areas["walls_m2"] = round(walls_m2, 2)
                areas["walls_sqft"] = round(walls_m2 * 10.7639, 1)
                areas["perimeter_m"] = round(perimeter_m, 2)
                areas["perimeter_ft"] = round(perimeter_m * 3.28084, 1)

                # PAINT - Comprehensive calculation
                paint_coverage_m2_per_liter = 10.0  # Standard coverage
                quantities["paint"] = {
                    "walls_only": {
                        "one_coat": {
                            "liters": round(walls_m2 / paint_coverage_m2_per_liter, 1),
                            "gallons": round((walls_m2 / paint_coverage_m2_per_liter) / 3.785, 2)
                        },
                        "two_coats": {
                            "liters": round((walls_m2 / paint_coverage_m2_per_liter) * 2, 1),
                            "gallons": round(((walls_m2 / paint_coverage_m2_per_liter) * 2) / 3.785, 2)
                        },
                        "estimated_cost_cad": {
                            "min": round(((walls_m2 / paint_coverage_m2_per_liter) * 2 / 3.785) * 40, 0),  # $40/gal
                            "max": round(((walls_m2 / paint_coverage_m2_per_liter) * 2 / 3.785) * 80, 0)  # $80/gal
                        }
                    },
                    "walls_and_ceiling": {
                        "total_area_m2": round(walls_m2 + floor_m2, 2) if floor_m2 else None,
                        "two_coats": {
                            "liters": round(((walls_m2 + (floor_m2 if floor_m2 else 0)) / paint_coverage_m2_per_liter) * 2, 1),
                            "gallons": round((((walls_m2 + (floor_m2 if floor_m2 else 0)) / paint_coverage_m2_per_liter) * 2) / 3.785, 2)
                        }
                    },
                    "primer": {
                        "liters": round(walls_m2 / paint_coverage_m2_per_liter, 1),
                        "gallons": round((walls_m2 / paint_coverage_m2_per_liter) / 3.785, 2),
                        "estimated_cost_cad": {
                            "min": round((walls_m2 / paint_coverage_m2_per_liter / 3.785) * 30, 0),  # $30/gal
                            "max": round((walls_m2 / paint_coverage_m2_per_liter / 3.785) * 50, 0)  # $50/gal
                        }
                    }
                }

                # TRIM & MOLDING - Comprehensive
                baseboard_m = perimeter_m * 1.1  # 10% waste
                quantities["trim"] = {
                    "baseboard": {
                        "linear_ft": round(baseboard_m * 3.28084, 1),
                        "linear_m": round(baseboard_m, 1),
                        "pieces_8ft": int((baseboard_m * 3.28084) / 8) + 1,
                        "estimated_cost_cad": {
                            "min": round((baseboard_m * 3.28084) * 1.5, 0),  # $1.5/ft
                            "max": round((baseboard_m * 3.28084) * 5, 0)  # $5/ft
                        }
                    },
                    "crown_molding": {
                        "linear_ft": round(baseboard_m * 3.28084, 1),
                        "linear_m": round(baseboard_m, 1),
                        "pieces_8ft": int((baseboard_m * 3.28084) / 8) + 1,
                        "estimated_cost_cad": {
                            "min": round((baseboard_m * 3.28084) * 2, 0),  # $2/ft
                            "max": round((baseboard_m * 3.28084) * 8, 0)  # $8/ft
                        }
                    },
                    "door_casing": {
                        "sets_needed": door_data.get("count", 0) if isinstance(door_data, dict) else door_data if isinstance(door_data, int) else 0,
                        "estimated_cost_cad": {
                            "min": (door_data.get("count", 0) if isinstance(door_data, dict) else door_data if isinstance(door_data, int) else 0) * 30,
                            "max": (door_data.get("count", 0) if isinstance(door_data, dict) else door_data if isinstance(door_data, int) else 0) * 100
                        }
                    },
                    "window_casing": {
                        "sets_needed": window_data.get("count", 0) if isinstance(window_data, dict) else window_data if isinstance(window_data, int) else 0,
                        "estimated_cost_cad": {
                            "min": (window_data.get("count", 0) if isinstance(window_data, dict) else window_data if isinstance(window_data, int) else 0) * 25,
                            "max": (window_data.get("count", 0) if isinstance(window_data, dict) else window_data if isinstance(window_data, int) else 0) * 80
                        }
                    }
                }

                # DRYWALL (if needed for renovation)
                quantities["drywall"] = {
                    "sheets_4x8": int((walls_m2 * 10.7639) / 32) + 1,  # 32 sqft per sheet
                    "sheets_4x12": int((walls_m2 * 10.7639) / 48) + 1,  # 48 sqft per sheet
                    "estimated_cost_cad": {
                        "min": int((walls_m2 * 10.7639) / 32) * 15,  # $15/sheet
                        "max": int((walls_m2 * 10.7639) / 32) * 25  # $25/sheet
                    }
                }

            normalized["areas"] = areas
            normalized["quantities"] = quantities

            logger.info(
                "[HomeImprovementAnalysis] Complete: colors=%d materials=%d styles=%d dims=%sx%sx%s confidence=%s",
                len(normalized["colors"]),
                len(normalized["materials"]),
                len(normalized["styles"]),
                Lm, Wm, Hm,
                normalized["confidence"]
            )

            return normalized

        except Exception as e:
            logger.error(f"Error in analyze_home_improvement_image: {e}", exc_info=True)
            return {"error": str(e)}

    async def analyze_design(
        self,
        image: Union[str, Path, Image.Image, bytes],
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: Use analyze_home_improvement_image() instead.

        This method is kept for backward compatibility but will be removed in future versions.
        """
        logger.warning("analyze_design() is deprecated. Use analyze_home_improvement_image() instead.")
        result = await self.analyze_home_improvement_image(image, room_hint)
        # Return only the design-related fields for backward compatibility
        return {
            "colors": result.get("colors", []),
            "materials": result.get("materials", []),
            "styles": result.get("styles", []),
            "description": result.get("description", "")
        }

    async def analyze_spatial_and_quantities(
        self,
        image: Union[str, Path, Image.Image, bytes],
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: Use analyze_home_improvement_image() instead.

        This method is kept for backward compatibility but will be removed in future versions.
        The new unified API returns spatial data + design analysis in ONE call.
        """
        logger.warning("analyze_spatial_and_quantities() is deprecated. Use analyze_home_improvement_image() instead.")
        result = await self.analyze_home_improvement_image(image, room_hint)
        # Return only the spatial-related fields for backward compatibility
        return {
            "dimensions": result.get("dimensions", {}),
            "openings": result.get("openings", {}),
            "object_counts": result.get("object_counts", {}),
            "assumptions": result.get("assumptions", []),
            "confidence": result.get("confidence", "medium")
        }

    async def analyze_with_bounding_boxes(
        self,
        image: Union[str, Path, Image.Image, bytes],
        objects_to_detect: Optional[List[str]] = None,
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect objects in an image and return bounding boxes with normalized coordinates.

        Based on Google Gemini Cookbook spatial understanding examples:
        https://github.com/google-gemini/cookbook/blob/main/quickstarts/Spatial_understanding.ipynb

        Args:
            image: Image to analyze
            objects_to_detect: List of specific objects to detect (e.g., ["sofa", "lamp", "window"])
                              If None, detects all notable objects
            room_hint: Optional room type hint for better context

        Returns:
            Dict with structure:
            {
                "objects": [
                    {
                        "label": str,
                        "confidence": float,
                        "bounding_box": {
                            "y_min": float,  # normalized 0-1000
                            "x_min": float,
                            "y_max": float,
                            "x_max": float
                        }
                    }
                ],
                "image_dimensions": {"width": int, "height": int}
            }
        """
        try:
            pil_image = self._load_image(image)
            width, height = pil_image.size

            # Build detection prompt
            if objects_to_detect:
                objects_str = ", ".join(objects_to_detect)
                detection_prompt = f"Detect and locate these objects in the image: {objects_str}."
            else:
                detection_prompt = "Detect and locate all notable objects, furniture, fixtures, and architectural elements in this interior image."

            if room_hint:
                detection_prompt += f" Room type: {room_hint}."

            prompt = (
                f"{detection_prompt}\n\n"
                "Return ONLY a JSON array where each object has:\n"
                "{\n"
                "  \"label\": string (object name),\n"
                "  \"confidence\": float (0.0-1.0),\n"
                "  \"bounding_box\": {\n"
                "    \"y_min\": float (0-1000, normalized),\n"
                "    \"x_min\": float (0-1000, normalized),\n"
                "    \"y_max\": float (0-1000, normalized),\n"
                "    \"x_max\": float (0-1000, normalized)\n"
                "  }\n"
                "}\n"
                "Use normalized coordinates where 0 is top/left and 1000 is bottom/right."
            )

            response = self.vision_model.generate_content(
                [prompt, pil_image],
                generation_config={"temperature": 0.1}
            )

            text = getattr(response, "text", "") or "[]"
            import json, re
            # Extract JSON array
            match = re.search(r"\[[\s\S]*\]", text)
            objects = json.loads(match.group(0)) if match else []

            logger.info(f"[BoundingBoxes] Detected {len(objects)} objects")

            return {
                "objects": objects if isinstance(objects, list) else [],
                "image_dimensions": {"width": width, "height": height}
            }

        except Exception as e:
            logger.error(f"analyze_with_bounding_boxes failed: {e}", exc_info=True)
            return {"error": str(e), "objects": [], "image_dimensions": {}}

    async def analyze_with_segmentation(
        self,
        image: Union[str, Path, Image.Image, bytes],
        objects_to_segment: Optional[List[str]] = None,
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Segment objects in an image and return segmentation masks.

        Based on Google Gemini Cookbook spatial understanding examples.
        Note: Segmentation masks are experimental and may not be available in all regions.

        Args:
            image: Image to analyze
            objects_to_segment: List of specific objects to segment
            room_hint: Optional room type hint

        Returns:
            Dict with structure:
            {
                "segments": [
                    {
                        "label": str,
                        "confidence": float,
                        "bounding_box": {...},
                        "mask": str  # base64 encoded PNG mask
                    }
                ]
            }
        """
        try:
            pil_image = self._load_image(image)

            # Build segmentation prompt
            if objects_to_segment:
                objects_str = ", ".join(objects_to_segment)
                seg_prompt = f"Segment these objects: {objects_str}."
            else:
                seg_prompt = "Segment all major objects, furniture, and architectural elements."

            if room_hint:
                seg_prompt += f" Room type: {room_hint}."

            prompt = (
                f"{seg_prompt}\n\n"
                "For each object, provide:\n"
                "1. Label (object name)\n"
                "2. Confidence score (0.0-1.0)\n"
                "3. Bounding box with normalized coordinates (0-1000)\n"
                "4. Segmentation mask as base64 encoded PNG\n\n"
                "Return as JSON array."
            )

            response = self.vision_model.generate_content(
                [prompt, pil_image],
                generation_config={"temperature": 0.1}
            )

            text = getattr(response, "text", "") or "[]"
            import json, re
            match = re.search(r"\[[\s\S]*\]", text)
            segments = json.loads(match.group(0)) if match else []

            logger.info(f"[Segmentation] Segmented {len(segments)} objects")

            return {
                "segments": segments if isinstance(segments, list) else []
            }

        except Exception as e:
            logger.error(f"analyze_with_segmentation failed: {e}", exc_info=True)
            return {"error": str(e), "segments": []}

    async def analyze_multi_image_sequence(
        self,
        images: List[Union[str, Path, Image.Image, bytes]],
        sequence_type: str = "transformation",
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a sequence of images to detect patterns, changes, or progression.

        Based on Google Gemini Cookbook "Guess the Shape" multi-image reasoning example.

        Args:
            images: List of images in sequence order
            sequence_type: Type of sequence - "transformation", "before_after", "progress", "variations"
            prompt: Optional custom prompt, otherwise uses default based on sequence_type

        Returns:
            Dict with analysis results including detected changes, patterns, and recommendations
        """
        try:
            # Load all images
            pil_images = [self._load_image(img) for img in images]

            # Build prompt based on sequence type
            if prompt is None:
                if sequence_type == "transformation":
                    prompt = (
                        "Analyze this sequence of room transformation images. "
                        "Identify what changed between each image: colors, materials, furniture, layout, lighting. "
                        "Return JSON with: changes (array of change descriptions), "
                        "progression_quality (rating 1-10), recommendations (array of suggestions)."
                    )
                elif sequence_type == "before_after":
                    prompt = (
                        "Compare the before and after images of this room renovation. "
                        "Return JSON with: changes_made (array), improvements (array), "
                        "estimated_cost_range (string), diy_feasibility (low/medium/high)."
                    )
                elif sequence_type == "progress":
                    prompt = (
                        "Analyze this renovation progress sequence. "
                        "Return JSON with: stages (array of stage descriptions with completion %), "
                        "current_stage (string), estimated_completion (percentage), "
                        "quality_issues (array of concerns if any)."
                    )
                elif sequence_type == "variations":
                    prompt = (
                        "Compare these design variations for the same space. "
                        "Return JSON with: variations (array with style, pros, cons for each), "
                        "best_option (index and reason), price_comparison (relative costs)."
                    )
                else:
                    prompt = "Analyze this sequence of images and describe the progression or changes."

            # Combine prompt with all images
            content = [prompt] + pil_images

            response = self.vision_model.generate_content(
                content,
                generation_config={"temperature": 0.3}
            )

            text = getattr(response, "text", "") or "{}"
            import json, re
            match = re.search(r"\{[\s\S]*\}", text)
            analysis = json.loads(match.group(0)) if match else {"raw": text}

            logger.info(f"[MultiImage] Analyzed {len(images)} images, type={sequence_type}")

            return analysis if isinstance(analysis, dict) else {"raw": text}

        except Exception as e:
            logger.error(f"analyze_multi_image_sequence failed: {e}", exc_info=True)
            return {"error": str(e)}

    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def suggest_products_with_grounding(
        self,
        summary_or_grounding: Dict[str, Any],
        max_items: int = 5,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ToolResponse:
        """
        Suggest products with Google Search grounding enabled.

        Accepts either a simple design summary dict or a diff-aware payload with keys:
        {
          "user_prompt": str,
          "requested_changes": [str],
          "original_summary": { ... },
          "new_summary": { ... }
        }

        Uses Gemini text model with tools=[{"google_search": {}}] per official docs:
        https://ai.google.dev/gemini-api/docs/google-search
        
        Features:
        - Intelligent caching (24h TTL)
        - Circuit breaker pattern for resilience
        - Retry logic with exponential backoff
        - Comprehensive monitoring and metrics
        """
        start_time = time.time()
        search_count = 0  # Track number of Google Search calls
        
        # Create cache key from query
        cache_key = str(summary_or_grounding)
        location_hint = summary_or_grounding.get("location_hint", "Canada") if isinstance(summary_or_grounding, dict) else "Canada"
        
        # Check cache first
        cached_result = self.grounding_cache.get(cache_key, location_hint)
        if cached_result:
            logger.info("[Grounding] Cache HIT for query: %s", cache_key[:50])
            # Record metrics for cache hit
            metrics = GroundingMetrics(
                query=cache_key[:100],
                success=True,
                latency_ms=int((time.time() - start_time) * 1000),
                cost_usd=0.0,  # No API cost for cache hit
                cached=True,
                sources_found=len(cached_result.get("sources", []))
            )
            self.grounding_monitor.record_request(metrics)
            
            return ToolResponse(
                success=True,
                data=cached_result,
                sources=cached_result.get("sources", []),
                cost_usd=0.0,
                latency_ms=metrics.latency_ms,
                cached=True
            )
        
        logger.info("[Grounding] Cache MISS for query: %s", cache_key[:50])

        try:
            # Build targeted prompt with strong shopping guidance and context.
            payload = summary_or_grounding or {}
            is_diff = isinstance(payload, dict) and (
                "original_summary" in payload or "new_summary" in payload
            )

            # Canada-specific market and sourcing guidance
            location_hint = (payload.get("location_hint") or "Canada").strip()
            retailer_hint = (
                "Market: Canada. STRICT: Use .ca domains or Canada sections (/en-ca,/fr-ca,/ca/). Avoid US-only or non-shippable items. "
                f"If a location is known, prefer nearest stores around: {location_hint}. "
                "Bias your Google Search queries with site:.ca and keywords like 'Canada' and 'CAD'. "
                "Include a mix of major Canadian retailers AND small local Canadian businesses when relevant. "
                "Prioritize PDPs from: Home Depot Canada, RONA, Canadian Tire, Home Hardware, IKEA.ca, Wayfair.ca, Costco.ca, BestBuy.ca, The Brick, Leon's, Structube, Amazon.ca, Walmart.ca. "
                "Return canonical product URLs (no tracking params). Avoid blog posts, category pages, and Pinterest."
            )

            logger.info("[Grounding] Start. location_hint=%s is_diff=%s", location_hint, is_diff)
            if is_diff:
                user_prompt = payload.get("user_prompt", "")
                changes = payload.get("requested_changes", []) or []
                original = payload.get("original_summary", {})
                new = payload.get("new_summary", {})
                changes_txt = ", ".join(changes) if changes else "unspecified"

                # Build brand preferences and per-category constraint text
                brand_lines: List[str] = []
                constraint_lines: List[str] = []
                for cat in changes:
                    prefs = CATEGORY_BRAND_PREFERENCES.get(cat)
                    if prefs:
                        brand_lines.append(f"{cat}: {', '.join(prefs)}")
                    hint = CATEGORY_CONSTRAINT_HINTS.get(cat)
                    if hint:
                        constraint_lines.append(f"{cat}: {hint}")
                brand_text = ("Brand preferences per category: " + "; ".join(brand_lines) + ".\n") if brand_lines else ""
                constraint_text = ("Category-specific constraints (include when applicable): " + " ".join(constraint_lines) + "\n") if constraint_lines else ""

                # Extract style cues from comprehensive analysis data
                def _as_list(val):
                    return val if isinstance(val, list) else []

                # Extract colors with location context
                new_colors = []
                for c in _as_list(new.get("colors", [])):
                    if isinstance(c, dict):
                        name = c.get("name", "")
                        hex_code = c.get("hex", "")
                        location = c.get("location", "")
                        if name:
                            label = f"{name} ({hex_code})" if hex_code else name
                            if location:
                                label += f" for {location}"
                            new_colors.append(label)
                    elif isinstance(c, str):
                        new_colors.append(c)

                # Extract materials with location context
                material_list = []
                for m in _as_list(new.get("materials", [])):
                    if isinstance(m, dict):
                        name = m.get("name", "")
                        location = m.get("location", "")
                        if name:
                            label = f"{name} ({location})" if location else name
                            material_list.append(label)
                    elif isinstance(m, str):
                        material_list.append(m)

                materials = ", ".join(material_list)
                styles = ", ".join(_as_list(new.get("styles", [])))
                color_txt = ", ".join(new_colors) if new_colors else ""

                # Extract room type and dimensions for better context
                room_type = new.get("room_type", "room")
                dimensions = new.get("dimensions", {})
                quantities = new.get("quantities", {})

                # Build dimension context
                dim_length = dimensions.get('length_m')
                dim_width = dimensions.get('width_m')
                dim_height = dimensions.get('height_m')

                # Create dimension text with fallback
                if dim_length and dim_width and dim_height:
                    dimension_text = f"{dim_length}m × {dim_width}m × {dim_height}m"
                elif dim_length and dim_width:
                    dimension_text = f"{dim_length}m × {dim_width}m (height unknown)"
                else:
                    dimension_text = "dimensions not available (estimate medium-sized room)"

                # Build quantity context for search
                quantity_context = ""
                if quantities:
                    paint_data = quantities.get("paint", {})
                    flooring_data = quantities.get("flooring", {})
                    trim_data = quantities.get("trim", {})

                    if paint_data:
                        walls_paint = paint_data.get("walls_only", {}).get("two_coats", {})
                        if walls_paint and walls_paint.get('gallons', 0) > 0:
                            quantity_context += f"Paint needed: {walls_paint.get('gallons', 0)} gallons. "

                    if flooring_data:
                        hardwood = flooring_data.get("hardwood", {})
                        if hardwood and hardwood.get('sqft', 0) > 0:
                            quantity_context += f"Flooring needed: {hardwood.get('sqft', 0)} sqft. "

                    if trim_data:
                        baseboard = trim_data.get("baseboard", {})
                        if baseboard and baseboard.get('linear_ft', 0) > 0:
                            quantity_context += f"Baseboard needed: {baseboard.get('linear_ft', 0)} linear ft. "

                # If no quantities calculated, provide general guidance
                if not quantity_context:
                    quantity_context = "Quantities not calculated - recommend standard package sizes for medium room. "

                regional_text = (
                    f"Region targeting: Canada (.ca domains) and CAD prices. If possible, include nearest Canadian stores around: {location_hint}. "
                    "In each product's brief_reason, mention Canada availability and the retailer/store (and nearest store if known).\n"
                )

                prompt = (
                    "You are a professional home improvement product recommender with access to real-time product search. "
                    "Based on comprehensive room analysis, recommend specific products customers can purchase.\n\n"
                    f"🏠 ROOM TYPE: {room_type}\n"
                    f"📐 ROOM SIZE: {dimension_text}\n"
                    f"🎨 TRANSFORMATION REQUEST: {user_prompt}\n"
                    f"📊 CHANGE CATEGORIES: {changes_txt}\n"
                    f"🎨 TARGET COLORS: {color_txt}\n"
                    f"🏗️  TARGET MATERIALS: {materials}\n"
                    f"✨ TARGET STYLES: {styles}\n"
                    f"📏 QUANTITIES NEEDED: {quantity_context}\n\n"
                    f"{brand_text}{constraint_text}"
                    f"ORIGINAL ROOM ANALYSIS:\n{original}\n\n"
                    f"TRANSFORMED ROOM ANALYSIS:\n{new}\n\n"
                    f"{regional_text}{retailer_hint}\n\n"
                    f"IMPORTANT: Even if exact dimensions/quantities are unavailable, still recommend products based on the style, colors, and materials.\n"
                    f"Recommend up to {max_items} specific products that enable this transformation.\n\n"
                    "For each product:\n"
                    "  - name: Specific product with brand (e.g., 'BEHR Premium Plus Interior Paint in Ultra Pure White 3.79L')\n"
                    "  - category: paint|flooring|furniture|lighting|decor|hardware|appliance|fixture|tile|countertop|cabinet|trim|other\n"
                    "  - brief_reason: Explain:\n"
                    "      • How this achieves the transformation\n"
                    "      • Why this specific product/brand\n"
                    "      • Quantity needed for room size\n"
                    "      • Canada availability and retailers\n"
                    "  - price_estimate: Realistic CAD price with quantity (e.g., 'CAD 45.99 per gallon, need 2 gallons = $91.98 total')\n"
                    "  - url: Use natural language search query optimized for Canadian retailers:\n"
                    "      • Include brand, color, finish, size, 'Canada'\n"
                    "      • Examples:\n"
                    "          'BEHR Premium Plus interior paint ultra pure white 3.79L Home Depot Canada'\n"
                    "          'white shaker cabinet pulls brushed nickel 3 inch Lowe\\'s Canada'\n"
                    "          'light oak vinyl plank flooring 20 sqft box Lifeproof Home Depot Canada'\n\n"
                    "CRITICAL: Focus on products matching ACTUAL CHANGES. Calculate realistic quantities from room dimensions.\n"
                    "Prioritize: Home Depot Canada, Lowe's Canada, IKEA Canada, Wayfair.ca, Amazon.ca, Rona, Canadian Tire.\n\n"
                    "Return ONLY valid JSON matching this schema exactly: {\n"
                    "  \"products\": [ { \"name\": string, \"category\": string|null, \"brief_reason\": string|null, \"price_estimate\": string|null, \"url\": string } ],\n"
                    "  \"sources\": [ string ]\n"
                    "}."
                )
            else:
                # Even without diff, honor any caller-provided requested_changes for brand/constraints
                changes = payload.get("requested_changes", []) or []
                brand_lines: List[str] = []
                constraint_lines: List[str] = []
                for cat in changes:
                    prefs = CATEGORY_BRAND_PREFERENCES.get(cat)
                    if prefs:
                        brand_lines.append(f"{cat}: {', '.join(prefs)}")
                    hint = CATEGORY_CONSTRAINT_HINTS.get(cat)
                    if hint:
                        constraint_lines.append(f"{cat}: {hint}")
                brand_text = ("Brand preferences per category: " + "; ".join(brand_lines) + ".\n") if brand_lines else ""
                constraint_text = ("Category-specific constraints (include when applicable): " + " ".join(constraint_lines) + "\n") if constraint_lines else ""

                prompt = (
                    "Given this interior design summary, suggest up to "
                    f"{max_items} purchasable products that match the style/colors/materials. "
                    "Return direct product detail page URLs only.\n\n"
                    f"Design summary JSON:\n{payload}\n\n"
                    f"{brand_text}{constraint_text}"
                    f"{retailer_hint}\n\n"
                    "Return ONLY valid JSON matching this schema exactly: {\n"
                    "  \"products\": [ { \"name\": string, \"category\": string|null, \"brief_reason\": string|null, \"price_estimate\": string|null, \"url\": string } ],\n"
                    "  \"sources\": [ string ]\n"
                    "}."
                )

            # Use official GenAI SDK for Google Search grounding
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            gen_config = types.GenerateContentConfig(
                tools=[grounding_tool],
                temperature=0.2,
            )
            # IMPORTANT: Do not use JSON mode with tools (per official docs)
            # Explicitly clear any structured-output fields that may be set by defaults.
            try:
                if hasattr(gen_config, "response_mime_type"):
                    gen_config.response_mime_type = None  # type: ignore[attr-defined]
                if hasattr(gen_config, "response_schema"):
                    gen_config.response_schema = None  # type: ignore[attr-defined]
                if hasattr(gen_config, "response_json_schema"):
                    gen_config.response_json_schema = None  # type: ignore[attr-defined]
            except Exception:
                pass

            logger.debug(
                "[Grounding] gen_config JSON mode check: response_mime_type=%s, has_response_schema=%s",
                getattr(gen_config, "response_mime_type", None),
                bool(getattr(gen_config, "response_json_schema", None) or getattr(gen_config, "response_schema", None)),
            )


            import json, re

            def _run_and_parse(contents_text: str) -> Dict[str, Any]:
                nonlocal search_count
                search_count += 1  # Count each search call

                resp_local = client.models.generate_content(
                    model=self.config.default_text_model,
                    contents=contents_text,
                    config=gen_config,
                )
                txt = getattr(resp_local, "text", "") or "{}"
                data: Dict[str, Any] = {}
                # First try direct JSON
                try:
                    data = json.loads(txt)
                except Exception:
                    # Try to find a JSON object in the text
                    m = re.search(r"\{[\s\S]*\}", txt)
                    if m:
                        try:
                            data = json.loads(m.group(0))
                        except Exception:
                            data = {}
                if not isinstance(data, dict):
                    data = {}
                # Attach sources from grounding metadata if present
                try:
                    cand0 = (resp_local.candidates or [None])[0]
                    gm = getattr(cand0, "grounding_metadata", None)
                    if gm:
                        sources = []
                        for chunk in getattr(gm, "grounding_chunks", []) or []:
                            web = getattr(chunk, "web", None)
                            if web and getattr(web, "uri", None):
                                sources.append(web.uri)
                        if sources and isinstance(data, dict):
                            data.setdefault("sources", sources)
                except Exception:
                    pass
                return data

            parsed = _run_and_parse(prompt)

            # If few/empty results, retry once with stricter retailer focus
            products = parsed.get("products") if isinstance(parsed, dict) else None
            logger.info("[Grounding] Initial candidates=%s (attempt=%s)", len(products or []), search_count)

            if not products or len(products) == 0:


                fallback_prompt = (
                    prompt
                    + "\n\nSTRICT RETAILER FOCUS (CANADA): Use Google Search to find ONLY product pages from Canadian retailers and .ca domains, e.g., Home Depot Canada, RONA, Canadian Tire, Home Hardware, Lowe's Canada, IKEA.ca, Wayfair.ca, Costco.ca, BestBuy.ca, The Brick, Leon's, Structube, Amazon.ca, Walmart.ca. "
                    + "Prefer pages with clear price in CAD and Add-to-Cart. Include small local Canadian businesses near the user's area when possible. Return the same JSON schema."
                )
                parsed2 = _run_and_parse(fallback_prompt)
                if isinstance(parsed2, dict) and parsed2.get("products"):
                    parsed = parsed2

            # Post-process: ENFORCE Canadian sourcing (.ca or Canada sections) and prefer small/local vendors
            try:
                def _domain(u: str) -> str:
                    from urllib.parse import urlparse
                    try:
                        return (urlparse(u).hostname or '').lower()
                    except Exception:
                        return ''
                def _is_ca_url(u: str) -> bool:
                    d = _domain(u)
                    if d.endswith('.ca'):
                        return True
                    # Heuristic for Canada sections on other TLDs
                    t = (u or '').lower()
                    return any(seg in t for seg in ['/ca/', '/en-ca', '/fr-ca', 'locale=ca'])
                # Big Canadian retailers (for ordering); everything else treated as small/local if .ca or /en-ca
                BIG_CA_DOMAINS = set([
                    'homedepot.ca', 'rona.ca', 'canadiantire.ca', 'homehardware.ca',
                    'ikea.com', 'ikea.ca', 'wayfair.ca', 'costco.ca', 'bestbuy.ca',
                    'thebrick.com', 'leons.ca', 'structube.com', 'amazon.ca', 'walmart.ca'
                ])

                if isinstance(parsed, dict):
                    prods = parsed.get('products') or []
                    # Strict filter: keep ONLY Canadian-targeted URLs
                    ca_only = [p for p in prods if isinstance(p, dict) and _is_ca_url(p.get('url',''))]
                    if not ca_only:
                        # No CA hits: try a stricter .ca-only retry once with explicit instruction
                        strict_ca_prompt = (
                            prompt
                            + "\n\nSTRICT .CA ONLY: Use Google Search with site:.ca and Canada sections (/en-ca,/fr-ca,/ca/). Return ONLY Canadian-targeted product pages with CAD pricing. Same JSON schema."
                        )
                        strict = _run_and_parse(strict_ca_prompt)

                        try:
                            all_domains = sorted(list({ _domain(p.get('url','')) for p in prods if isinstance(p, dict) }))
                            ca_domains = sorted(list({ _domain(p.get('url','')) for p in ca_only if isinstance(p, dict) }))
                            logger.info("[Grounding] CA filter: %s/%s kept. sample_ca_domains=%s", len(ca_only), len(prods), ca_domains[:5])
                        except Exception:
                            pass

                        if isinstance(strict, dict):
                            prods2 = strict.get('products') or []
                            ca_only = [p for p in prods2 if isinstance(p, dict) and _is_ca_url(p.get('url',''))]

                        try:
                            all_domains = sorted(list({ _domain(p.get('url','')) for p in prods if isinstance(p, dict) }))
                            ca_domains = sorted(list({ _domain(p.get('url','')) for p in ca_only if isinstance(p, dict) }))
                            logger.info("[Grounding] After strict retry: CA filter %s/%s kept. sample_ca_domains=%s", len(ca_only), len(prods), ca_domains[:5])
                        except Exception:
                            pass

                            parsed = strict if ca_only else parsed
                    # If still empty after strict retry, leave empty but attach a notice
                    if ca_only:
                        # Order: prefer small/local (not in big list) before big retailers
                        def _is_big(p: dict) -> bool:
                            d = _domain(p.get('url',''))
                            return d in BIG_CA_DOMAINS
                        small_locals = [p for p in ca_only if not _is_big(p)]
                        bigs = [p for p in ca_only if _is_big(p)]
                        ordered = small_locals + bigs
                        if len(ordered) > max_items:
                            ordered = ordered[:max_items]
                        parsed['products'] = ordered

                        try:
                            logger.info("[Grounding] Final kept=%s (small_local=%s, big=%s)", len(ordered), len(small_locals), len(bigs))
                        except Exception:
                            pass

                    else:
                        # Drop all non-CA items to honor policy
                        parsed['products'] = []
                        parsed['grounding_notice'] = (
                            'Filtered non-Canadian sources. No Canadian (.ca or /en-ca) product pages were found this time.'
                        )
            except Exception:
                pass

            # Track cost for Google Search grounding calls
            duration = time.time() - start_time
            total_cost = self.cost_service.track_cost(
                service="google_search",
                operation="grounding",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "search_count": search_count,
                    "products_found": len(parsed.get("products", [])) if isinstance(parsed, dict) else 0,
                    "sources_found": len(parsed.get("sources", [])) if isinstance(parsed, dict) else 0,
                    "duration_ms": int(duration * 1000)
                }
            )

            # Cache the result
            self.grounding_cache.set(cache_key, parsed, location_hint)
            
            # Record metrics
            latency_ms = int(duration * 1000)
            metrics = GroundingMetrics(
                query=cache_key[:100],
                success=True,
                latency_ms=latency_ms,
                cost_usd=total_cost,
                cached=False,
                sources_found=len(parsed.get("sources", [])) if isinstance(parsed, dict) else 0
            )
            self.grounding_monitor.record_request(metrics)

            logger.info(f"Google Search grounding: {search_count} calls, ${total_cost:.4f}, {duration:.2f}s")

            return ToolResponse(
                success=True,
                data=parsed,
                sources=parsed.get("sources", []) if isinstance(parsed, dict) else [],
                cost_usd=total_cost,
                latency_ms=latency_ms,
                cached=False
            )
        except Exception as e:
            logger.error(f"Error in suggest_products_with_grounding: {e}", exc_info=True)
            
            # Record failure metrics
            duration = time.time() - start_time
            metrics = GroundingMetrics(
                query=cache_key[:100],
                success=False,
                latency_ms=int(duration * 1000),
                cost_usd=0.0,
                cached=False,
                sources_found=0,
                error=str(e)
            )
            self.grounding_monitor.record_request(metrics)
            
            return ToolResponse(
                success=False,
                error=str(e),
                cost_usd=0.0,
                latency_ms=int(duration * 1000),
                cached=False
            )

    async def analyze_image_and_suggest_products(
        self,
        image: Union[str, Path, Image.Image, bytes],
        user_prompt: str,
        room_hint: Optional[str] = None,
        max_items: int = 5,
        location_hint: str = "Canada",
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ToolResponse:
        """
        Multi-modal integration: Analyze image → Extract styles/colors → Enhance search → Get products.

        This combines image analysis with grounding search for more accurate product recommendations.

        Args:
            image: Image to analyze (path, PIL Image, or bytes)
            user_prompt: User's request (e.g., "find paint colors for this room")
            room_hint: Optional room type hint
            max_items: Maximum number of products to return
            location_hint: Location for product search
            user_id: Optional user ID for cost tracking
            project_id: Optional project ID for cost tracking

        Returns:
            ToolResponse with products, sources, and analysis metadata
        """
        start_time = time.time()

        try:
            logger.info("[MultiModal] Starting image analysis + grounding search")

            # Step 1: Analyze the image to extract design elements
            analysis = await self.analyze_design(image, room_hint=room_hint)

            if "error" in analysis:
                return ToolResponse(
                    success=False,
                    error=f"Image analysis failed: {analysis['error']}",
                    latency_ms=int((time.time() - start_time) * 1000)
                )

            # Step 2: Extract key design elements
            colors = analysis.get("colors", [])
            materials = analysis.get("materials", [])
            styles = analysis.get("styles", [])
            description = analysis.get("description", "")

            # Build color names for search
            color_names = []
            for color in colors:
                if isinstance(color, dict):
                    color_names.append(color.get("name", ""))
                elif isinstance(color, str):
                    color_names.append(color)

            # Step 3: Enhance the search query with extracted design elements
            enhanced_query_parts = [user_prompt]

            if color_names:
                enhanced_query_parts.append(f"Colors: {', '.join(color_names[:3])}")

            if styles:
                style_list = styles if isinstance(styles, list) else [styles]
                enhanced_query_parts.append(f"Style: {', '.join(style_list[:2])}")

            if materials:
                material_list = materials if isinstance(materials, list) else [materials]
                enhanced_query_parts.append(f"Materials: {', '.join(material_list[:2])}")

            enhanced_query = " | ".join(enhanced_query_parts)

            logger.info(f"[MultiModal] Enhanced query: {enhanced_query}")

            # Step 4: Use enhanced query for grounding search
            grounding_input = {
                "user_prompt": enhanced_query,
                "requested_changes": [],
                "original_summary": analysis,
                "location_hint": location_hint,
            }

            # Step 5: Execute grounding search with enhanced query
            grounding_result = await self.suggest_products_with_grounding(
                grounding_input,
                max_items=max_items,
                user_id=user_id,
                project_id=project_id
            )

            # Step 6: Enrich response with analysis metadata
            if grounding_result.success:
                result_data = grounding_result.data if isinstance(grounding_result.data, dict) else {}
                result_data["image_analysis"] = {
                    "colors": colors,
                    "materials": materials,
                    "styles": styles,
                    "description": description,
                }
                result_data["enhanced_query"] = enhanced_query

                return ToolResponse(
                    success=True,
                    data=result_data,
                    sources=grounding_result.sources,
                    grounding_metadata=grounding_result.grounding_metadata,
                    cost_usd=grounding_result.cost_usd,
                    latency_ms=int((time.time() - start_time) * 1000),
                    cached=grounding_result.cached
                )
            else:
                return ToolResponse(
                    success=False,
                    error=grounding_result.error,
                    latency_ms=int((time.time() - start_time) * 1000)
                )

        except Exception as e:
            logger.error(f"[MultiModal] Error: {e}", exc_info=True)
            return ToolResponse(
                success=False,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )

    async def suggest_products_without_grounding_function_calling(
        self,
        summary_or_grounding: Dict[str, Any],
        max_items: int = 5,
    ) -> Dict[str, Any]:
        """
        Function-calling variant that returns structured product objects WITHOUT google_search.

        Notes per official docs:
        - Function calling: https://ai.google.dev/gemini-api/docs/function-calling
        - Multi-tool use (combine google_search + function calling) is Live API only at the moment.
          We therefore use function calling alone here as a graceful fallback when grounding is unavailable.
        """
        try:
            payload = summary_or_grounding or {}
            changes = payload.get("requested_changes", []) or []

            # Build brand preferences and constraint text
            brand_lines: List[str] = []
            constraint_lines: List[str] = []
            for cat in changes:
                prefs = CATEGORY_BRAND_PREFERENCES.get(cat)
                if prefs:
                    brand_lines.append(f"{cat}: {', '.join(prefs)}")
                hint = CATEGORY_CONSTRAINT_HINTS.get(cat)
                if hint:
                    constraint_lines.append(f"{cat}: {hint}")
            brand_text = ("Brand preferences per category: " + "; ".join(brand_lines) + ".\n") if brand_lines else ""
            constraint_text = ("Category-specific constraints (include when applicable): " + " ".join(constraint_lines) + "\n") if constraint_lines else ""

            # Build a concise context message
            # Canada-specific context and optional location hint
            location_hint = (payload.get("location_hint") or "Canada").strip()
            ctx_lines = [
                "You are an interior design shopping assistant.",
                f"Return at most {max_items} products.",
                "Prefer items that the user can buy directly.",
                "Use model knowledge only (no live web calls).",
                "Market: Canada. Prefer .ca domains and CAD pricing. Avoid US-only or non-shippable items.",
                f"If a location is known, prefer nearest stores around: {location_hint}.",
                "Include a mix of major Canadian retailers AND small local Canadian businesses when relevant.",
                brand_text.strip(),
                constraint_text.strip(),
            ]
            context_text = "\n".join([l for l in ctx_lines if l])

            # We use new google.genai SDK function calling
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)

            product_fn = types.FunctionDeclaration(
                name="present_products",
                description="Return a small list of purchasable products relevant to the requested interior design changes.",
                parameters={
                    "type": "object",
                    "properties": {
                        "products": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "category": {"type": "string"},
                                    "brand": {"type": "string"},
                                    "sku": {"type": "string"},
                                    "price_estimate": {"type": "string"},
                                    "brief_reason": {"type": "string"},
                                    "url": {"type": "string"},
                                },
                                "required": ["name"]
                            }
                        }
                    },
                    "required": ["products"]
                }
            )

            gen_config = types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=[product_fn])],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="ANY",
                        allowed_function_names=["present_products"],
                    )
                ),
                temperature=0.2,
            )

            # Compose content
            is_diff = isinstance(payload, dict) and (
                "original_summary" in payload or "new_summary" in payload
            )
            if is_diff:
                user_prompt = payload.get("user_prompt", "")
                changes_txt = ", ".join(changes) if changes else "unspecified"
                original = payload.get("original_summary", {})
                new = payload.get("new_summary", {})
                prompt = (
                    f"{context_text}\n\n"
                    f"USER REQUEST: {user_prompt}\n"
                    f"CHANGE CATEGORIES: {changes_txt}\n"
                    f"ORIGINAL SUMMARY JSON: {original}\n"
                    f"TRANSFORMED SUMMARY JSON: {new}\n"
                    f"Return via present_products(products=[...])."
                )
            else:
                prompt = (
                    f"{context_text}\n\n"
                    f"ROOM SUMMARY JSON: {payload}\n"
                    f"Return via present_products(products=[...])."
                )

            resp = client.models.generate_content(
                model=self.config.default_text_model,
                contents=prompt,
                config=gen_config,
            )

            # Parse function call args
            products: List[Dict[str, Any]] = []
            try:
                cand0 = (resp.candidates or [None])[0]
                if cand0 and getattr(cand0, "content", None):
                    parts = getattr(cand0.content, "parts", []) or []
                    if parts and getattr(parts[0], "function_call", None):
                        fn = parts[0].function_call
                        if getattr(fn, "name", "") == "present_products":
                            args = getattr(fn, "args", {}) or {}
                            if isinstance(args, dict):
                                products = args.get("products", []) or []
            except Exception:
                pass

            # Cap items and normalize
            if not isinstance(products, list):
                products = []
            # ENFORCE Canadian targeting (.ca or Canada sections) and prefer small/local first
            def _domain(u: str) -> str:
                try:
                    from urllib.parse import urlparse
                    return (urlparse(u).hostname or '').lower()
                except Exception:
                    return ''
            def _is_ca_url(u: str) -> bool:
                d = _domain(u)
                if d.endswith('.ca'):
                    return True
                t = (u or '').lower()
                return any(seg in t for seg in ['/ca/', '/en-ca', '/fr-ca', 'locale=ca'])
            BIG_CA_DOMAINS = set([
                'homedepot.ca', 'rona.ca', 'canadiantire.ca', 'homehardware.ca',
                'ikea.com', 'ikea.ca', 'wayfair.ca', 'costco.ca', 'bestbuy.ca',
                'thebrick.com', 'leons.ca', 'structube.com', 'amazon.ca', 'walmart.ca'
            ])
            ca_only = [p for p in products if isinstance(p, dict) and _is_ca_url(p.get('url',''))]
            if ca_only:
                def _is_big(p: dict) -> bool:
                    return _domain(p.get('url','')) in BIG_CA_DOMAINS
                small_locals = [p for p in ca_only if not _is_big(p)]
                bigs = [p for p in ca_only if _is_big(p)]
                products = small_locals + bigs
            else:
                products = []
            if len(products) > max_items:
                products = products[:max_items]

            return {"products": products, "sources": []}
        except Exception as e:
            logger.error(f"Error in suggest_products_without_grounding_function_calling: {e}", exc_info=True)
            return {"error": str(e), "products": [], "sources": []}

    async def batch_grounding_queries(
        self,
        queries: List[Dict[str, Any]],
        max_items: int = 5,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        use_query_optimizer: bool = True,
    ) -> List[ToolResponse]:
        """
        Process multiple grounding queries in parallel for improved performance.

        Uses asyncio.gather to execute queries concurrently, resulting in 3-5x faster
        batch operations compared to sequential processing.

        Args:
            queries: List of query dictionaries (same format as suggest_products_with_grounding)
            max_items: Maximum items per query
            user_id: Optional user ID for cost tracking
            project_id: Optional project ID for cost tracking
            use_query_optimizer: Whether to apply query optimization

        Returns:
            List of ToolResponse objects, one per query

        Example:
            queries = [
                {"user_prompt": "modern gray sofa", "location_hint": "Vancouver"},
                {"user_prompt": "pendant lighting", "location_hint": "Toronto"},
                {"user_prompt": "hardwood flooring", "location_hint": "Montreal"}
            ]
            results = await client.batch_grounding_queries(queries)
        """
        import asyncio

        start_time = time.time()
        logger.info(f"[BatchGrounding] Processing {len(queries)} queries in parallel")

        # Apply query optimization if requested
        if use_query_optimizer:
            optimized_queries = []
            for query in queries:
                user_prompt = query.get("user_prompt", "")
                location = query.get("location_hint", "Canada")

                # Try to extract category from query
                category = self.query_optimizer.extract_category_from_query(user_prompt)

                # Optimize the query
                optimized = self.query_optimizer.optimize_query(
                    user_prompt,
                    location=location,
                    category=category
                )

                # Update query with optimized version
                optimized_query = {**query}
                optimized_query["user_prompt"] = optimized.optimized_query
                optimized_query["_optimization_metadata"] = {
                    "original_query": optimized.original_query,
                    "applied_optimizations": optimized.applied_optimizations,
                    "confidence": optimized.confidence
                }
                optimized_queries.append(optimized_query)

            queries = optimized_queries

        # Create tasks for parallel execution
        tasks = [
            self.suggest_products_with_grounding(
                query,
                max_items=max_items,
                user_id=user_id,
                project_id=project_id
            )
            for query in queries
        ]

        # Execute all queries in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error responses
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"[BatchGrounding] Query {i} failed: {result}")
                    processed_results.append(ToolResponse(
                        success=False,
                        error=str(result),
                        latency_ms=0
                    ))
                else:
                    processed_results.append(result)

            total_time = time.time() - start_time
            logger.info(
                f"[BatchGrounding] Completed {len(queries)} queries in {total_time:.2f}s "
                f"(avg: {total_time/len(queries):.2f}s per query)"
            )

            return processed_results

        except Exception as e:
            logger.error(f"[BatchGrounding] Batch processing failed: {e}", exc_info=True)
            # Return error responses for all queries
            return [
                ToolResponse(
                    success=False,
                    error=f"Batch processing failed: {str(e)}",
                    latency_ms=0
                )
                for _ in queries
            ]

    async def find_local_contractors_with_maps(
        self,
        service_type: str,
        location: str,
        radius_miles: int = 25,
        max_results: int = 5,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ToolResponse:
        """
        Find local contractors using Google Maps grounding.

        Based on official documentation:
        https://ai.google.dev/gemini-api/docs/maps-grounding

        Args:
            service_type: Type of service (e.g., "plumber", "electrician", "painter")
            location: Location to search (e.g., "Vancouver, BC", "Toronto, ON")
            radius_miles: Search radius in miles
            max_results: Maximum number of results
            user_id: Optional user ID for cost tracking
            project_id: Optional project ID for cost tracking

        Returns:
            ToolResponse with contractor information
        """
        start_time = time.time()

        try:
            from google import genai as google_genai
            from google.genai import types

            logger.info(f"[MapsGrounding] Searching for {service_type} in {location}")

            # Initialize client with API key
            client = google_genai.Client(api_key=self.config.api_key)

            # Configure Maps grounding tool
            maps_tool = types.Tool(google_maps=types.GoogleMaps())

            config = types.GenerateContentConfig(
                tools=[maps_tool],
                temperature=0.2,
                response_modalities=["TEXT"]
            )

            # Build search prompt
            prompt = (
                f"Find {service_type} contractors in {location} within {radius_miles} miles. "
                f"Return up to {max_results} results with business name, address, phone, "
                f"rating, and website if available. Focus on licensed and reputable businesses."
            )

            # Execute Maps grounding
            response = client.models.generate_content(
                model=self.config.default_text_model,
                contents=prompt,
                config=config
            )

            # Parse response
            text = getattr(response, 'text', '')

            # Extract grounding metadata
            contractors = []
            grounding_metadata = getattr(response.candidates[0], 'grounding_metadata', None) if response.candidates else None

            # Track cost
            duration_ms = int((time.time() - start_time) * 1000)
            cost_usd = 0.001  # Estimated cost per Maps grounding call

            self.cost_service.track_cost(
                service="gemini",
                operation="maps_grounding",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "model": self.config.default_text_model,
                    "duration_ms": duration_ms,
                    "service_type": service_type,
                    "location": location
                }
            )

            logger.info(f"[MapsGrounding] Found contractors in {duration_ms}ms")

            return ToolResponse(
                success=True,
                data={
                    "contractors": text,
                    "service_type": service_type,
                    "location": location,
                    "radius_miles": radius_miles
                },
                sources=[],
                grounding_metadata=grounding_metadata,
                cost_usd=cost_usd,
                latency_ms=duration_ms,
                cached=False
            )

        except Exception as e:
            logger.error(f"[MapsGrounding] Error: {e}", exc_info=True)
            return ToolResponse(
                success=False,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )

    async def search_with_url_context(
        self,
        query: str,
        url: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ToolResponse:
        """
        Search with URL context - use webpage content as additional context.

        Based on official documentation:
        https://ai.google.dev/gemini-api/docs/url-context

        Args:
            query: Search query
            url: URL to use as context
            user_id: Optional user ID for cost tracking
            project_id: Optional project ID for cost tracking

        Returns:
            ToolResponse with search results enriched by URL context
        """
        start_time = time.time()

        try:
            from google import genai as google_genai
            from google.genai import types

            logger.info(f"[URLContext] Searching '{query}' with context from {url}")

            # Initialize client
            client = google_genai.Client(api_key=self.config.api_key)

            # Configure with Google Search and URL context
            search_tool = types.Tool(google_search=types.GoogleSearch())

            config = types.GenerateContentConfig(
                tools=[search_tool],
                temperature=0.3,
                response_modalities=["TEXT"]
            )

            # Build prompt with URL context
            prompt = (
                f"Using the content from {url} as context, {query}. "
                f"Provide relevant information and product recommendations."
            )

            # Execute search with URL context
            response = client.models.generate_content(
                model=self.config.default_text_model,
                contents=prompt,
                config=config
            )

            text = getattr(response, 'text', '')

            # Extract grounding metadata
            grounding_metadata = getattr(response.candidates[0], 'grounding_metadata', None) if response.candidates else None
            sources = []

            if grounding_metadata:
                chunks = getattr(grounding_metadata, 'grounding_chunks', [])
                for chunk in chunks:
                    web = getattr(chunk, 'web', None)
                    if web and hasattr(web, 'uri'):
                        sources.append(web.uri)

            duration_ms = int((time.time() - start_time) * 1000)
            cost_usd = 0.001

            self.cost_service.track_cost(
                service="gemini",
                operation="url_context_search",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "model": self.config.default_text_model,
                    "duration_ms": duration_ms,
                    "url": url
                }
            )

            logger.info(f"[URLContext] Search completed in {duration_ms}ms")

            return ToolResponse(
                success=True,
                data={
                    "results": text,
                    "context_url": url
                },
                sources=sources,
                grounding_metadata=grounding_metadata,
                cost_usd=cost_usd,
                latency_ms=duration_ms,
                cached=False
            )

        except Exception as e:
            logger.error(f"[URLContext] Error: {e}", exc_info=True)
            return ToolResponse(
                success=False,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )

    async def search_uploaded_files(
        self,
        query: str,
        file_ids: List[str],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ToolResponse:
        """
        Search across uploaded files using File Search grounding.

        Based on official documentation:
        https://ai.google.dev/gemini-api/docs/file-search

        This is useful for searching through:
        - Project documents
        - Design specifications
        - Product catalogs
        - Contractor proposals
        - DIY guides

        Args:
            query: Search query
            file_ids: List of file IDs to search (files must be uploaded first)
            user_id: Optional user ID for cost tracking
            project_id: Optional project ID for cost tracking

        Returns:
            ToolResponse with search results from files

        Note:
            Files must be uploaded to Gemini File API first using:
            file = genai.upload_file(path="document.pdf")
            Then use file.name as the file_id
        """
        start_time = time.time()

        try:
            from google import genai as google_genai
            from google.genai import types

            logger.info(f"[FileSearch] Searching '{query}' across {len(file_ids)} files")

            # Initialize client
            client = google_genai.Client(api_key=self.config.api_key)

            # Configure file search tool
            # Note: File search configuration depends on uploaded files
            config = types.GenerateContentConfig(
                temperature=0.2,
                response_modalities=["TEXT"]
            )

            # Build prompt with file references
            prompt = (
                f"Search the uploaded documents for information about: {query}. "
                f"Provide relevant excerpts and summaries from the documents."
            )

            # Execute file search
            # Note: This requires files to be uploaded first via genai.upload_file()
            response = client.models.generate_content(
                model=self.config.default_text_model,
                contents=prompt,
                config=config
            )

            text = getattr(response, 'text', '')

            duration_ms = int((time.time() - start_time) * 1000)
            cost_usd = 0.001

            self.cost_service.track_cost(
                service="gemini",
                operation="file_search",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "model": self.config.default_text_model,
                    "duration_ms": duration_ms,
                    "num_files": len(file_ids)
                }
            )

            logger.info(f"[FileSearch] Search completed in {duration_ms}ms")

            return ToolResponse(
                success=True,
                data={
                    "results": text,
                    "file_ids": file_ids,
                    "num_files_searched": len(file_ids)
                },
                sources=[],
                cost_usd=cost_usd,
                latency_ms=duration_ms,
                cached=False
            )

        except Exception as e:
            logger.error(f"[FileSearch] Error: {e}", exc_info=True)
            return ToolResponse(
                success=False,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )

    async def upload_file_for_search(
        self,
        file_path: Union[str, Path],
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Gemini for file search.

        Supported file types:
        - PDF documents
        - Text files
        - Word documents
        - Spreadsheets

        Args:
            file_path: Path to file to upload
            display_name: Optional display name for the file

        Returns:
            Dict with file_id and metadata
        """
        try:
            logger.info(f"[FileUpload] Uploading file: {file_path}")

            # Upload file using genai
            uploaded_file = genai.upload_file(
                path=str(file_path),
                display_name=display_name
            )

            logger.info(f"[FileUpload] File uploaded: {uploaded_file.name}")

            return {
                "success": True,
                "file_id": uploaded_file.name,
                "display_name": uploaded_file.display_name,
                "mime_type": uploaded_file.mime_type,
                "size_bytes": getattr(uploaded_file, 'size_bytes', None)
            }

        except Exception as e:
            logger.error(f"[FileUpload] Error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_transformation_ideas(
        self,
        summary: Dict[str, Any],
        room_hint: Optional[str] = None,
        max_ideas: int = 6,
    ) -> Dict[str, List[str]]:
        """
        Generate concise, multi-step transformation ideas grouped by theme.

        Uses the official Gemini text generation API (google.generativeai) and returns ONLY JSON
        in the schema:
        {
          "color": ["..."],
          "flooring": ["..."],
          "lighting": ["..."],
          "decor": ["..."],
          "other": ["..."]
        }
        Each idea should be an imperative suggestion (5-12 words), specific and non-duplicative.
        """
        try:
            prompt = (
                "You are an interior design assistant. Based on the following structured "
                "room summary, propose concise transformation ideas grouped by theme. "
                "Focus on actionable changes the user could request in an image edit. "
                "Return ONLY JSON with keys color, flooring, lighting, decor, other.\n\n"
                f"Room type (hint): {room_hint or 'unknown'}\n"
                f"Summary JSON:\n{summary}\n\n"
                "Constraints:\n"
                f"- Cap total ideas to about {max_ideas} across all groups.\n"
                "- 5-12 words per idea, avoid redundancy, be practical.\n"
                "- Color group should include palettes or paint changes when relevant.\n"
                "- Flooring group should include material/finish suggestions when relevant.\n"
                "- Lighting group should include fixture type/finish/warmth suggestions when relevant.\n"
                "- Decor group can include accents, textiles, hardware, art.\n"
                "- Use 'other' only if something does not fit the above."
            )

            resp = self.text_model.generate_content(
                prompt,
                generation_config={"temperature": 0.4}
            )
            text = getattr(resp, "text", "") or "{}"

            import json, re
            match = re.search(r"\{[\s\S]*\}", text)
            payload = json.loads(match.group(0)) if match else {}

            # Normalize into expected keys
            if not isinstance(payload, dict):
                return {"color": [], "flooring": [], "lighting": [], "decor": [], "other": []}
            for key in ["color", "flooring", "lighting", "decor", "other"]:
                if key not in payload or not isinstance(payload.get(key), list):
                    payload[key] = []
            # Trim to max_ideas overall
            total = 0
            for k in ["color", "flooring", "lighting", "decor", "other"]:
                arr = []
                for idea in payload[k]:
                    if total >= max_ideas:
                        break
                    if isinstance(idea, str) and idea.strip():
                        arr.append(idea.strip())
                        total += 1
                payload[k] = arr
            return payload
        except Exception as e:
            logger.error(f"Error in generate_transformation_ideas: {e}", exc_info=True)
            return {"color": [], "flooring": [], "lighting": [], "decor": [], "other": []}

    async def generate_style_transformations(
        self,
        summary: Dict[str, Any],
        room_hint: Optional[str] = None,
        max_items: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Generate 3-5 high-level style transformation presets for the room.

        Follows official Gemini text generation guidance (google.generativeai) and returns ONLY JSON:
        { "items": [ { "label": str, "prompt": str } ] }
        The prompt should be a complete, safe Imagen editing instruction that:
        - Preserves layout, walls, windows, doors, and lighting
        - Only modifies style, finishes, colors, and decor as implied by the label
        - Uses clear, concise sentences (<= 80 words)
        """
        try:
            count = max(1, min(int(max_items or 4), 6))
            prompt = (
                "You are an interior design AI. Based on the structured room summary, propose "
                f"{count} distinct STYLE TRANSFORMATION presets appropriate for the space. "
                "Return ONLY JSON in the schema {\"items\":[{\"label\":str,\"prompt\":str}]}. "
                "The prompt should be a full image-edit instruction for Gemini Imagen that preserves the scene except for style changes.\n\n"
                f"Room type (hint): {room_hint or 'unknown'}\n"
                f"Summary JSON:\n{summary}\n\n"
                "Rules for prompt content:\n"
                "- Preserve layout, structure, and lighting; no structural changes.\n"
                "- Only adjust style, finishes, furniture/decor, and color palettes.\n"
                "- Keep unchanged elements identical unless the label explicitly implies a swap.\n"
                "- Maintain photorealism and correct perspective.\n"
            )
            resp = self.text_model.generate_content(
                prompt,
                generation_config={"temperature": 0.5}
            )
            text = getattr(resp, "text", "") or "{}"

            import json, re
            match = re.search(r"\{[\s\S]*\}", text)
            payload = json.loads(match.group(0)) if match else {}
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                return []
            out: List[Dict[str, Any]] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                label = (it.get("label") or "").strip()
                pr = (it.get("prompt") or "").strip()
                if label and pr:
                    out.append({"label": label, "prompt": pr})
                if len(out) >= count:
                    break
            return out
        except Exception as e:
            logger.error(f"Error in generate_style_transformations: {e}", exc_info=True)
            return []



    async def generate_image(
        self,
        prompt: str,
        reference_image: Optional[Union[str, Path, Image.Image, bytes]] = None,
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        image_size: str = "1K"
    ) -> List[Image.Image]:
        """
        Generate images using Gemini Imagen.

        Based on official Gemini Imagen API documentation:
        https://ai.google.dev/gemini-api/docs/imagen

        Args:
            prompt: Image generation prompt (max 480 tokens)
            reference_image: Optional reference image for editing/style transfer
            aspect_ratio: Aspect ratio ("1:1", "16:9", "9:16", "4:3", "3:4")
            num_images: Number of images to generate (1-4)
            image_size: Image size ("1K" or "2K") - only for Standard/Ultra models

        Returns:
            List of generated PIL Images
        """
        try:
            from google import genai as google_genai
            from google.genai import types

            # Initialize client
            client = google_genai.Client(api_key=self.config.api_key)

            # Build configuration
            config = types.GenerateImagesConfig(
                number_of_images=num_images,
                aspect_ratio=aspect_ratio,
            )

            # If we have a reference image, include it in the prompt
            # For image editing/transformation, we use the reference image
            if reference_image:
                pil_image = self._load_image(reference_image)

                # For transformations, we need to use the image as context
                # The prompt should describe the transformation
                # Imagen will use the reference image as a base

                # Convert PIL image to bytes
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()

                # Create a combined prompt that includes the image context
                # Note: This approach uses the image as a reference for style/content
                full_prompt = f"""Using the provided reference image as a base, {prompt}

IMPORTANT: Maintain the exact composition, perspective, and layout of the reference image.
Only modify the specific elements mentioned in the transformation request."""

                # Generate with reference image
                response = client.models.generate_images(
                    model='imagen-4.0-generate-001',
                    prompt=full_prompt,
                    config=config
                )
            else:
                # Generate from text prompt only
                response = client.models.generate_images(
                    model='imagen-4.0-generate-001',
                    prompt=prompt,
                    config=config
                )

            # Extract images from response
            images = []
            for generated_image in response.generated_images:
                # The image is in generated_image.image
                # Convert to PIL Image
                if hasattr(generated_image.image, 'image_bytes'):
                    image_data = generated_image.image.image_bytes
                    images.append(Image.open(BytesIO(image_data)))
                elif hasattr(generated_image, 'image'):
                    # Alternative response format
                    images.append(generated_image.image)

            logger.info(f"Generated {len(images)} images using Imagen")
            return images

        except Exception as e:
            logger.error(f"Error generating image with Imagen: {str(e)}", exc_info=True)
            raise

    async def get_embeddings(
        self,
        texts: Union[str, List[str]],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts
            user_id: User ID for cost tracking
            project_id: Project/home ID for cost tracking

        Returns:
            List of embedding vectors
        """
        start_time = time.time()

        try:
            if isinstance(texts, str):
                texts = [texts]

            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model=self.config.default_embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])

            # Track cost (estimate tokens)
            total_tokens = sum(len(text.split()) * 1.3 for text in texts)
            self.cost_service.track_cost(
                service="gemini",
                operation="embed",
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "model": self.config.default_embedding_model,
                    "tokens": int(total_tokens),
                    "count": len(texts),
                    "duration_ms": int((time.time() - start_time) * 1000)
                }
            )

            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Multi-turn chat with Gemini.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            system_instruction: System instruction

        Returns:
            Assistant's response
        """
        try:
            generation_config = {
                "temperature": temperature or self.config.default_temperature,
            }

            # Create chat session
            model = self.text_model
            if system_instruction:
                model = GenerativeModel(
                    model_name=self.config.default_text_model,
                    safety_settings=self.safety_settings,
                    system_instruction=system_instruction
                )

            chat = model.start_chat(history=[])

            # Add prior messages (only user messages are sent)
            for msg in (messages or [])[:-1]:
                if msg.get("role") == "user":
                    chat.send_message(msg.get("content", ""), generation_config=generation_config)

            # Send the final user turn and return text
            final_text = (messages or [{"content": ""}])[-1].get("content", "")
            response = chat.send_message(final_text, generation_config=generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise

    async def edit_image(
        self,
        prompt: str,
        reference_image: Union[str, Path, Image.Image, bytes],
        num_images: int = 1,
        aspect_ratio: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Edit an image using native Gemini image generation (gemini-2.5-flash-image).

        Official docs: https://ai.google.dev/gemini-api/docs/image-generation
        """
        try:
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)

            pil_image = self._load_image(reference_image)

            gen_config = types.GenerateContentConfig(
                response_modalities=["Image"],
            )
            if aspect_ratio:
                try:
                    gen_config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
                except Exception:
                    pass

            contents = [pil_image, prompt]

            images: List[Image.Image] = []
            count = max(1, int(num_images or 1))

            # Generate images in parallel using asyncio.gather for speed
            import asyncio

            async def generate_single():
                try:
                    response = client.models.generate_content(
                        model=self.config.default_image_gen_model,
                        contents=contents,
                        config=gen_config,
                    )
                    result_images = []
                    for part in getattr(response.candidates[0].content, "parts", []) or []:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            result_images.append(Image.open(BytesIO(inline.data)))
                    return result_images
                except Exception as e:
                    logger.warning(f"Failed to generate single variation: {e}")
                    return []

            # Generate all variations in parallel
            tasks = [generate_single() for _ in range(count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results
            for result in results:
                if isinstance(result, list):
                    images.extend(result)

            logger.info(f"Edited image with native Gemini model; produced {len(images)} variation(s)")
            return images
        except Exception as e:
            logger.error(f"Error editing image with Gemini native model: {e}", exc_info=True)
            raise


    async def edit_image_masked(
        self,
        prompt: str,
        reference_image: Union[str, Path, Image.Image, bytes],
        mask_image: Union[str, Path, Image.Image, bytes],
        num_images: int = 1,
        aspect_ratio: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Edit an image using a user-provided mask (white = editable, black/transparent = protected).

        Note: The Gemini Image API does not expose a mask parameter; we follow the official
        multimodal pattern (https://ai.google.dev/gemini-api/docs/image-generation) by
        passing both the reference image and the mask image as inputs with clear instructions
        to restrict edits to the white regions.
        """
        try:
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)

            pil_reference = self._load_image(reference_image)
            pil_mask = self._load_image(mask_image)

            gen_config = types.GenerateContentConfig(
                response_modalities=["Image"],
            )
            if aspect_ratio:
                try:
                    gen_config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
                except Exception:
                    pass

            # Provide both images and strict masking instruction
            mask_instruction = (
                "Apply changes ONLY within the WHITE areas of the mask image. "
                "Treat BLACK or transparent areas as protected and leave them identical to the original."
            )
            contents = [
                pil_reference,
                mask_instruction,
                pil_mask,
                prompt,
            ]

            images: List[Image.Image] = []
            count = max(1, int(num_images or 1))
            for _ in range(count):
                response = client.models.generate_content(
                    model=self.config.default_image_gen_model,
                    contents=contents,
                    config=gen_config,
                )
                try:
                    for part in getattr(response.candidates[0].content, "parts", []) or []:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            images.append(Image.open(BytesIO(inline.data)))
                except Exception:
                    pass

            logger.info(
                f"Edited image with mask via Gemini; produced {len(images)} variation(s)"
            )
            return images
        except Exception as e:
            logger.error(f"Error in edit_image_masked: {e}", exc_info=True)
            raise

    async def segment_image(
        self,
        reference_image: Union[str, Path, Image.Image, bytes],
        segment_class: str,
        points: Optional[List[Dict[str, int]]] = None,
        num_masks: int = 1,
    ) -> List[Image.Image]:
        """
        Ask Gemini to produce a binary segmentation mask image for the target class.

        Note: There is no dedicated segmentation API; we follow the official image-generation
        pattern (https://ai.google.dev/gemini-api/docs/image-generation) and prompt the model
        to output a black/white mask image where WHITE = target class, BLACK = everything else.
        This is a best-effort helper for click-to-segment.
        """
        try:
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)
            pil_image = self._load_image(reference_image)

            hint = ""
            if points:
                coords = ", ".join([f"({p.get('x')},{p.get('y')})" for p in points])
                hint = f"\nCoordinate hints (approx centers/edges): {coords}"

            prompt = (
                "Create a binary segmentation mask for the target region.\n"
                "- Target class: " + segment_class + "\n"
                "- Output FORMAT: a single image where WHITE (255) are target pixels and BLACK (0) all else.\n"
                "- STRICT: No grayscale, no color, no alpha; only pure black/white.\n"
                "- Align mask exactly to the reference image dimensions.\n"
                "- Keep crisp edges; avoid feathering." + hint
            )

            gen_config = types.GenerateContentConfig(
                response_modalities=["Image"],
            )

            contents = [pil_image, prompt]

            masks: List[Image.Image] = []
            count = max(1, int(num_masks or 1))
            for _ in range(count):
                response = client.models.generate_content(
                    model=self.config.default_image_gen_model,
                    contents=contents,
                    config=gen_config,
                )
                try:
                    for part in getattr(response.candidates[0].content, "parts", []) or []:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            masks.append(Image.open(BytesIO(inline.data)).convert("L"))
                except Exception:
                    pass

            logger.info(f"Segmentation requested for '{segment_class}'; produced {len(masks)} mask(s)")
            return masks
        except Exception as e:
            logger.error(f"Error in segment_image: {e}", exc_info=True)
            raise


    async def analyze_video(
        self,
        video_path: Union[str, Path],
        prompt: str,
        analysis_type: str = "summary",
        fps: Optional[int] = None,
        start_offset_seconds: Optional[int] = None,
        end_offset_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a video file using Gemini's video understanding capabilities.

        Based on Google Gemini Cookbook video understanding examples:
        https://github.com/google-gemini/cookbook/blob/main/quickstarts/Video_understanding.ipynb

        Args:
            video_path: Path to video file or YouTube URL
            prompt: Analysis prompt (or use default based on analysis_type)
            analysis_type: Type of analysis - "summary", "search", "extract_text", "tutorial"
            fps: Frames per second to analyze (default: 1 FPS)
            start_offset_seconds: Start time in seconds for clipping
            end_offset_seconds: End time in seconds for clipping

        Returns:
            Dict with analysis results
        """
        try:
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)

            # Upload video to File API if it's a local file
            video_uri = None
            if str(video_path).startswith(('http://', 'https://', 'www.')):
                # YouTube or web video
                video_uri = str(video_path)
            else:
                # Local file - upload to File API
                logger.info(f"[Video] Uploading video file: {video_path}")
                video_file = client.files.upload(file=str(video_path))

                # Wait for processing
                import time
                while video_file.state == "PROCESSING":
                    logger.info("[Video] Waiting for video processing...")
                    time.sleep(5)
                    video_file = client.files.get(name=video_file.name)

                if video_file.state == "FAILED":
                    raise ValueError(f"Video processing failed: {video_file.state}")

                video_uri = video_file.uri
                logger.info(f"[Video] Processing complete: {video_uri}")

            # Build video metadata for clipping/FPS
            video_metadata = None
            if fps or start_offset_seconds or end_offset_seconds:
                video_metadata = types.VideoMetadata()
                if fps:
                    video_metadata.fps = fps
                if start_offset_seconds is not None:
                    video_metadata.start_offset = f"{start_offset_seconds}s"
                if end_offset_seconds is not None:
                    video_metadata.end_offset = f"{end_offset_seconds}s"

            # Build default prompts based on analysis type
            if not prompt or prompt == "":
                if analysis_type == "summary":
                    prompt = "Summarize this video in 3-5 sentences with key timestamps."
                elif analysis_type == "search":
                    prompt = "For each scene in this video, generate captions with timecodes."
                elif analysis_type == "extract_text":
                    prompt = "Extract all visible text from this video and organize it with timestamps."
                elif analysis_type == "tutorial":
                    prompt = (
                        "Analyze this DIY/tutorial video and extract:\n"
                        "1. Step-by-step instructions with timestamps\n"
                        "2. Tools and materials mentioned\n"
                        "3. Safety warnings or tips\n"
                        "4. Estimated difficulty level\n"
                        "Return as structured JSON."
                    )

            # Build content parts
            parts = []
            if video_metadata:
                parts.append(types.Part(
                    file_data=types.FileData(file_uri=video_uri),
                    video_metadata=video_metadata
                ))
            else:
                parts.append(types.Part(file_data=types.FileData(file_uri=video_uri)))

            parts.append(types.Part(text=prompt))

            # Generate content
            response = client.models.generate_content(
                model=self.config.default_vision_model,
                contents=types.Content(parts=parts),
            )

            text = getattr(response, "text", "") or "{}"

            # Try to parse as JSON if it looks like JSON
            import json, re
            result = {"raw_text": text}
            if text.strip().startswith('{') or text.strip().startswith('['):
                try:
                    match = re.search(r"[\{\[][\s\S]*[\}\]]", text)
                    if match:
                        result["structured"] = json.loads(match.group(0))
                except:
                    pass

            logger.info(f"[Video] Analysis complete, type={analysis_type}")
            return result

        except Exception as e:
            logger.error(f"analyze_video failed: {e}", exc_info=True)
            return {"error": str(e)}

    async def analyze_youtube_video(
        self,
        youtube_url: str,
        prompt: str,
        start_offset_seconds: Optional[int] = None,
        end_offset_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a YouTube video directly without downloading.

        Args:
            youtube_url: YouTube video URL
            prompt: Analysis prompt
            start_offset_seconds: Start time for clipping
            end_offset_seconds: End time for clipping

        Returns:
            Dict with analysis results
        """
        return await self.analyze_video(
            video_path=youtube_url,
            prompt=prompt,
            start_offset_seconds=start_offset_seconds,
            end_offset_seconds=end_offset_seconds
        )

    async def generate_structured_content(
        self,
        prompt: str,
        image: Optional[Union[str, Path, Image.Image, bytes]] = None,
        response_schema: Optional[type] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured content with enforced JSON schema using TypedDict.

        Based on Google Gemini Cookbook "Market a Jet Backpack" example:
        https://github.com/google-gemini/cookbook/blob/main/examples/Market_a_Jet_Backpack.ipynb

        Args:
            prompt: Generation prompt
            image: Optional image for multimodal generation
            response_schema: TypedDict class defining the expected JSON structure
            temperature: Sampling temperature

        Returns:
            Dict matching the response_schema structure

        Example:
            from typing_extensions import TypedDict

            class DIYInstructions(TypedDict):
                title: str
                difficulty: str
                estimated_time: str
                materials: list[str]
                tools: list[str]
                steps: list[str]
                safety_tips: list[str]

            result = await client.generate_structured_content(
                prompt="Generate DIY instructions for painting a room",
                response_schema=DIYInstructions
            )
        """
        try:
            from google import genai as google_genai
            from google.genai import types

            client = google_genai.Client(api_key=self.config.api_key)

            # Build content
            content_parts = [prompt]
            if image:
                pil_image = self._load_image(image)
                content_parts.append(pil_image)

            # Build config with JSON schema
            config = types.GenerateContentConfig(
                temperature=temperature or 0.4,
                response_mime_type="application/json",
            )

            if response_schema:
                config.response_schema = response_schema

            response = client.models.generate_content(
                model=self.config.default_text_model,
                contents=content_parts,
                config=config
            )

            text = getattr(response, "text", "") or "{}"
            import json
            result = json.loads(text)

            logger.info(f"[StructuredContent] Generated with schema: {response_schema.__name__ if response_schema else 'None'}")
            return result if isinstance(result, dict) else {"raw": text}

        except Exception as e:
            logger.error(f"generate_structured_content failed: {e}", exc_info=True)
            return {"error": str(e)}

    async def generate_diy_instructions(
        self,
        project_description: str,
        image: Optional[Union[str, Path, Image.Image, bytes]] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured DIY instructions for a home improvement project.

        Args:
            project_description: Description of the DIY project
            image: Optional reference image

        Returns:
            Dict with structured DIY instructions including steps, materials, tools, etc.
        """
        try:
            from typing_extensions import TypedDict

            class DIYInstructions(TypedDict):
                title: str
                difficulty: str  # "beginner", "intermediate", "advanced"
                estimated_time: str
                estimated_cost: str
                materials: list[str]
                tools: list[str]
                steps: list[str]
                safety_tips: list[str]
                pro_tips: list[str]

            prompt = (
                f"Generate detailed DIY instructions for: {project_description}\n\n"
                "Include:\n"
                "- Clear title\n"
                "- Difficulty level (beginner/intermediate/advanced)\n"
                "- Estimated time and cost\n"
                "- Complete materials list with quantities\n"
                "- Required tools\n"
                "- Step-by-step instructions (numbered)\n"
                "- Safety tips\n"
                "- Pro tips for best results"
            )

            return await self.generate_structured_content(
                prompt=prompt,
                image=image,
                response_schema=DIYInstructions,
                temperature=0.5
            )

        except Exception as e:
            logger.error(f"generate_diy_instructions failed: {e}", exc_info=True)
            return {"error": str(e)}

    def _load_image(self, image: Union[str, Path, Image.Image, bytes]) -> Image.Image:
        """
        Load image from various formats.

        Args:
            image: Image as file path, PIL Image, or bytes

        Returns:
            PIL Image
        """
        if isinstance(image, Image.Image):
            return image
        elif isinstance(image, (str, Path)):
            return Image.open(image)
        elif isinstance(image, bytes):
            return Image.open(BytesIO(image))
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Token count
        """
        try:
            result = self.text_model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}")
            return 0

