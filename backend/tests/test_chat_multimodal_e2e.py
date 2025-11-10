import json
import uuid
import asyncio
import pytest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.api.auth import get_current_user, get_current_user_optional

# We will monkeypatch GeminiClient methods used by ChatWorkflow
import backend.integrations.gemini.client as gemini_mod


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """Override auth to return a lightweight fake user for API tests."""
    fake_user = SimpleNamespace(id=uuid.uuid4())

    async def _override():
        return fake_user

    async def _override_optional():
        return fake_user

    app.dependency_overrides[get_current_user] = _override
    app.dependency_overrides[get_current_user_optional] = _override_optional
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_user_optional, None)


@pytest.fixture
def client():
    # Use context manager to ensure lifespan events (DB init) run
    with TestClient(app) as c:
        yield c


@pytest.fixture
def patched_gemini(monkeypatch):
    """Patch GeminiClient.generate_text and suggest_products_with_grounding to be deterministic."""

    async def fake_generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int | None = None):
        # Intent classification path
        if "Classify the user's intent" in prompt:
            # Extract the actual user message from the prompt to avoid keyword collisions
            lower_prompt = prompt.lower()
            marker = 'user message: "'
            start = lower_prompt.find(marker)
            if start != -1:
                end = lower_prompt.find('"', start + len(marker))
                user_msg = lower_prompt[start + len(marker): end if end != -1 else None]
            else:
                user_msg = lower_prompt
            # Prefer DIY guide if asked (place before PDF export keywords)
            if ("guide" in user_msg) or ("step-by-step" in user_msg) or ("how do i" in user_msg):
                return '{"intent": "diy_guide", "confidence": 0.9, "requires_home_data": false}'
            if ("pdf" in user_msg) or ("export" in user_msg) or ("document" in user_msg):
                return '{"intent": "pdf_request", "confidence": 0.9, "requires_home_data": false}'
            if ("estimate" in user_msg) or ("cost" in user_msg):
                return '{"intent": "cost_estimate", "confidence": 0.8, "requires_home_data": true}'
            if any(k in user_msg for k in ["product", "recommend", "material", "tile", "grout", "appliance", "paint", "flooring"]):
                return '{"intent": "product_recommendation", "confidence": 0.85, "requires_home_data": false}'
            if any(k in user_msg for k in ["contractor", "quote", "hire", "bid", "install for me"]):
                return '{"intent": "contractor_quotes", "confidence": 0.8, "requires_home_data": false}'
            return '{"intent": "question", "confidence": 0.6, "requires_home_data": false}'
        # Suggested actions/questions helper prompts
        if ("Suggestions for next actions" in prompt) or ("Top 4 concise follow-up questions" in prompt):
            return "[]"
        # Default response generation
        return "Got it. Here's a helpful response with next steps."

    async def fake_grounding(self, grounding_input: dict, max_items: int = 5):
        # Return YouTube-like results when asked for tutorials; otherwise simple product stubs
        req = (grounding_input or {}).get("requested_changes") or []
        user_prompt = (grounding_input or {}).get("user_prompt") or ""
        if any("youtube" in (r or "").lower() for r in req) or "site:youtube.com" in user_prompt:
            return {
                "products": [
                    {
                        "name": "Backsplash Tile Tutorial",
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "description": "Step-by-step backsplash install",
                        "vendor": "YouTube",
                    }
                ],
                "sources": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            }
        return {
            "products": [
                {
                    "name": "Sample Product",
                    "url": "https://example.com/product",
                    "price": "$19.99",
                    "vendor": "Example Store",
                }
            ],
            "sources": ["https://example.com"],
        }

    monkeypatch.setattr(gemini_mod.GeminiClient, "generate_text", fake_generate_text, raising=True)
    monkeypatch.setattr(gemini_mod.GeminiClient, "suggest_products_with_grounding", fake_grounding, raising=True)


def test_chat_message_with_youtube_enrichment(client, patched_gemini):
    # DIY guide request should trigger YouTube enrichment in agent mode
    payload = {
        "message": "Give me a step-by-step DIY guide to install a kitchen backsplash",
        "persona": "diy_worker",
        "scenario": "diy_project_plan",
        "mode": "agent",
    }
    r = client.post("/api/v1/chat/message", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    # Basic response structure
    assert data["conversation_id"]
    assert isinstance(data["response"], str)
    # Multimodal enrichment should include YouTube videos
    md = data.get("metadata") or {}
    vids = md.get("youtube_videos") or []
    assert isinstance(vids, list)
    assert len(vids) >= 1
    assert vids[0].get("url", "").startswith("https://www.youtube.com/") or "youtu.be" in (vids[0].get("url") or "")


def test_execute_action_export_pdf_requests_plan_first(client, patched_gemini):
    # Start a conversation first
    r1 = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Please export this as a PDF",
            "persona": "diy_worker",
            "scenario": "diy_project_plan",
            "mode": "agent",
        },
    )
    assert r1.status_code == 200, r1.text
    conv_id = r1.json()["conversation_id"]

    # Try exporting PDF without an existing DIY plan should request plan_to_export
    r2 = client.post(
        "/api/v1/chat/execute-action",
        json={
            "conversation_id": conv_id,
            "action": {"action": "export_pdf"},
            "persona": "diy_worker",
            "scenario": "diy_project_plan",
        },
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["status"] in ("needs_input", "error")
    # If ReportLab isn't installed, implementation may return error directly; otherwise it asks for a plan
    if data["status"] == "needs_input":
        assert "requested_fields" in data.get("metadata", {})
    else:
        # error path: PDF dependency missing
        assert data.get("metadata", {}).get("error") == "pdf_export_unavailable"




def test_chat_message_with_product_enrichment(client, patched_gemini):
    # Product/material recommendation should trigger web search enrichment
    payload = {
        "message": "Recommend backsplash tile and grout options for a 10x10 kitchen under $400",
        "persona": "homeowner",
        "scenario": "material_selection",
        "mode": "agent",
    }
    r = client.post("/api/v1/chat/message", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    md = data.get("metadata") or {}
    products = md.get("web_search_results") or []
    sources = md.get("web_sources") or []
    assert isinstance(products, list) and len(products) >= 1
    assert isinstance(sources, list) and len(sources) >= 1


def test_contractor_quotes_suggested_action(client, patched_gemini):
    # Contractor quotes flow should suggest starting contractor quotes
    payload = {
        "message": "Find a licensed contractor to install a kitchen backsplash in Toronto",
        "persona": "homeowner",
        "scenario": "contractor_quotes",
        "mode": "agent",
    }
    r = client.post("/api/v1/chat/message", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    actions = data.get("suggested_actions") or []
    assert any((a or {}).get("action") == "start_contractor_quotes" for a in actions)
