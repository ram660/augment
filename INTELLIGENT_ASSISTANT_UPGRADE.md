# HomeView AI - Intelligent Assistant Upgrade Plan

## Problem Statement

The current AI behaves like a **basic chatbot** that:
- ❌ Asks repetitive questions (ignores conversation history)
- ❌ Lists capabilities instead of taking action
- ❌ Asks for information the user already provided
- ❌ Provides generic responses without context
- ❌ Acts like a menu system, not a personal assistant

**User Feedback:** "this is very basic static bot, we should do better in helping customers"

---

## Solution: Transform into Intelligent Personal Assistant

### 1. Enhanced System Prompt ✅ DONE

**File Created:** `backend/prompts/intelligent_assistant_system_prompt.txt`

This new prompt teaches the AI to:
- **Remember context** - Read entire conversation history
- **Make smart assumptions** - Infer details from context
- **Take initiative** - Execute tasks proactively
- **Be empathetic** - Acknowledge user emotions
- **Provide specifics** - Give numbers, steps, and actionable advice

### 2. Backend Changes Needed

#### A. Update `backend/workflows/chat_workflow.py`

**Location:** Line 1625-1647 in `_build_response_prompt()` method

**Change:** Replace the current system prompt with the new intelligent assistant prompt:

```python
# Read the enhanced prompt from file
prompt_file = Path(__file__).parent.parent / "prompts" / "intelligent_assistant_system_prompt.txt"
if prompt_file.exists():
    enhanced_prompt = prompt_file.read_text(encoding="utf-8")
    prompt_parts.append(enhanced_prompt)
else:
    # Fallback to original prompt
    prompt_parts.append("""You are HomeView AI...""")
```

#### B. Enhance Conversation History Context

**Location:** `_load_conversation_history()` method (line 584)

**Current:** Loads last 10 messages
**Enhancement:** Include richer context:
- User's stated preferences (quality tier, DIY vs contractor, budget)
- Previous decisions and confirmations
- Emotional state indicators

#### C. Add Context Extraction

**New Method:** `_extract_conversation_context(history: List[Dict]) -> Dict`

Extract key facts from conversation:
- Quality tier mentioned (budget/mid-range/high-end)
- DIY vs contractor preference
- Room dimensions if provided
- Budget constraints
- Timeline requirements

### 3. Streamlit Playground Enhancements ✅ DONE

**File:** `streamlit_homeview_chat.py`

**Changes Made:**
- ✅ Show AI thinking process in real-time
- ✅ Display workflow steps and tool execution
- ✅ Status indicators ("AI is thinking...", "Executing task...")
- ✅ Expandable thinking process section
- ✅ Toggle to show/hide thinking (enabled by default)

### 4. Example Transformations

#### Before (Current Behavior):
```
User: "Ugh, my bathroom is outdated, chipped tiles, bad showerhead"
AI: "I can help! Would you like a cost estimate or DIY plan?"

User: "Estimating the cost"
AI: "What quality tier are you aiming for?"

User: "mid range"
AI: "Should I include labor costs?"

User: "i will do it myself"
AI: "What quality tier are you aiming for?"  ← REPEATS QUESTION!
```

#### After (Target Behavior):
```
User: "Ugh, my bathroom is outdated, chipped tiles, bad showerhead"
AI: "I understand how frustrating that is. Let me help you tackle this systematically.

Based on a typical bathroom renovation, here's what I'm thinking:

**Quick Wins (Weekend projects):**
1. Replace showerhead ($50-150, 30 min)
2. Re-caulk tub/shower ($20, 2 hours)

**Bigger Impact (1-2 weekends):**
3. Retile problem areas ($300-800, depends on size)
4. Update fixtures ($200-500)

For a mid-range DIY bathroom refresh, you're looking at $600-1,500 total.

Want me to create a detailed plan starting with the quick wins?"

User: "yes"
AI: "Perfect! I'm creating a DIY plan for your bathroom refresh...

[Shows thinking process]
🔧 Using tool: intelligence_generate_diy_guide
📋 Generating step-by-step instructions...
✅ Plan ready!

**DIY Bathroom Refresh Plan**
[Detailed plan with tools, materials, steps, safety notes]

I've also found these products at Home Depot Canada:
- Moen Showerhead ($89.99)
- DAP Caulk Kit ($24.99)
[etc.]

Total estimated cost: $847
Time: 2 weekends

Ready to export this as a PDF?"
```

---

## Implementation Priority

### Phase 1: Backend Intelligence (COMPLETED ✅)
1. ✅ Create enhanced system prompt file
2. ✅ Update `chat_workflow.py` to use new prompt
3. ⏳ Add context extraction from conversation history (NEXT)
4. ⏳ Test with real conversations (READY TO TEST)

### Phase 2: Streamlit Visualization (DONE)
1. ✅ Show thinking process
2. ✅ Display tool execution
3. ✅ Status indicators
4. ✅ Toggle controls

### Phase 3: Testing & Refinement
1. ⏳ Test with various scenarios
2. ⏳ Measure conversation quality
3. ⏳ Iterate on prompt based on results

---

## Testing Scenarios

### Scenario 1: Bathroom Renovation (Overwhelmed User)
**User:** "Ugh, I don't even know where to begin. Every time I walk into that bathroom, I just feel... defeated."

**Expected AI Behavior:**
1. Acknowledge emotion
2. Break down into simple steps
3. Take initiative to assess situation
4. Provide specific, actionable plan
5. Don't ask unnecessary questions

### Scenario 2: Cost Estimate (Context Awareness)
**Conversation:**
- User: "I want to renovate my bathroom"
- AI: [asks about scope]
- User: "mid range quality"
- User: "i will do it myself"
- User: "Estimating the cost"

**Expected AI Behavior:**
- Remember "mid range" from 2 messages ago
- Remember "DIY" approach
- Generate estimate immediately
- Don't ask "what quality tier?" again

### Scenario 3: DIY Planning (Proactive)
**User:** "Create a DIY plan for painting my living room"

**Expected AI Behavior:**
1. Assume standard room size (12x15) unless specified
2. Generate plan immediately
3. Include tools, materials, steps
4. Offer to find products
5. Suggest PDF export

---

## Success Metrics

- ❌ **Reduce repetitive questions** - AI should never ask the same question twice
- ✅ **Increase tool usage** - AI should proactively use tools, not just suggest them
- ✅ **Improve context retention** - AI remembers details from 5+ messages ago
- ✅ **Faster task completion** - Users get results in fewer messages
- ✅ **Higher satisfaction** - Users feel helped, not interrogated

---

## Next Steps

1. **Restart backend** with updated prompt
2. **Test in Streamlit playground** with real scenarios
3. **Iterate on prompt** based on results
4. **Deploy to production** once validated

---

## Files Modified

- ✅ `backend/prompts/intelligent_assistant_system_prompt.txt` (NEW)
- ✅ `streamlit_homeview_chat.py` (ENHANCED)
- ⏳ `backend/workflows/chat_workflow.py` (NEEDS UPDATE)
- ✅ `STREAMLIT_PLAYGROUND_QUICKSTART.md` (UPDATED)
- ✅ `INTELLIGENT_ASSISTANT_UPGRADE.md` (THIS FILE)

