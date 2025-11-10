import pytest

from backend.services.vision_service import UnifiedVisionService
from backend.integrations.deepseek.vision_client import DeepSeekVisionClient
from backend.integrations.gemini import GeminiClient


@pytest.mark.asyncio
async def test_deepseek_fallbacks_to_gemini(monkeypatch):
    # DeepSeek raises to trigger fallback
    async def fake_ds_analyze(self, image, prompt, temperature=0.2):
        raise RuntimeError("DeepSeek not configured")

    # Gemini returns deterministic text
    async def fake_gem_analyze(self, image, prompt, temperature=0.3):
        return "{}"

    monkeypatch.setattr(DeepSeekVisionClient, "analyze_image", fake_ds_analyze, raising=True)
    monkeypatch.setattr(GeminiClient, "analyze_image", fake_gem_analyze, raising=True)

    svc = UnifiedVisionService(provider="deepseek")
    text = await svc.analyze_image(image=b"fake-bytes", prompt="test")

    meta = svc.last_metadata
    assert text == "{}"
    assert meta.get("provider") == "gemini"
    assert "fallback_reason" in meta


@pytest.mark.asyncio
async def test_deepseek_used_when_available(monkeypatch):
    # DeepSeek returns success
    async def fake_ds_analyze(self, image, prompt, temperature=0.2):
        return "{\"ok\": true}"

    monkeypatch.setattr(DeepSeekVisionClient, "analyze_image", fake_ds_analyze, raising=True)

    svc = UnifiedVisionService(provider="deepseek")
    text = await svc.analyze_image(image=b"fake-bytes", prompt="test")

    meta = svc.last_metadata
    assert text.startswith("{")
    assert meta.get("provider") == "deepseek"

