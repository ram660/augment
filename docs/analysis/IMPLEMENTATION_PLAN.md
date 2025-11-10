# HomeView AI: Deep-Dive Technologies Implementation Plan

**Created:** 2025-11-07  
**Branch:** `feat/chat-concise-history-aware`  
**Status:** Planning Phase

---

## Executive Summary

This document outlines the phased implementation of six AI technologies into HomeView AI:
1. **DeepSeek VL2** - Cost-optimized vision analysis (85% cost reduction)
2. **Microsoft MarkItDown** - Document parsing for quotes/manuals/reports
3. **IBM Docling** - Enhanced RAG with building codes and technical manuals
4. **Anthropic Skills** - Domain expertise framework (plumbing, electrical, cost, design)
5. **Agent Lightning** - Performance tracking and continuous improvement
6. **ACP + Stripe** - In-chat commerce for products and services

**Total Estimated ROI:** 764% Year 1, 2,341% over 3 years (per deep-dive analysis)

---

## Current Architecture Context

### Stack
- **Backend:** FastAPI + SQLAlchemy (async) + LangGraph workflows
- **AI Models:** Gemini 2.0 Flash (text), Gemini 2.5 Flash Image (Imagen), text-embedding-004
- **Database:** PostgreSQL + pgvector (production), SQLite (development)
- **Frontend:** React/Next.js + TypeScript
- **Deployment:** TBD (currently local development)

### Key Constraints
- **Gemini-first:** Official Gemini API documentation is the source of truth
- **Digital Twin detached:** No home_id usage in chat; Twin features are separate
- **No unnecessary files:** Only create files essential to functionality
- **Package managers only:** Never manually edit package.json, requirements.txt, etc.
- **Production-grade:** Focus on best practices, error handling, observability

### Current Features
- Multi-persona chat (homeowner, DIY worker, contractor)
- Multimodal input (text, images, PDFs)
- Intent classification and routing
- Conversation history with context-aware follow-ups
- Design Studio (image transformations via Gemini Imagen)
- Floor plan and room analysis (currently detached from chat)

---

## Technology Fit Assessment

### 1. DeepSeek VL2 (Vision Analysis)

**Fit:** ⭐⭐⭐⭐ (High - cost optimization)

**Use Cases:**
- Floor plan analysis (room detection, measurements)
- Room image analysis (materials, fixtures, condition)
- Design Studio visual grounding (precise object detection)
- Batch processing for multi-room homes

**Benefits:**
- 85% cost reduction vs Gemini Vision
- Multi-image analysis (up to 10 images in one call)
- Visual grounding with bounding boxes
- Self-hosted option for data privacy

**Risks:**
- Infrastructure complexity (GPU hosting or API dependency)
- Model quality vs Gemini (needs validation)
- Additional API key management
- Fallback logic required

**Decision:** Add as optional provider behind feature flag; keep Gemini as default.

---

### 2. Microsoft MarkItDown (Document Parsing)

**Fit:** ⭐⭐⭐⭐⭐ (Excellent - immediate value, low risk)

**Use Cases:**
- Contractor quote parsing → structured comparison
- Product datasheet extraction → chat context enrichment
- Home inspection report parsing → issue tracking
- Invoice processing → cost validation

**Benefits:**
- Instant conversion of PDF/Word/Excel/images to Markdown
- Clean table extraction
- No API costs (local processing)
- Simple Python package

**Risks:**
- Minimal (well-maintained Microsoft project)
- May struggle with complex layouts (fallback to OCR)

**Decision:** Implement in Phase 1 (highest priority).

---

### 3. IBM Docling (RAG Enhancement)

**Fit:** ⭐⭐⭐⭐ (High - specialized use case)

**Use Cases:**
- Building code indexing (jurisdiction-specific)
- Technical manual indexing (HVAC, plumbing, electrical)
- Product catalog indexing (specifications, compatibility)
- Contractor certification document parsing

**Benefits:**
- Structure-preserving chunking (sections, tables, formulas)
- OCR support for scanned documents
- Better retrieval accuracy than naive chunking
- Citation extraction

**Risks:**
- Heavier dependency (OCR extras require system libraries)
- Slower processing than MarkItDown
- Requires careful chunk size tuning

**Decision:** Implement in Phase 3 after MarkItDown proves document parsing value.

---

### 4. Anthropic Skills Framework

**Fit:** ⭐⭐⭐⭐⭐ (Excellent - quality improvement)

