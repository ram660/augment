# HomeView AI – Consolidated Agent System Implementation Plan

**Source inputs:**
- Introduction to Agents
- Agent Quality
- Agent Tools & Interoperability with MCP
- Context Engineering: Sessions & Memory
- Prototype to Production (AgentOps)

This plan outlines how to evolve HomeView AI from a prototype into a production-grade, agentic system across Chat, Design Studio, and future tabs.

---

## 1. Goals & Scope

**Primary goals**
- Turn HomeView into a **Level 2 agent system** (orchestrated workflows, tools, memory) with:
  - Image-first, guest-friendly UX
  - Stable, testable backends
  - Good observability and safety
- Establish **AgentOps**: evaluation-gated releases, CI/CD, and safe rollout strategies.

**Non-goals (for now)**
- Full multi-agent A2A ecosystem
- Heavy fine-tuning / RLHF
- Complex contractor marketplace logic (beyond basic placeholders)

---

## 2. Current State (Assumptions)

- Backend: FastAPI services for Chat, Design Studio, analysis; uses Google APIs (Vision, Imagen, Grounding).
- Frontend: Next.js app with main tabs (Chat, Design Studio, Explore, Communities, Contractors/Jobs).
- Agents:
  - Single primary agent per major flow (Chat, Design Studio) with tools.
  - No persistent memory across sessions (only short-term context in each request).
- Quality & Ops:
  - Some logging and ad-hoc tests.
  - No Golden Dataset, no LLM-based eval harness.
  - CI/CD either minimal or not agent-aware.

If any of these are inaccurate, we’ll adjust the plan as we implement.

---

## 3. High-Level Phasing

**Phase 0 – Baseline & Cleanup (quick)**
- Confirm current architecture, main APIs, and data flows.
- Identify and remove dead code paths from older experiments (carefully, behind flags).

**Phase 1 – Core Agent Architecture & Tools**
- Stabilize the main agent entrypoints and tool design.
- Ensure all critical flows use clear, well-documented tools and MCP-style patterns where useful.

**Phase 2 – Context & Memory**
- Implement robust session management and long-term memory for user preferences, projects, and feedback.

**Phase 3 – Quality, Evaluation, & Safety**
- Define Golden Datasets and build an evaluation harness (LLM-as-judge + metrics).

**Phase 4 – CI/CD & AgentOps**
- Implement evaluation-gated CI/CD, safe rollout strategies, and improved observability.

**Phase 5 – Multi-Agent & A2A (Future)**
- Gradually separate concerns into specialized agents and prepare for A2A.


### 3.1 Current implementation status (snapshot)

_As of November 2025; this is meant to stay high-level and will drift over time._

- **Phase 0 – Baseline & Cleanup:** First pass completed (architecture documented, main chat and design flows mapped, legacy ChatOrchestrator flagged behind a feature flag). Further cleanup will be done opportunistically.
- **Phase 1 – Core Agent Architecture & Tools:** Partially implemented. `ChatWorkflow` is the primary chat entrypoint with structured tool logging and Design Studio tools wired through the Gemini client; a full cross-product tool registry and unified agent interface are still to be finished.
- **Phase 2 – Context & Memory:** In progress. Conversation summaries, a token-aware context window, and a `UserMemory`/`MemoryService` layer (including basic LLM-driven extraction and chat integration) are implemented; Design Studio memory writes and debugging APIs are being wired.
- **Phase 3 – Quality, Evaluation & Safety:** Not started.
- **Phase 4 – CI/CD & AgentOps:** Not started.
- **Phase 5 – Multi-Agent & A2A:** Not started.

---

## 4. Phase 0 – Baseline & Cleanup

**Objectives**
- Get a clear picture of the existing code.
- Remove or isolate legacy experiments that interfere with the new architecture.

**Key tasks**
- Document current:
  - Chat backend entrypoints and agent orchestration.
  - Design Studio pipeline (upload → analysis → transform → recommendations).
- Mark experimental/legacy modules and wrap them behind feature flags where needed.
- Add or fix basic unit tests for existing critical functions (no new features yet).

---

## 5. Phase 1 – Core Agent Architecture & Tools

**Objectives**
- Implement a clear, reusable agent architecture across Chat and Design Studio.
- Standardize tool design and registration.

**Key tasks**
- Define a **HomeView Agent Interface**:
  - Unified abstraction for Chat & Design Studio agents (ReAct-style loop, tools, system prompts).
