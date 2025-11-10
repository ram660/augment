# Universal Chat Implementation Summary

## 🎯 Goal
Make the chat work universally for all personas (homeowner, DIY worker, contractor) based on their actual questions and needs, not their persona label.

---

## 🔑 Key Principles

1. **Persona-Agnostic:** Respond to what the user ASKS, not what their persona label says
2. **Intent-Based Actions:** Suggest actions based on detected intent and keywords in user's message
3. **Neutral Pathways:** Offer both DIY and contractor options neutrally unless user chooses one
4. **Canvas On-Demand:** Only show canvas when there are canvas-worthy items (images, designs, products, estimates, plans)
5. **No Repetition:** Don't repeat the same action chips or questions across consecutive messages
6. **PDF Capability:** Always confirm PDF export capability; never claim inability

---

## 📝 Implementation Details

### 1. Backend: Universal Action Suggestions (`backend/api/chat.py`)

**Before (Persona-Locked):**
```python
if p == "homeowner" or s == "contractor_quotes":
    suggested_actions.append({"action": "start_contractor_quotes", ...})
if p == "diy_worker" or s == "diy_project_plan":
    suggested_actions.append({"action": "create_diy_plan", ...})
```

**After (Universal, Intent-Based):**
```python
# Intent-based actions
if intent == "cost_estimate":
    suggested_actions.append({"action": "get_detailed_estimate", ...})
elif intent == "diy_guide":
    suggested_actions.append({"action": "create_diy_plan", ...})
elif intent == "pdf_request":
    suggested_actions.append({"action": "export_pdf", ...})

# Keyword-based universal actions
um_lower = (request.message or "").lower()
if any(k in um_lower for k in ["contractor", "hire", "quote", "bid", "professional"]):
    suggested_actions.append({"action": "start_contractor_quotes", ...})
if any(k in um_lower for k in ["diy", "myself", "do it myself", "step", "guide", "how to"]):
    suggested_actions.append({"action": "create_diy_plan", ...})
```

**Key Changes:**
- Actions triggered by user's QUESTIONS (keywords + intent), not persona
- Contractor can get DIY guidance if they ask "how do I do this myself?"
- DIY worker can get contractor quotes if they ask "should I hire someone?"
- Homeowner gets both options offered neutrally

---

### 2. Backend: Universal System Prompt (`backend/workflows/chat_workflow.py`)

**Before (Persona-Specific):**
```python
if persona == "homeowner":
    prompt_parts.append("Persona: Homeowner. Be supportive and practical...")
elif persona == "diy_worker":
    prompt_parts.append("Persona: DIY Worker. Emphasize step-by-step guidance...")
elif persona == "contractor":
    prompt_parts.append("Persona: Contractor. Focus on scope of work...")
```

**After (Universal):**
```python
prompt_parts.append("""
Respond universally to all users based on their questions and needs, not their persona label:
- If they ask about costs or budgets → provide estimates and offer contractor quotes if they want professional help
- If they ask "how to" or want to DIY → provide step-by-step guidance and offer to create a detailed DIY plan
- If they ask about products → recommend products with Canadian/.ca vendors preferred
- If they ask about design/visuals → offer to generate mockups in the Design Studio
- If they want to hire help → guide them to prepare a contractor brief
- Always offer BOTH pathways (DIY and contractor) neutrally unless the user has clearly chosen one

Adapt your tone and detail level to match what the user is asking for, not what their persona label says.
""")
```

**Key Changes:**
- No more persona-specific instructions
- AI adapts to user's actual questions
- Both pathways offered neutrally
- Tone and detail match user's needs

---

### 3. Backend: PDF Export Capability (`backend/workflows/chat_workflow.py`)

**Added CRITICAL Instruction:**
```python
- CRITICAL: You CAN create and export PDFs. Never say "I cannot create PDF documents" or similar.
  When asked for a PDF, confirm you can do it and guide the user to provide any missing content
  (e.g., create a DIY plan first if needed).
```

**Intent Detection Enhanced (`backend/api/chat.py`):**
```python
# Broadened PDF keywords
if any(k in um for k in ["pdf", "export", "document", "download", "printable", "print"]):
    intent = "pdf_request"
```

**Friendly Missing Info Prompt:**
```python
if intent == "pdf_request" and "plan_to_export" in fields:
    content = (
        "I can export a polished PDF for you. I don't see a DIY plan yet — "
        "would you like me to create one now and then export it?"
    )
```

---

### 4. Backend: No Repetitive Questions (`backend/api/chat.py`)

**Added Helper Function:**
```python
def _has_recent_question(q_text: str) -> bool:
    """Check if a question was asked in the last 6 messages"""
    recent = history[-6:] if history else []
    for msg in reversed(recent):
        if msg.get("role") == "assistant":
            qs = ((msg.get("metadata") or {}).get("suggested_questions") or [])
            if q_text in qs:
                return True
    return False
```

