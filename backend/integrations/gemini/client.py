"""
Gemini API client wrapper for HomeVision AI.

This module provides a unified interface to Google's Gemini models:
- Text generation (gemini-2.0-flash)
- Vision analysis (gemini-2.0-flash)
- Image generation (gemini-2.0-flash with Imagen)
- Embeddings (text-embedding-004)

Official Documentation:
- https://ai.google.dev/gemini-api/docs
- https://ai.google.dev/gemini-api/docs/imagen
- https://ai.google.dev/gemini-api/docs/image-understanding
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
            # Create a model with Google Search grounding tool enabled
            grounded_model = GenerativeModel(
                model_name=self.config.default_text_model,
                safety_settings=self.safety_settings,
                tools=[{"google_search": {}}],
            )

            # Build targeted prompt
            payload = summary_or_grounding or {}
            is_diff = isinstance(payload, dict) and (
                "original_summary" in payload or "new_summary" in payload
            )
            if is_diff:
                user_prompt = payload.get("user_prompt", "")
                changes = payload.get("requested_changes", []) or []
                original = payload.get("original_summary", {})
                new = payload.get("new_summary", {})
                changes_txt = ", ".join(changes) if changes else "unspecified"
                prompt = (
                    "You are a grounded product recommender for interior design. Based on the user's"
                    " requested change(s), suggest up to "
                    f"{max_items} purchasable products that enable the SPECIFIC transformation.\n\n"
                    f"USER REQUEST: {user_prompt}\n"
                    f"CHANGE CATEGORIES: {changes_txt}\n\n"
                    f"ORIGINAL ROOM SUMMARY (JSON):\n{original}\n\n"
                    f"TRANSFORMED ROOM SUMMARY (JSON):\n{new}\n\n"
                    "Return ONLY JSON with schema: {\n"
                    "  \"products\": [ { \"name\": str, \"category\": str, \"brief_reason\": str, \"price_estimate\"?: str, \"url\": str } ],\n"
                    "  \"sources\": [ str ]\n"
                    "}."
                )
            else:
                prompt = (
                    "Given this interior design summary, suggest up to "
                    f"{max_items} purchasable products that match the style/colors/materials. "
                    "For each product, include: name, category, brief_reason, price_estimate (if found), "
                    "and a url from a reputable retailer. Return ONLY JSON with schema: {\n"
                    "  \"products\": [ { \"name\": str, \"category\": str, \"brief_reason\": str, \"price_estimate\"?: str, \"url\": str } ],\n"
                    "  \"sources\": [ str ]\n"
                    "}.\n\n"
                    f"Design summary JSON:\n{payload}"
                )

            resp = grounded_model.generate_content(prompt, generation_config={"temperature": 0.3})
            text = getattr(resp, "text", "") or "{}"

            import json, re
            match = re.search(r"\{[\s\S]*\}", text)
            parsed = json.loads(match.group(0)) if match else {}
            # Attach any grounding metadata if available
            try:
                gm = getattr(resp, "grounding_metadata", None)
                if gm and isinstance(parsed, dict):
                    parsed.setdefault("grounding_metadata", str(gm))
            except Exception:
                pass
            return parsed if isinstance(parsed, dict) else {"raw": text}
        except Exception as e:
            logger.error(f"Error in suggest_products_with_grounding: {e}", exc_info=True)
            return {"error": str(e)}

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

            for msg in messages[:-1]:  # All but last message
                if msg["role"] == "user":
                    chat.send_message(msg["content"])

            # Send final message and get response
            response = chat.send_message(messages[-1]["content"])

            return response.text

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
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

