"""
UnifiedVisionService - abstraction over vision operations (DeepSeek-first with Gemini fallback).

Follows Google Gemini official docs for image-understanding and generation:
- https://ai.google.dev/gemini-api/docs
- Image understanding: https://ai.google.dev/gemini-api/docs/image-understanding
- Image generation/editing: https://ai.google.dev/gemini-api/docs/image-generation

DeepSeek VL2 is supported behind a provider flag and will gracefully fallback to
Gemini when unavailable or on error. Lightweight cost/confidence metadata is
exposed via last_metadata property after each call.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from PIL import Image

from backend.integrations.gemini import GeminiClient
from backend.integrations.deepseek.vision_client import DeepSeekVisionClient
from backend.services.cache_service import get_cache_service
import hashlib
import logging

logger = logging.getLogger(__name__)


class UnifiedVisionService:
    """Provider-agnostic facade for vision ops with fallback and metadata."""

    def __init__(self, provider: Optional[str] = None) -> None:
        self._provider = (provider or os.getenv("VISION_PROVIDER", "gemini")).lower()
        self._gemini = GeminiClient()
        self._deepseek = None
        if self._provider == "deepseek":
            self._deepseek = DeepSeekVisionClient(
                model_size=os.getenv("DEEPSEEK_MODEL_SIZE", "small")
            )
        # Last-call metadata
        self._last_meta: Dict[str, Any] = {}

        # Cache service
        self.cache_service = get_cache_service()

    @property
    def last_metadata(self) -> Dict[str, Any]:
        return self._last_meta

    def _set_meta(self, provider: str, start_ts: float, **extra: Any) -> None:
        elapsed_ms = (time.perf_counter() - start_ts) * 1000.0
        meta = {
            "provider": provider,
            "processing_time_ms": round(elapsed_ms, 2),
        }
        meta.update({k: v for k, v in extra.items() if v is not None})
        self._last_meta = meta

    def _create_cache_key(self, image: Union[str, Path, Image.Image, bytes], prompt: str) -> str:
        """Create a cache key for image analysis."""
        # Hash the prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:16]

        # Hash the image content
        if isinstance(image, (str, Path)):
            # For file paths, use the path + file modification time
            image_path = Path(image)
            if image_path.exists():
                mtime = image_path.stat().st_mtime
                image_hash = hashlib.md5(f"{image_path}:{mtime}".encode()).hexdigest()[:16]
            else:
                image_hash = hashlib.md5(str(image).encode()).hexdigest()[:16]
        elif isinstance(image, bytes):
            # Hash the bytes directly
            image_hash = hashlib.md5(image).hexdigest()[:16]
        elif isinstance(image, Image.Image):
            # Convert PIL image to bytes and hash
            import io
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            image_hash = hashlib.md5(buf.getvalue()).hexdigest()[:16]
        else:
            image_hash = "unknown"

        return f"vision:{image_hash}:{prompt_hash}"

    # ---------------------- High-level analysis ---------------------- #
    async def analyze_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.3,
    ) -> str:
        """General image analysis with provider fallback.

        If provider is 'deepseek', try DeepSeek first and fallback to Gemini on error.
        """
        # Check cache first
        cache_key = self._create_cache_key(image, prompt)
        cached_result = await self.cache_service.get(cache_key, cache_type="vision_analysis")
        if cached_result:
            logger.debug(f"Vision cache hit for prompt: {prompt[:50]}...")
            self._last_meta = {"provider": "cache", "processing_time_ms": 0}
            return cached_result

        start = time.perf_counter()
        if self._provider == "deepseek" and self._deepseek is not None:
            try:
                text = await self._deepseek.analyze_image(image=image, prompt=prompt, temperature=temperature)
                # If DeepSeek returns, assume lower cost; confidence unknown unless caller parses JSON
                self._set_meta("deepseek", start, cost_estimate=0.03, confidence=None)

                # Cache the result
                await self.cache_service.set(cache_key, text, cache_type="vision_analysis")
                return text
            except Exception as e:
                # Fallback to Gemini
                try:
                    text = await self._gemini.analyze_image(image=image, prompt=prompt, temperature=temperature)
                    self._set_meta("gemini", start, fallback_reason=str(e)[:200])

                    # Cache the result
                    await self.cache_service.set(cache_key, text, cache_type="vision_analysis")
                    return text
                except Exception as e2:
                    self._set_meta("gemini", start, fallback_reason=f"gemini_failed: {str(e2)[:120]}")
                    raise
        # Default: Gemini only
        text = await self._gemini.analyze_image(image=image, prompt=prompt, temperature=temperature)
        self._set_meta("gemini", start)

        # Cache the result
        await self.cache_service.set(cache_key, text, cache_type="vision_analysis")
        return text

    async def analyze_floor_plan(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.3,
    ) -> str:
        return await self.analyze_image(image=image, prompt=prompt, temperature=temperature)

    async def analyze_room(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.3,
    ) -> str:
        return await self.analyze_image(image=image, prompt=prompt, temperature=temperature)

    # ---------------------- Segmentation ---------------------- #
    async def segment_image(
        self,
        reference_image: Union[str, Path, Image.Image, bytes],
        segment_class: str,
        points: Optional[List[Dict[str, int]]] = None,
        num_masks: int = 1,
    ) -> List[Image.Image]:
        """Return list of PIL mask images (white=target, black=background).

        DeepSeek segmentation not implemented in stub; fallback to Gemini.
        """
        start = time.perf_counter()
        try:
            # No DeepSeek segmentation in stub; always Gemini
            masks = await self._gemini.segment_image(
                reference_image=reference_image,
                segment_class=segment_class,
                points=points,
                num_masks=num_masks,
            )
            self._set_meta("gemini", start)
            return masks
        except Exception as e:
            self._set_meta("gemini", start, fallback_reason=str(e)[:200])
            raise

