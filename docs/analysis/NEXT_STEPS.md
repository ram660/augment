## Next Steps from the Deep Dive Integration Guide

This action plan translates the integration guide into concrete, high‑impact work items, with clear deliverables, files to touch, acceptance criteria, and a suggested sequence.

### Top priorities (quick summary)
- Priority 1: DeepSeek VL2 integration with smart fallback, cost tracking, and batch analysis (largest ROI)
- Priority 2: Pin MarkItDown dependency and add doc parse smoke tests (stabilize existing endpoints)
- Priority 3: Docling-based ingestion for complex PDFs into RAG (phase 3, optional but valuable)
- Priority 4: Skills strategy (keep internal SkillManager now; revisit Anthropic Skills later)
- Priority 5: Commerce (Stripe/ACP) when monetization path is ready

---

## Priority 1 — DeepSeek VL2 vision integration (Highest ROI)
Goal: Reduce vision analysis cost by ~85% via DeepSeek, while retaining quality using an automatic fallback to Gemini. Add provider/cost/confidence metadata and batch image support.

Deliverables:
- New integration: backend/integrations/deepseek/vision_client.py
- Enhanced service: backend/services/vision_service.py (DeepSeek-first with Gemini fallback, metadata, batch)
- Agents updated to record provider/cost/confidence: 
  - backend/agents/digital_twin/floor_plan_agent.py
  - backend/agents/homeowner/vision_agent.py
- Tests covering provider selection, fallback behavior, and metadata shape
- Env flags: VISION_PROVIDER, DEEPSEEK_MODEL_SIZE

Files to modify/add:
- Add: backend/integrations/deepseek/vision_client.py (DeepSeekVisionClient)
- Modify: backend/services/vision_service.py (provider selection: deepseek|gemini, fallback, batch)
- Modify: backend/agents/digital_twin/floor_plan_agent.py (include analysis metadata in response)
- Modify: backend/agents/homeowner/vision_agent.py (same; optionally route through UnifiedVisionService)
- Add tests under backend/tests/ (vision fallback, metadata)

Example skeletons (for reference):

<augment_code_snippet path="backend/integrations/deepseek/vision_client.py" mode="EXCERPT">
````python
class DeepSeekVisionClient:
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
    async def analyze_image(self, image, prompt, temperature: float = 0.3) -> str:
        # TODO: call DeepSeek VL2 and return text
        return ""
````
</augment_code_snippet>

<augment_code_snippet path="backend/services/vision_service.py" mode="EXCERPT">
````python
class UnifiedVisionService:
    def __init__(self, provider: str = "deepseek") -> None:
        # TODO: instantiate deepseek and gemini; set fallback policy
        ...
````
</augment_code_snippet>

Implementation steps:
1) Implement DeepSeekVisionClient with minimal analyze_image(images) API
2) Update UnifiedVisionService:
   - Try DeepSeek first; if confidence < threshold or error → fallback to Gemini
   - Return metadata: {provider, confidence, cost, processing_time_ms, fallback_reason?}
   - Add analyze_images([...]) for batch processing
3) Update floor_plan_agent and vision_agent to include returned metadata in their responses
4) Add env/config defaults:
   - VISION_PROVIDER=deepseek
   - DEEPSEEK_MODEL_SIZE=small
5) Tests:
   - Unit tests for fallback path (force DeepSeek low confidence/error → Gemini)
   - Assert metadata keys in agent responses
   - Batch analysis happy-path test

Acceptance criteria:
- Vision service supports DeepSeek with automatic Gemini fallback
- Agent responses include provider, cost estimate, confidence, processing_time_ms
- Batch pathway supported (and used where helpful)
- Tests pass in CI without external GPU dependencies (mock DeepSeek client)

Risks & mitigations:
- DeepSeek hosting: start with mocked client for tests; add real integration behind env flag
- Quality regressions: use confidence gating + fallback to Gemini

---