- Refine tool design using best practices from the MCP paper:
  - Narrow, user-facing tasks (e.g., `analyze_room_image`, `generate_design_options`, `estimate_budget_range`).
  - Strong parameter schemas and structured outputs (JSON-like responses).
  - Clear docstrings including when/when-not-to-use.
- Inventory existing implicit tools and convert them to explicit tool functions.
- Introduce a simple **tool registry** in code (not necessarily a full MCP server yet).
- Ensure all backend calls from Chat & Design Studio go through this standardized agent + tool layer.

**Outputs**
- A small set of well-documented tools powering the main flows.
- Cleaner agent orchestration code for Chat and Design Studio.

---

## 6. Phase 2 – Context & Memory

**Objectives**
- Implement robust sessions (short-term context) and memory (long-term personalization).

**Key tasks**
- Session layer:
  - Introduce a `Session` model (ID, user ID/anonymous token, messages, metadata, images).
  - Add Redis- or DB-backed session storage with TTL.
  - Wire Chat and Design Studio requests to use session IDs and maintain history.
- Context manager:
  - Implement token-aware context building (sliding window + summarization of older turns).
  - Support injecting analysis results and tool outputs into context in structured form.
- Memory layer (minimum viable):
  - Define HomeView memory topics: design preferences, project info, budget, home constraints, feedback.
  - Implement basic memory extraction (LLM-driven or rule-based) at session end.
  - Store memories in a simple vector DB or relational store with provenance (user, topic, source, confidence).
  - Implement retrieval for:
    - Design Studio (style/material preferences)
    - Chat (ongoing project context, budget, dislikes/likes).

**Outputs**
- Users get personalized suggestions and consistent context across sessions.
- Memory operations run asynchronously and don’t block UX.

---

## 7. Phase 3 – Quality, Evaluation & Safety

**Objectives**
- Make quality measurable and regression-resistant.
- Embed safety in prompts and tests.

**Key tasks**
- Golden Datasets:
  - Define representative scenarios for Chat and Design Studio (including Vancouver-specific defaults, budgets, safety edge cases).
- Evaluation harness:
  - Implement offline eval runner that:
    - Replays scenarios against the agent.
    - Uses an LLM-as-judge (and where useful, agent-as-judge) to score:
      - Task success
      - Helpfulness
      - Safety (policy violations, hallucinations)
  - Track metrics: win-rate vs baseline, quality scores per dimension.
- Safety:
  - Consolidate a single security/system prompt for all agents.
  - Add test cases for prompt injection, unsafe DIY, data leakage, etc.
  - Ensure eval suite fails when safety regressions occur.

**Outputs**
- A repeatable eval suite that can run locally and in CI.
- Clear quality baselines and guardrails.

---

## 8. Phase 4 – CI/CD & AgentOps

**Objectives**
- Have a reliable path from commit → tested agent → staged → production.

**Key tasks**
- CI:
  - Add GitHub Actions / Cloud Build jobs that run:
    - Unit tests, linters, type checks.
    - The agent evaluation suite on Golden Datasets.
- CD:
  - Define staging environment for backend.
  - Deploy backend containers to staging on merge to `main`.
  - Add a manual, approval-based promotion to production.
- Rollout strategies:
  - Introduce versioning for agents (e.g., `agent_version`, or route key).
  - Implement simple canary routing (small % of traffic to new version).
  - Add feature flags for risky capabilities (new tools, new memory behavior).
- Observability:
  - Add structured logs for: sessions, tools, latencies, costs, errors.
  - Basic dashboards for latency, error rate, and cost per feature.

**Outputs**
- Evaluation-gated, observable deployment flow with safe rollouts and rollback.

---

## 9. Phase 5 – Multi-Agent & A2A (Future)

**Objectives**
- Prepare HomeView to scale into multiple specialized agents and integrate with external agents.

**Key tasks**
- Identify natural agent boundaries (design, budgeting, contractors, communities).
- For at least one boundary, define an agent contract (inputs/outputs, responsibilities).
- Optionally explore exposing an internal agent via A2A, while keeping most logic in-process.

**Outputs**
- A roadmap to multi-agent collaboration without complicating the current system prematurely.

---

## 10. Recommended Implementation Order

If we start implementing now:
1. Phase 0 and Phase 1 in parallel (where safe): clean up and stabilize the agent + tools.
2. Phase 2 to unlock real personalization via sessions + memory.
3. Phase 3 so we can quantify improvements and protect safety.
4. Phase 4 to make iteration safe and fast.
5. Phase 5 opportunistically as new features demand specialization.

This plan should guide issue/ticket creation and branch strategy as we begin implementation.

