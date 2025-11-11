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
    async def analyze_design(
        self,
        image: Union[str, Path, Image.Image, bytes],
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a room design image and return a structured summary.

        Returns a dict with keys like: colors, materials, styles, description.
        Uses the official image understanding pattern with Gemini vision.
        """
        try:
            pil_image = self._load_image(image)

            analysis_prompt = (
                "Analyze this interior room photo and return ONLY a compact JSON object with: "
                "colors (array of {name, hex?}), materials (array), styles (array of tags), "
                "and a short description (<=40 words)."
            )
            if room_hint:
                analysis_prompt += f" Room context: {room_hint}."

            response = self.vision_model.generate_content([
                analysis_prompt,
                pil_image,
            ], generation_config={"temperature": 0.2})

            text = getattr(response, "text", "") or "{}"
            # Best-effort JSON parse; tolerate stray text
            import json, re
            match = re.search(r"\{[\s\S]*\}", text)
            payload = json.loads(match.group(0)) if match else {}
            return payload if isinstance(payload, dict) else {"raw": text}
        except Exception as e:
            logger.error(f"Error in analyze_design: {e}", exc_info=True)
            return {"error": str(e)}

    async def analyze_spatial_and_quantities(
        self,
        image: Union[str, Path, Image.Image, bytes],
        room_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Estimate basic room spatial dimensions from a single photo and return structured data.

        This uses Gemini Vision's spatial reasoning capabilities (see Google Gemini Cookbook examples)
        to infer approximate dimensions by referencing common object sizes (doors, windows, furniture),
        perspective lines, and visible planes. All numbers are approximate.

        Returns a dict like:
        {
          "dimensions": {"length_m": float|null, "width_m": float|null, "height_m": float|null},
          "openings": {"windows": int|null, "doors": int|null},
          "object_counts": {"sofas": int, "chairs": int, ...},
          "assumptions": [str],
          "confidence": "low|medium|high"
        }
        """
        try:
            pil_image = self._load_image(image)
            prompt = (
                "You are a spatial reasoning assistant. From this single interior photo, estimate the room's "
                "approximate dimensions in METERS. If the whole room isn't visible, infer plausible values based on "
                "perspective and common object sizes (e.g., door ~0.9m wide x 2.0m tall, countertop ~0.9m high).\n\n"
                f"Room type (hint): {room_hint or 'unknown'}.\n"
                "Return ONLY compact JSON with this schema: {\n"
                "  \"dimensions\": { \"length_m\": number|null, \"width_m\": number|null, \"height_m\": number|null },\n"
                "  \"openings\": { \"windows\": integer|null, \"doors\": integer|null },\n"
                "  \"object_counts\": object,  // keys for notable furniture or fixtures you can name\n"
                "  \"assumptions\": [string],\n"

                "  \"confidence\": \"low\"|\"medium\"|\"high\"\n"
                "}.\n"
                "Use one decimal place for meters when possible. Keep JSON under 1KB."
            )
            resp = self.vision_model.generate_content(
                [prompt, pil_image],
                generation_config={"temperature": 0.1}
            )
            text = getattr(resp, "text", "") or "{}"
            import json, re
            m = re.search(r"\{[\s\S]*\}", text)
            data = json.loads(m.group(0)) if m else {}
            if not isinstance(data, dict):
                data = {}
            # Normalize minimal structure
            dims = data.get("dimensions") if isinstance(data.get("dimensions"), dict) else {}
            openings = data.get("openings") if isinstance(data.get("openings"), dict) else {}
            obj_counts = data.get("object_counts") if isinstance(data.get("object_counts"), dict) else {}
            assumptions = data.get("assumptions") if isinstance(data.get("assumptions"), list) else []
            confidence = data.get("confidence") if isinstance(data.get("confidence"), str) else "low"
            out = {
                "dimensions": {
                    "length_m": dims.get("length_m"),
                    "width_m": dims.get("width_m"),
                    "height_m": dims.get("height_m"),
                },
                "openings": {
                    "windows": openings.get("windows"),
                    "doors": openings.get("doors"),
                },
                "object_counts": obj_counts,
                "assumptions": assumptions,
                "confidence": confidence,
            }
            try:
                l, w, h = out["dimensions"].get("length_m"), out["dimensions"].get("width_m"), out["dimensions"].get("height_m")
                logger.info("[Spatial] dims (m): L=%s W=%s H=%s, confidence=%s", l, w, h, confidence)
            except Exception:
                pass
            return out
        except Exception as e:
            logger.warning(f"analyze_spatial_and_quantities failed: {e}", exc_info=True)
            return {"error": str(e)}

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

    async def suggest_products_with_grounding(
        self,
        summary_or_grounding: Dict[str, Any],
        max_items: int = 5,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        """
        start_time = time.time()
        search_count = 0  # Track number of Google Search calls

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

                # Extract a few style cues to help search quality
                def _as_list(val):
                    return val if isinstance(val, list) else []
                new_colors = []
                for c in _as_list(new.get("colors", [])):
                    if isinstance(c, dict):
                        label = " ".join(filter(None, [c.get("name"), c.get("hex")]))
                        if label:
                            new_colors.append(label)
                    elif isinstance(c, str):
                        new_colors.append(c)
                materials = ", ".join(_as_list(new.get("materials", [])))
                styles = ", ".join(_as_list(new.get("styles", [])))
                color_txt = ", ".join(new_colors) if new_colors else ""

                regional_text = (
                    f"Region targeting: Canada (.ca domains) and CAD prices. If possible, include nearest Canadian stores around: {location_hint}. "
                    "In each product's brief_reason, mention Canada availability and the retailer/store (and nearest store if known).\n"
                )

                prompt = (
                    "You are a grounded product recommender for interior design. Based on the user's "
                    "requested change(s), suggest up to "
                    f"{max_items} purchasable products that enable the SPECIFIC transformation.\n\n"
                    f"USER REQUEST: {user_prompt}\n"
                    f"CHANGE CATEGORIES: {changes_txt}\n"
                    f"TARGET COLORS: {color_txt}\n"
                    f"TARGET MATERIALS: {materials}\n"
                    f"TARGET STYLES: {styles}\n\n"
                    f"{brand_text}{constraint_text}"
                    f"ORIGINAL ROOM SUMMARY (JSON):\n{original}\n\n"
                    f"TRANSFORMED ROOM SUMMARY (JSON):\n{new}\n\n"
                    f"{regional_text}{retailer_hint}\n\n"
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

            logger.info(f"Google Search grounding: {search_count} calls, ${total_cost:.4f}, {duration:.2f}s")

            return parsed if isinstance(parsed, dict) else {"products": [], "sources": []}
        except Exception as e:
            logger.error(f"Error in suggest_products_with_grounding: {e}", exc_info=True)
            return {"error": str(e)}

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