**Use Cases:**
- Plumbing advisor (leak diagnosis, fixture selection, code compliance)
- Electrical advisor (circuit planning, safety, permits)
- Cost estimation expert (data-driven pricing, regional adjustments)
- Design consultant (style matching, color theory, spatial planning)
- DIY safety (tool usage, protective equipment, hazard awareness)
- Contractor vetting (license verification, insurance, red flags)

**Benefits:**
- Consistent, high-quality responses
- Reusable knowledge across agents
- Easy to update/version
- No API costs (local files)
- Community contribution potential (DIY agent marketplace)

**Risks:**
- Requires creating/maintaining skill files
- Skill selection logic needs tuning
- May increase prompt size (context limits)

**Decision:** Implement in Phase 2 (high impact, low technical risk).

---

### 5. Agent Lightning (Performance Tracking)

**Fit:** ⭐⭐⭐⭐ (High - continuous improvement)

**Use Cases:**
- Track chat agent performance (satisfaction, resolution rate)
- Validate cost estimation accuracy (estimated vs actual)
- Measure contractor match success (hire rate, satisfaction)
- Identify improvement opportunities (low-rated responses, failures)
- A/B test prompt changes and skill updates

**Benefits:**
- Data-driven optimization
- User feedback collection
- Outcome validation (ground truth)
- Session replay for debugging
- RL training data generation

**Risks:**
- Additional API dependency (agentops.ai)
- Privacy considerations (session data storage)
- Requires user feedback UI
- ROI takes time to materialize

**Decision:** Implement in Phase 4 after core features are stable.

---

### 6. ACP + Stripe (Commerce)

**Fit:** ⭐⭐⭐⭐⭐ (Excellent - revenue generation)

**Use Cases:**
- Product purchases (faucets, fixtures, materials)
- Material procurement for projects (bulk ordering)
- Contractor payment escrow (milestone-based)
- Premium subscriptions (advanced features, priority support)

**Benefits:**
- Direct revenue stream (10% commission on products)
- Platform transaction fees (3% on contractor payments)
- Subscription MRR ($49/mo per premium user)
- Seamless UX (buy without leaving chat)

**Risks:**
- Requires product catalog and inventory management
- Payment processing compliance (PCI, tax calculation)
- Fulfillment integration complexity
- Customer support overhead (returns, disputes)

**Decision:** Implement in Phase 5 after user base is established.

---

## Phased Implementation Roadmap

### Phase 1: Document Parsing Foundation (Weeks 1-2)
**Goal:** Enable chat to understand uploaded documents

**Deliverables:**
- `backend/services/document_parser_service.py`
  - `parse()` - Generic document → Markdown/JSON
  - `parse_contractor_quote()` - Extract line items, totals, contractor info
  - `parse_product_datasheet()` - Extract specs, dimensions, compatibility
  - `parse_inspection_report()` - Extract issues, recommendations, photos
- `backend/api/documents.py`
  - `POST /api/v1/documents/parse`
  - `POST /api/v1/documents/contractor-quote/parse`
  - `POST /api/v1/documents/datasheet/parse`
  - `POST /api/v1/documents/inspection/parse`
- Update `backend/workflows/chat_workflow.py` to include parsed doc summaries in context
- Add document parsing to multipart chat endpoint

**Dependencies:**
- `pip install markitdown`

**Success Metrics:**
- Parse 95%+ of contractor quotes successfully
- Extract all line items and totals accurately
- Chat responses reference parsed document data

**Testing:**
- Unit tests for each parser method
- Integration tests with sample PDFs (quotes, datasheets, reports)
- Manual testing with real contractor quotes

---

### Phase 2: Skills-Driven Expertise (Weeks 3-5)
**Goal:** Provide consistent, expert-level guidance across domains

**Deliverables:**
- `backend/services/skill_manager.py`
  - `SkillManager` class (load, query, find relevant skills)
  - `SkillEnhancedAgent` base class
- `skills/` directory structure:
  - `plumbing-advisor/SKILL.md` (or `.yaml`)
  - `electrical-advisor/SKILL.md`
  - `cost-estimation-expert/SKILL.md`
  - `design-consultant/SKILL.md`
  - `diy-safety/SKILL.md`
- Update `backend/agents/conversational/home_chat_agent.py` to use skills
- `backend/api/skills.py`
  - `GET /api/v1/skills/list`
  - `GET /api/v1/skills/{skill_name}`
  - `POST /api/v1/skills/query` (ask specific skill)

