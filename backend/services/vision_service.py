"""
UnifiedVisionService - abstraction over vision operations (Gemini-only implementation for now).

Follows Google Gemini official docs for image-understanding and generation:
- https://ai.google.dev/gemini-api/docs
- Image understanding: https://ai.google.dev/gemini-api/docs/image-understanding
- Image generation/editing: https://ai.google.dev/gemini-api/docs/image-generation
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from PIL import Image

from backend.integrations.gemini import GeminiClient


class UnifiedVisionService:
    """Provider-agnostic facade for vision ops.

    Initial provider is Gemini via GeminiClient. The interface is intentionally
    minimal and matches current agent needs so we can swap/add providers later
    without refactoring agents/workflows.
    """

    def __init__(self, provider: str = "gemini") -> None:
        if provider != "gemini":
            raise NotImplementedError(f"Provider '{provider}' not supported yet")
        self._provider = provider
        self._gemini = GeminiClient()

    # ---------------------- High-level analysis ---------------------- #
    async def analyze_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.3,
    ) -> str:
        """General image analysis.

        Uses Gemini Vision per official docs (generate_content with [prompt, image]).
        """
        return await self._gemini.analyze_image(image=image, prompt=prompt, temperature=temperature)

    async def analyze_floor_plan(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.3,
    ) -> str:
        """Alias for analyze_image; kept for clarity/metrics separation later."""
        return await self.analyze_image(image=image, prompt=prompt, temperature=temperature)

    async def analyze_room(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.3,
    ) -> str:
        """Alias for analyze_image; kept for clarity/metrics separation later."""
        return await self.analyze_image(image=image, prompt=prompt, temperature=temperature)

    # ---------------------- Segmentation ---------------------- #
    async def segment_image(
        self,
        reference_image: Union[str, Path, Image.Image, bytes],
        segment_class: str,
        points: Optional[List[Dict[str, int]]] = None,
        num_masks: int = 1,
    ) -> List[Image.Image]:
        """Return list of PIL mask images (white=target, black=background)."""
        return await self._gemini.segment_image(
            reference_image=reference_image,
            segment_class=segment_class,
            points=points,
            num_masks=num_masks,
        )