## Priority 2 — Stabilize document parsing (MarkItDown dep + smoke tests)
Goal: Ensure document endpoints work out of the box.

Findings: Code already uses MarkItDown but requirements.txt does not pin it.

Steps:
- Add dependency: markitdown to requirements.txt (ask before installing in CI/CD)
- Add smoke tests for document endpoints:
  - /api/v1/documents/parse
  - /api/v1/documents/chat
- Keep DocumentParserService fail‑safe error message for missing dependency

Acceptance criteria:
- Fresh environment with `pip install -r requirements.txt` enables document endpoints
- Tests cover parse + chat flows (using small sample files)

---

## Priority 3 — Docling-enhanced RAG for complex PDFs (Phase 3)
Goal: Ingest building codes, manuals, and technical docs with structure‑preserving parsing.

Deliverables:
- New: backend/services/enhanced_rag_service.py (Docling-powered ingestion)
- Optional admin endpoints: backend/api/knowledge.py for upload/index/search
- Tests for ingesting a sample code/manual and searching with citations

Key steps:
1) Introduce Docling dependency (get approval): `docling` (and optionally `docling[ocr]`)
2) Implement EnhancedRAGService that converts PDFs to markdown/structured text with Docling
3) Chunk, embed (reuse existing embedding), and store with metadata
4) Add search endpoint and citation fields in results

Acceptance criteria:
- Can ingest at least one complex PDF and retrieve structured sections with citations
- Hybrid retrieval continues to work with new chunks

Note: This is optional Phase 3; do after Priority 1 and 2 deliver.

---

## Priority 4 — Skills strategy
Current: Lightweight internal SkillManager is integrated in chat; no Anthropic Skills framework.

Recommendation now:
- Expand internal SkillManager with a few high‑value skills (e.g., Building Code quick tips, Contractor quote checklist, Product fit checks)
- Revisit Anthropic Skills later if external packaging/versioning is needed

Acceptance criteria:
- SkillManager returns concise skill blocks for common chat intents (cost_estimate, diy_guide, product_recommendation)
- Prompts show improved grounded guidance without bloating context

---

## Priority 5 — Commerce (Stripe/ACP)
Start when monetization flow is defined.

Initial steps:
- Define minimal purchase/checkout flow and data model
- Implement Stripe secret/webhook handling and a test mode flow
- Add unit tests for signature verification and idempotency

Acceptance criteria:
- Test checkout flow works in Stripe test mode end‑to‑end

---

## Cross‑cutting: metrics and QA
- Add cost/latency/provider counters to monitoring; expose basic stats (e.g., in Agent Lightning store stats)
- Extend tests:
  - Vision: fallback and metadata tests
  - Documents: MarkItDown parse/chat
  - RAG: retrieval quality smoke with mixed sources
- Keep all external heavy deps behind flags; mock in unit tests

---

## Suggested sequencing & timeline
- Week 1: DeepSeek integration + fallback + metadata + tests (Priority 1)
- Week 1 (parallel): Add markitdown to requirements + doc parse smoke tests (Priority 2)
- Week 2: Batch analysis integration in agents; monitoring & metrics for cost
- Week 3 (optional): Docling Enhanced RAG spike and admin endpoints (Priority 3)
- Week 3+: Skills expansion; plan commerce integration based on product readiness

---

## Environment/config checklist
- VISION_PROVIDER=deepseek (default), gemini as fallback
- DEEPSEEK_MODEL_SIZE=tiny|small|full (default small)
- Keep existing GOOGLE_API_KEY for Gemini fallback
- Add toggles for batch enablement if needed

---

## Definition of done (overall)
- Vision analysis cost reduced via DeepSeek-first strategy with reliable Gemini fallback
- Agents emit provider/cost/confidence metadata
- Document endpoints stable in fresh environments (MarkItDown pinned + tests)
- Optional: Docling path proven for at least one complex PDF with searchable citations
- All new code has unit tests and is guarded by env flags for safe CI