**Dependencies:**
- `pip install pyyaml` (if using YAML format)

**Success Metrics:**
- 5 core skills created and tested
- Chat agent automatically selects correct skill 90%+ of time
- User satisfaction increase (measure via feedback)

**Testing:**
- Unit tests for skill loading and selection
- Integration tests for each skill (sample questions → expected answers)
- A/B test skill-enhanced vs baseline responses

---

### Phase 3: Enhanced RAG with Building Codes (Weeks 6-8)
**Goal:** Provide accurate, cited answers to code/compliance questions

**Deliverables:**
- `backend/services/enhanced_rag_service.py`
  - `index_building_code()` - Docling-based indexing with structure preservation
  - `index_technical_manual()` - Product manuals, HVAC guides, etc.
  - `query_building_code()` - Jurisdiction-aware queries with citations
  - `query_technical_manual()` - Product-specific queries
- `backend/api/knowledge.py` (admin-only)
  - `POST /api/v1/knowledge/building-codes/upload`
  - `POST /api/v1/knowledge/manuals/upload`
  - `GET /api/v1/knowledge/search`
- Update chat workflow to query RAG for code/compliance questions
- Add citation display in chat UI

**Dependencies:**
- `pip install docling`
- (Optional) `pip install docling[ocr]` for scanned documents

**Success Metrics:**
- Index 10+ building codes (major jurisdictions)
- 95%+ accuracy on code compliance questions
- All answers include section citations

**Testing:**
- Unit tests for indexing and chunking
- Integration tests with sample code PDFs
- Manual validation with known code questions

---

### Phase 4: Performance Tracking & Feedback (Weeks 9-11)
**Goal:** Measure and improve agent performance continuously

**Deliverables:**
- `backend/services/agent_metrics.py`
  - `AgentMetricsService` class (track sessions, record feedback/outcomes)
  - `@track_agent` decorator for automatic tracking
- Update all agents to use `@track_agent` decorator
- `backend/api/feedback.py`
  - `POST /api/v1/feedback/response/{session_id}/thumbs`
  - `POST /api/v1/feedback/response/{session_id}/rating`
  - `POST /api/v1/feedback/estimate/{session_id}/outcome`
  - `POST /api/v1/feedback/contractor/{session_id}/hired`
  - `POST /api/v1/feedback/project/{session_id}/completed`
- `backend/api/analytics.py` (admin-only)
  - `GET /api/v1/analytics/agents/performance`
  - `GET /api/v1/analytics/agents/improvement-opportunities`
- Frontend: Add thumbs up/down buttons to chat messages
- Frontend: Add rating modal after key interactions

**Dependencies:**
- `pip install agentops`
- AgentOps API key (sign up at agentops.ai)

**Success Metrics:**
- Track 100% of agent interactions
- Collect feedback on 30%+ of responses
- Identify top 3 improvement areas per agent

**Testing:**
- Unit tests for metrics recording
- Integration tests for feedback endpoints
- Manual testing of analytics dashboard

---

### Phase 5: Commerce Integration (Weeks 12-16)
**Goal:** Enable in-chat product purchases and contractor payments

**Deliverables:**
- `backend/agents/commerce/purchase_agent.py`
  - `ProductPurchaseAgent` class
  - `initiate_purchase()` - Full purchase flow with Stripe
  - `get_purchase_options()` - Preview cost/shipping/tax
- `backend/api/commerce.py`
  - `POST /api/v1/commerce/purchase/initiate`
  - `GET /api/v1/commerce/purchase/options`
  - `GET /api/v1/commerce/orders`
  - `GET /api/v1/commerce/orders/{order_id}`
  - `POST /api/v1/commerce/payment-methods`
- Database models: `Order`, `OrderItem`, `PaymentMethod`
- Update chat agent to detect purchase intent and offer purchase flow
- Frontend: Stripe Elements integration for payment methods
- Frontend: Purchase confirmation modal
- Frontend: Order history page

**Dependencies:**
- `pip install stripe`
- `pip install anthropic-agent-commerce` (if ACP is available; otherwise direct Stripe)
- Stripe account + API keys
- Product catalog (initial seed data)

**Success Metrics:**
- 10%+ of product recommendations convert to purchases
- Average order value $150+
- <1% payment failure rate

