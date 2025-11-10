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
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from io import BytesIO

from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

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
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system_instruction: System instruction for the model

        Returns:
            Generated text
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
                    system_instruction=system_instruction
                )

            response = model.generate_content(
                prompt,
                generation_config=generation_config
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
        temperature: Optional[float] = None
    ) -> str:
        """
        Analyze an image with Gemini Vision.

        Args:
            image: Image as file path, PIL Image, or bytes
            prompt: Analysis prompt
            temperature: Sampling temperature

        Returns:
            Analysis result as text
        """
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

    async def suggest_products_with_grounding(
        self,
        summary_or_grounding: Dict[str, Any],
        max_items: int = 5,
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
                        if isinstance(strict, dict):
                            prods2 = strict.get('products') or []
                            ca_only = [p for p in prods2 if isinstance(p, dict) and _is_ca_url(p.get('url',''))]
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
                    else:
                        # Drop all non-CA items to honor policy
                        parsed['products'] = []
                        parsed['grounding_notice'] = (
                            'Filtered non-Canadian sources. No Canadian (.ca or /en-ca) product pages were found this time.'
                        )
            except Exception:
                pass

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

    async def get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts

        Returns:
            List of embedding vectors
        """
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

