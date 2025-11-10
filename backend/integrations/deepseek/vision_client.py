"""
DeepSeek Vision client (VL2) - lightweight abstraction.

This is a minimal, test-friendly client that can be patched/mocked in unit tests.
In production, wire this up to your actual DeepSeek/VL2 inference endpoint or SDK.

Design goals:
- Async interface matching GeminiClient.analyze_image
- No heavyweight deps by default; avoid network calls in tests
- Raise a clear error by default if not configured so UnifiedVisionService can fallback
"""
from __future__ import annotations

import os
import time
from typing import Optional, Union
from pathlib import Path

from PIL import Image
from backend.services.cost_tracking_service import get_cost_tracking_service
from backend.services.event_bus import get_event_bus


class DeepSeekVisionClient:
    """Minimal DeepSeek VL2 vision client.

    By default this stub raises RuntimeError to signal "not configured" so callers
    can implement a safe fallback (e.g., to Gemini). Tests can monkeypatch
    analyze_image to simulate various outcomes (success/low confidence/error).
    """

    def __init__(self, model_size: str = "small", api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model_size = model_size or os.getenv("DEEPSEEK_MODEL_SIZE", "small")
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_API_URL")

        # Initialize services
        self.cost_service = get_cost_tracking_service()
        self.event_bus = get_event_bus()

    async def analyze_image(
        self,
        image: Union[str, Path, Image.Image, bytes],
        prompt: str,
        temperature: Optional[float] = 0.2,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> str:
        """Analyze an image and return text.

        Replace this with a real implementation when wiring the DeepSeek endpoint.
        The default behavior raises to trigger fallback in UnifiedVisionService.
        """
        start_time = time.time()

        try:
            # TODO: Replace with actual DeepSeek API call
            # For now, raise to trigger fallback
            raise RuntimeError("DeepSeekVisionClient not configured. Set DEEPSEEK_API_* and implement the request.")

            # When implemented, track cost like this:
            # result = await self._call_deepseek_api(image, prompt, temperature)
            #
            # duration = time.time() - start_time
            # self.cost_service.track_cost(
            #     service="deepseek",
            #     operation="analyze_image",
            #     user_id=user_id,
            #     project_id=project_id,
            #     metadata={
            #         "model": f"deepseek-vl2-{self.model_size}",
            #         "duration_ms": int(duration * 1000)
            #     }
            # )
            #
            # return result

        except Exception as e:
            # Track failed attempt (no cost)
            duration = time.time() - start_time
            await self.event_bus.publish(
                "deepseek.vision_failed",
                {
                    "error": str(e),
                    "user_id": user_id,
                    "project_id": project_id,
                    "duration_ms": int(duration * 1000)
                },
                source="deepseek_vision_client"
            )
            raise

    async def segment_image(
        self,
        reference_image: Union[str, Path, Image.Image, bytes],
        segment_class: str,
        num_masks: int = 1,
    ):
        """Optional segmentation endpoint; not implemented in the stub.
        Callers should fallback to Gemini segmentation when unavailable.
        """
        raise NotImplementedError("DeepSeek segmentation not implemented in stub")