**Filter Questions:**
```python
# Build candidate questions based on intent
candidate_questions = [...]

# Filter out recently asked questions
for q in candidate_questions:
    if not _has_recent_question(q):
        suggested_questions.append(q)
```

---

### 5. Frontend: Canvas On-Demand (`homeview-frontend/components/chat/ChatInterface.tsx`)

**Before (Always Visible):**
```tsx
<div className="hidden md:block md:h-[calc(100vh-0px)]">
  <ReactFlowCanvasPanel conversationId={currentConversationId || null} messages={messages} />
</div>
```

**After (Conditional):**
```tsx
{(() => {
  const hasCanvasItems = messages.some((m) => {
    const meta = m.metadata || {};
    return (
      meta.images?.length ||
      meta.designs?.length ||
      meta.products?.length ||
      meta.cost_estimate ||
      meta.diy_plan
    );
  });
  return hasCanvasItems ? (
    <div className="hidden md:block md:h-[calc(100vh-0px)]">
      <ReactFlowCanvasPanel conversationId={currentConversationId || null} messages={messages} />
    </div>
  ) : null;
})()}
```

**Key Changes:**
- Canvas hidden by default
- Only appears when messages contain canvas-worthy items
- Checks for: images, designs, products, cost_estimate, diy_plan

---

## 🧪 Test Scenarios

See `TEST_SCENARIOS.md` for comprehensive test cases.

See `QUICK_TEST_GUIDE.md` for a quick checklist.

---

## ✅ Expected Behavior

### For All Personas:

1. **PDF Export:**
   - ✅ Always confirms capability
   - ✅ Offers to create prerequisites if missing
   - ❌ Never claims inability

2. **Canvas:**
   - ✅ Hidden when no canvas-worthy items
   - ✅ Appears when images/designs/products/estimates/plans exist

3. **Actions:**
   - ✅ Based on user's QUESTIONS and intent
   - ✅ Not locked by persona label
   - ✅ Both DIY and contractor pathways offered neutrally

4. **Questions:**
   - ✅ Don't repeat across consecutive messages
   - ✅ Context-aware and progressive

5. **Prompts:**
   - ✅ Friendly and conversational
   - ✅ Offer to create prerequisites
   - ❌ Not rigid "I need: X" format

---

## 🎯 Example Flows

### Example 1: Contractor Wants DIY Guidance
**User:** (persona=contractor) "How do I install flooring myself?"
**Expected:**
- ✅ "Create DIY Plan" chip appears
- ✅ Step-by-step guidance offered
- ✅ No "you're a contractor, you should know this" response

### Example 2: DIY Worker Wants to Hire Help
**User:** (persona=diy_worker) "This is too complex, should I hire a pro?"
**Expected:**
- ✅ "Get Contractor Quotes" chip appears
- ✅ Guidance on preparing a contractor brief
- ✅ No "you're DIY, do it yourself" response

### Example 3: Homeowner Exploring Options
**User:** (persona=homeowner) "How much to paint my living room?"
**Expected:**
- ✅ "Get Detailed Cost Estimate" chip
- ✅ Both DIY and contractor options offered neutrally
- ✅ No forced pathway

### Example 4: PDF Export for Any Persona
**User:** (any persona) "create me a pdf document"
**Expected:**
- ✅ AI confirms it CAN create PDFs
- ✅ Offers to create DIY plan first if needed
- ✅ "Export as PDF" chip appears
- ❌ NEVER says "I cannot create PDF documents"

---

## 🚀 Deployment Checklist

Before deploying:

- [ ] Backend syntax validated (`python -m py_compile backend/api/chat.py backend/workflows/chat_workflow.py`)
- [ ] Frontend builds without errors
- [ ] All test scenarios in `TEST_SCENARIOS.md` pass
- [ ] Quick test guide in `QUICK_TEST_GUIDE.md` completed
- [ ] PDF export tested for all personas
- [ ] Canvas visibility tested
- [ ] Universal actions tested (contractor gets DIY, DIY worker gets contractor quotes)
- [ ] No repetitive questions verified
- [ ] Friendly prompts verified

---

## 📚 Related Files

- `TEST_SCENARIOS.md` - Comprehensive test cases
- `QUICK_TEST_GUIDE.md` - Quick test checklist
- `backend/api/chat.py` - Action suggestions and intent classification
- `backend/workflows/chat_workflow.py` - System prompt and universal guidance
- `homeview-frontend/components/chat/ChatInterface.tsx` - Canvas conditional rendering

---

## 🎉 Success Criteria

**The chat is successful when:**

1. ✅ Works universally for all personas
2. ✅ Responds to user's QUESTIONS, not persona label
3. ✅ PDF export works and never claims inability
4. ✅ Canvas only appears when needed
5. ✅ Actions are intent-based, not persona-locked
6. ✅ Questions don't repeat
7. ✅ Prompts are friendly and conversational
8. ✅ Both DIY and contractor pathways offered neutrally

**If all criteria met:** 🎊 **UNIVERSAL CHAT COMPLETE** 🎊