**Testing:**
- Unit tests for purchase flow
- Integration tests with Stripe test mode
- End-to-end testing with test cards
- Manual testing of full purchase journey

---

## Cross-Technology Integration Patterns

### Pattern 1: MarkItDown + Chat Context
```
User uploads contractor quote PDF
→ MarkItDown parses to structured data
→ Chat agent includes quote details in context
→ User asks "Is this quote reasonable?"
→ Agent compares to cost estimation skill + market data
```

### Pattern 2: Skills + Agent Lightning
```
User asks plumbing question
→ Chat agent activates plumbing-advisor skill
→ Agent Lightning tracks session
→ User gives thumbs down
→ Analytics identifies pattern (too technical for beginners)
→ Update skill with simpler explanations
→ A/B test improvement
```

### Pattern 3: Docling RAG + Skills + Commerce
```
User asks "Can I install a tankless water heater myself?"
→ Chat agent activates plumbing-advisor + diy-safety skills
→ Queries building code RAG for permit requirements
→ Provides answer with code citations
→ Recommends specific tankless models
→ Offers in-chat purchase option
```

### Pattern 4: DeepSeek + MarkItDown + Commerce
```
User uploads room photo + contractor quote PDF
→ DeepSeek analyzes room (dimensions, current fixtures)
→ MarkItDown parses quote (products, prices)
→ Agent validates quote against room requirements
→ Suggests alternative products (better fit or price)
→ Enables purchase of recommended products
```

---

## Dependencies & Prerequisites

### Python Packages (install via pip)
- `markitdown` - Phase 1
- `pyyaml` - Phase 2 (if using YAML skills)
- `docling` - Phase 3
- `docling[ocr]` - Phase 3 (optional, for scanned docs)
- `agentops` - Phase 4
- `stripe` - Phase 5

### API Keys & Accounts
- AgentOps API key - Phase 4 (sign up at agentops.ai)
- Stripe account + API keys - Phase 5 (sign up at stripe.com)
- (Optional) DeepSeek API key - Future (if not self-hosting)

### Infrastructure
- (Optional) GPU instance for DeepSeek self-hosting - Future
- (Optional) OCR system libraries for Docling - Phase 3

---

## Risk Mitigation

### Technical Risks
- **Package conflicts:** Use virtual environment; test each install
- **API rate limits:** Implement exponential backoff and caching
- **Model quality:** A/B test new providers vs Gemini baseline
- **Context limits:** Implement smart truncation and summarization

### Business Risks
- **User adoption:** Gradual rollout with feature flags
- **Cost overruns:** Monitor usage; set budget alerts
- **Compliance:** Legal review of commerce features before launch
- **Support burden:** Comprehensive documentation and error messages

---

## Success Criteria

### Phase 1 (Document Parsing)
- ✅ Parse 95%+ of contractor quotes successfully
- ✅ Chat responses reference parsed data accurately
- ✅ Zero regressions in existing chat functionality

### Phase 2 (Skills)
- ✅ 5 core skills operational
- ✅ Correct skill selection 90%+ of time
- ✅ Measurable quality improvement in responses

### Phase 3 (RAG)
- ✅ 10+ building codes indexed
- ✅ 95%+ accuracy on code questions
- ✅ All answers include citations

### Phase 4 (Metrics)
- ✅ 100% of interactions tracked
- ✅ 30%+ feedback collection rate
- ✅ Actionable insights identified

### Phase 5 (Commerce)
- ✅ 10%+ conversion on product recommendations
- ✅ $150+ average order value
- ✅ <1% payment failure rate

---

## Next Steps

1. **Review & Approve:** User reviews this plan and approves phases
2. **Branch Strategy:** Continue on `feat/chat-concise-history-aware` or create new branch per phase?
3. **Phase 1 Kickoff:** Install markitdown and begin DocumentParserService implementation
4. **Testing Strategy:** Set up test fixtures (sample PDFs, quotes, datasheets)
5. **Documentation:** Update README with new capabilities as they ship

---

## Questions for User

1. **Skill file format:** SKILL.md (Markdown) or skill.yaml (YAML-only)?
2. **DeepSeek priority:** Add in Phase 1 or defer to Phase 6+?
3. **Branch strategy:** One branch for all phases or separate branches?
4. **Commerce scope:** Start with products only or include contractor payments in Phase 5?
5. **Testing requirements:** Unit tests only or also integration/E2E tests?

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-07  
**Next Review:** After Phase 1 completion

