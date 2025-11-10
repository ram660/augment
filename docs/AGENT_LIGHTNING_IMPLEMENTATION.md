# Agent Lightning Implementation Guide

## Overview

This document describes the Agent Lightning integration for HomeView AI, enabling reinforcement learning-based optimization of our AI agents.

**Status:** Phase 1 Complete ✅  
**Date:** 2025-11-08  
**Version:** 0.1.0

---

## What is Agent Lightning?

Agent Lightning is a reinforcement learning framework that enables continuous improvement of AI agents through user feedback. It works with any AI framework (LangChain, CrewAI, AutoGen, etc.) and requires minimal code changes.

### Key Features

- **Zero-code optimization** (almost) - Just add tracking calls
- **Framework agnostic** - Works with our LangChain/LangGraph stack
- **Selective optimization** - Optimize specific agents in multi-agent systems
- **Multiple algorithms** - GRPO, DPO, PPO, and custom algorithms

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Chat Workflow                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. User Message → 2. Generate Response               │   │
│  │ 3. Track Interaction (implicit reward)               │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         AgentTracker.track_chat_message()            │   │
│  │  - Prompt, Response, Metadata, Implicit Reward       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LightningStore (SQLite)                    │
│  Stores: prompts, responses, rewards, metadata              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  User Provides Feedback                      │
│  POST /api/v1/chat/feedback                                  │
│  - Thumbs up/down, Rating 1-5, Copy, Regenerate             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              RewardCalculator.calculate_reward()             │
│  Converts feedback → reward score (0.0 to 1.0)              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Update LightningStore with Explicit Reward           │
│         Track with AgentTracker (updated reward)             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Training (Future - Phase 3)                   │
│  Trainer.train() → Optimized prompts/model                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Phase 1: Infrastructure Setup ✅ COMPLETE

#### 1. LightningStore Manager

**File:** `backend/integrations/agentlightning/store.py`

Manages the central store for agent interactions:
- SQLite for development (`lightning.db` in project root)
- PostgreSQL for production (future)
- Query helpers for retrieving training data
- Statistics and monitoring

**Usage:**
```python
from backend.integrations.agentlightning.store import get_lightning_store

store = get_lightning_store()
stats = store.get_statistics("chat_agent")
# Returns: {total_interactions, avg_reward, min_reward, max_reward}
```

#### 2. Agent Tracker

**File:** `backend/integrations/agentlightning/tracker.py`

Tracks agent interactions using `agl.emit_step()`:
- User prompts
- Agent responses
- Rewards (implicit or explicit)
- Metadata (intent, context, persona, etc.)

**Usage:**
```python
from backend.integrations.agentlightning.tracker import AgentTracker

tracker = AgentTracker(agent_name="chat_agent")
tracker.track_chat_message(
    user_message="How much to paint my living room?",
    ai_response="Based on a 12x15 room...",
    conversation_id="conv-123",
    intent="cost_estimate",
    reward=0.85  # Calculated reward
)
```

#### 3. Reward Calculator

**File:** `backend/integrations/agentlightning/rewards.py`

Calculates reward scores from user feedback:

**Reward Scale:**
- `1.0` - Excellent (thumbs up, 5-star, copy)
- `0.7-0.9` - Good (4-star, follow-up question)
- `0.5` - Neutral (3-star, no feedback)
- `0.2-0.4` - Poor (2-star, regenerate)
- `0.0` - Bad (thumbs down, 1-star)

**Adjustments:**
- +0.1 for intent match
- +0.05 for context utilization
- -0.1 for too short responses (<50 chars)
- -0.05 for too long responses (>2000 chars)

**Usage:**
```python
from backend.integrations.agentlightning.rewards import RewardCalculator, FeedbackType

calculator = RewardCalculator()
reward = calculator.calculate_from_feedback(
    feedback_type=FeedbackType.THUMBS_UP,
    additional_signals={"intent_match": True, "used_context": True}
)
# Returns: 1.0 (max reward with bonuses)
```

#### 4. Chat Workflow Integration

**File:** `backend/workflows/chat_workflow.py`

Added tracking to the `_finalize()` step:
1. Calculate implicit reward based on response quality
2. Track interaction with AgentTracker
3. Store in LightningStore for future training

**Tracked Metadata:**
- Intent and confidence
- Context usage
- Suggested actions
- Response length
- Execution time
- Errors

#### 5. Feedback API Endpoint

**File:** `backend/api/chat.py`

**Endpoint:** `POST /api/v1/chat/feedback`

**Request:**
```json
{
  "message_id": "msg-uuid",
  "feedback_type": "thumbs_up",
  "rating": 5,
  "comment": "Very helpful!",
  "helpful": true,
  "accurate": true,
  "complete": true
}
```

**Response:**
```json
{
  "feedback_id": "feedback-uuid",
  "message_id": "msg-uuid",
  "feedback_type": "thumbs_up",
  "reward_score": 1.0,
  "created_at": "2025-11-08T12:00:00Z"
}
```

**Feedback Types:**
- `thumbs_up` / `thumbs_down`
- `rating_1` through `rating_5`
- `regenerate` (user wasn't satisfied)
- `copy` (user found it useful)
- `follow_up` (user engaged with response)

#### 6. Database Model

**File:** `backend/models/message_feedback.py`

New `MessageFeedback` model stores:
- Message ID and conversation ID
- User ID (optional for anonymous)
- Feedback type and rating
- Calculated reward score
- Text comments
- Boolean flags (helpful, accurate, complete)

---

## Testing the Implementation

### 1. Verify Installation

```bash
pip show agentlightning
# Should show version 0.2.1
```

### 2. Test Tracking

Start a chat conversation and check if interactions are being tracked:

```python
from backend.integrations.agentlightning.store import get_lightning_store

store = get_lightning_store()
stats = store.get_statistics("chat_agent")
print(stats)
# Should show: {enabled: True, total_interactions: N, avg_reward: X}
```

### 3. Test Feedback API

```bash
curl -X POST http://localhost:8000/api/v1/chat/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "your-message-id",
    "feedback_type": "thumbs_up",
    "rating": 5
  }'
```

### 4. Check Database

```sql
SELECT * FROM message_feedback ORDER BY created_at DESC LIMIT 10;
```

---

## Next Steps

### Phase 2: Data Collection (Weeks 3-6)

- [ ] Collect 1000+ interaction samples
- [ ] Build reward functions for each agent type
- [ ] Monitor reward distribution
- [ ] Identify low-performing patterns

### Phase 3: Training (Weeks 7-8)

- [ ] Implement training workflow
- [ ] Train Chat Agent with GRPO algorithm
- [ ] Evaluate on held-out test set
- [ ] Compare to baseline performance

### Phase 4: Deployment (Weeks 9-10)

- [ ] Deploy optimized agents to staging
- [ ] A/B test with 20% of users
- [ ] Monitor performance metrics
- [ ] Gradually roll out to 100%

---

## Performance Metrics

### Expected Improvements

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Chat Response Quality | 70% | 85-90% | +15-20% |
| User Satisfaction | 75% | 90% | +15% |
| Response Accuracy | 70% | 85% | +15% |
| First-Attempt Success | 60% | 75% | +15% |

### Monitoring

Track these metrics in production:
- Average reward score per day/week
- Feedback submission rate
- Distribution of feedback types
- Reward score by intent type
- Reward score by persona

---

## Files Created/Modified

### New Files
- `backend/integrations/agentlightning/__init__.py`
- `backend/integrations/agentlightning/store.py`
- `backend/integrations/agentlightning/tracker.py`
- `backend/integrations/agentlightning/rewards.py`
- `backend/models/message_feedback.py`

### Modified Files
- `requirements.txt` - Added agentlightning>=0.2.1
- `backend/workflows/chat_workflow.py` - Added tracking
- `backend/api/chat.py` - Added feedback endpoint

---

## Troubleshooting

### Agent Lightning Not Available

If `agentlightning` import fails, tracking is automatically disabled. Check:
```python
from backend.integrations.agentlightning.store import get_lightning_store
store = get_lightning_store()
print(store.is_enabled())  # Should be True
```

### No Data in LightningStore

Check if tracking is working:
```python
from backend.integrations.agentlightning.tracker import AgentTracker
tracker = AgentTracker("chat_agent")
print(tracker.enabled)  # Should be True
```

### Database Migration Needed

The `MessageFeedback` model requires a database migration:
```bash
# Create migration
alembic revision --autogenerate -m "Add message feedback table"

# Apply migration
alembic upgrade head
```

---

## References

- [Agent Lightning GitHub](https://github.com/microsoft/agent-lightning)
- [Agent Lightning Documentation](https://microsoft.github.io/agent-lightning/)
- [HomeView AI Technology Integration Analysis](./analysis/AI_TECHNOLOGY_INTEGRATION_ANALYSIS.md)

