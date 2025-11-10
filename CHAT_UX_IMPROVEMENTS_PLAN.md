# Chat UX Improvements Plan

## Issues Identified from User Conversation

### 1. **Duplicate "Suggested actions" appearing multiple times** ❌
**Problem:** Suggestions appear after every AI response, creating visual clutter
**Root Cause:** Backend generates suggestions for every message without checking recent history
**Impact:** User sees same buttons repeatedly (e.g., "Get Contractor Quotes" 5+ times)

### 2. **Repetitive "Continue your journey" prompts** ❌  
**Problem:** Same follow-up questions asked repeatedly
**Root Cause:** Question deduplication logic not working properly
**Impact:** User sees "What are the dimensions?" multiple times in same conversation

### 3. **Poor formatting - hard to follow** ❌
**Problem:** Responses lack structure, bullets not formatted properly
**Root Cause:** AI generates markdown but frontend doesn't render it properly
**Impact:** Wall of text, hard to scan

### 4. **No agent/chat toggle** ❌
**Problem:** No way to switch between simple chat and agentic mode
**Root Cause:** Feature doesn't exist
**Impact:** Users can't control whether AI executes actions automatically

### 5. **Missing multimodal features** ❌
**Problem:** No web search, image generation, visual aids, YouTube videos
**Root Cause:** Not integrated into workflow
**Impact:** Limited functionality compared to modern AI assistants

### 6. **Circular conversation - AI keeps asking instead of executing** ❌
**Problem:** AI says "I can export PDF" but doesn't do it, asks more questions
**Root Cause:** Over-cautious prompting, too many confirmation steps
**Impact:** Frustrating user experience, takes 5+ messages to accomplish simple tasks

---

## Solutions

### ✅ Solution 1: Smart Suggestion Deduplication

**Backend Changes:**
- Track last 3 messages for suggested_actions
- Only show action if:
  - Not shown in last 3 messages
  - OR user explicitly requested it
  - OR context changed significantly

**Code Location:** `backend/api/chat.py` lines 1260-1341

**Implementation:**
```python
def _should_show_action(action_key: str, history: List[dict], intent: str) -> bool:
    """Only show action if not recently shown OR explicitly requested."""
    # Check last 3 messages
    recent = history[-3:] if len(history) >= 3 else history
    for msg in reversed(recent):
        if msg.get("role") == "assistant":
            acts = ((msg.get("metadata") or {}).get("suggested_actions") or [])
            for a in acts:
                if (a.get("action") or a.get("type")) == action_key:
                    return False  # Already shown recently
    return True
```

### ✅ Solution 2: Remove "Continue your journey" Label

**Frontend Changes:**
- Remove hardcoded "Continue your journey:" text
- Show questions as subtle chips without label
- Only show if questions are contextually relevant

**Code Location:** `homeview-frontend/components/chat/MessageBubble.tsx` line 477

**Before:**
```tsx
<p className="text-xs text-gray-500 px-2">Continue your journey:</p>
```

**After:**
```tsx
{/* No label - just show chips */}
```

### ✅ Solution 3: Proper Markdown Rendering

**Frontend Changes:**
- Install `react-markdown` and `remark-gfm`
- Render AI responses with proper formatting
- Support: bullets, numbered lists, bold, italic, code blocks

**Code Location:** `homeview-frontend/components/chat/MessageBubble.tsx` line 78

**Implementation:**
```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

<ReactMarkdown 
  remarkPlugins={[remarkGfm]}
  className="prose prose-sm max-w-none"
>
  {message.content}
</ReactMarkdown>
```

### ✅ Solution 4: Agent/Chat Mode Toggle

**Frontend Changes:**
- Add toggle component (already created: `ChatModeToggle.tsx`)
- Integrate into `ChatInterface.tsx`
- Pass mode to backend in chat request

**Backend Changes:**
- Add `mode` field to `ChatRequest`
- In CHAT mode: no automatic actions, simple responses
- In AGENT mode: full agentic workflow with tools

**Code Location:** 
- Frontend: `homeview-frontend/components/chat/ChatInterface.tsx`
- Backend: `backend/api/chat.py`

**UI Placement:**
```
┌─────────────────────────────────────┐
│  HomeView AI    [Chat|Agent] Toggle │
├─────────────────────────────────────┤
│  Messages...                        │
└─────────────────────────────────────┘
```

### ✅ Solution 5: Integrate Multimodal Features

**Web Search (Google Grounding):**
- Use Gemini's grounding feature for product recommendations
- Automatically search Canadian vendors (.ca domains)
- Show sources with clickable links

**Image Generation (Gemini Imagen):**
- Generate visual aids for DIY steps
- Create design mockups
- Show before/after comparisons

**YouTube Video Recommendations:**
- Search for relevant DIY tutorials
- Embed video thumbnails with links
- Match to current task (e.g., "how to install exhaust fan")

**Visual Aids:**
- Generate diagrams for measurements
- Create checklists with checkboxes
- Show progress bars for multi-step tasks

**Implementation Locations:**
- Web Search: `backend/integrations/gemini/client.py` - add grounding parameter
- Image Gen: `backend/integrations/gemini/imagen.py` - new file
- YouTube: `backend/integrations/youtube_search.py` - new file
- Visual Aids: `homeview-frontend/components/chat/VisualAids.tsx` - new file

### ✅ Solution 6: Reduce Confirmation Steps

**Backend Prompt Changes:**
- When user says "download PDF", generate and return download link immediately
- When user says "create DIY plan", create it immediately
- Only ask for clarification if truly ambiguous

**Code Location:** `backend/workflows/chat_workflow.py` lines 710-730

**Before:**
```
User: "download pdf"
AI: "Certainly! Which document would you like to download?"
```

**After:**
```
User: "download pdf"
AI: "Here's your PDF: [Download DIY Plan - Exhaust Fan Replacement.pdf]"
```

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Remove "Continue your journey" label
2. ✅ Fix suggestion deduplication (last 3 messages)
3. ✅ Add markdown rendering
4. ✅ Create ChatModeToggle component (DONE)

### Phase 2: Core Features (3-4 hours)
5. ⏳ Integrate agent/chat mode toggle
6. ⏳ Add web search (Google Grounding)
7. ⏳ Reduce confirmation steps in prompts

### Phase 3: Advanced Features (5-6 hours)
8. ⏳ Image generation (Gemini Imagen)
9. ⏳ YouTube video recommendations
10. ⏳ Visual aids (diagrams, checklists)

---

## Expected Outcome

### Before (Current UX):
```
User: "i want to change exhaust fan the bathroom"
AI: "Replacing a bathroom exhaust fan is a great project..."

Suggested actions:
- Generate DIY Step-by-Step Plan
- Get Contractor Quotes

Continue your journey:
- What is your skill level and available time?
- Do you already have any of the required tools?
- What is your budget and deadline?
- Do you prefer DIY plan or contractor quotes?

---

User: "Create the detailed DIY plan"
AI: "Excellent! Here is a detailed DIY plan..."

Suggested actions:
- Generate DIY Step-by-Step Plan  ← DUPLICATE
- Get Contractor Quotes  ← DUPLICATE

Continue your journey:  ← REPETITIVE
- What is your skill level and available time?
- Do you already have any of the required tools?
```

### After (Improved UX):
```
User: "i want to change exhaust fan the bathroom"
AI: "I'll create a DIY plan for replacing your bathroom exhaust fan.

**Tools Needed:**
• Screwdriver set
• Wire strippers
• Voltage tester

**Materials:**
• New exhaust fan ($50-150 CAD)
• Wire nuts
• Caulk

**Estimated Time:** 2-4 hours

[Generate DIY Step-by-Step Plan] [Get Contractor Quotes]

---

User: "Create the detailed DIY plan"
AI: "✅ DIY Plan Created!

**Step 1: Safety First**
Turn off power at breaker...

[📥 Download PDF] [🛒 Find Products] [🎥 Watch Tutorial Video]
```

---

## Files to Modify

### Backend:
1. `backend/api/chat.py` - Fix suggestion deduplication, add mode support
2. `backend/workflows/chat_workflow.py` - Reduce confirmation steps
3. `backend/integrations/gemini/client.py` - Add grounding support
4. `backend/integrations/gemini/imagen.py` - NEW: Image generation
5. `backend/integrations/youtube_search.py` - NEW: YouTube API

### Frontend:
6. `homeview-frontend/components/chat/MessageBubble.tsx` - Markdown rendering, remove labels
7. `homeview-frontend/components/chat/ChatInterface.tsx` - Integrate mode toggle
8. `homeview-frontend/components/chat/ChatModeToggle.tsx` - ✅ DONE
9. `homeview-frontend/components/chat/VisualAids.tsx` - NEW: Diagrams, checklists
10. `homeview-frontend/package.json` - Add react-markdown, remark-gfm

---

## Testing Checklist

- [ ] Suggestions don't repeat in consecutive messages
- [ ] "Continue your journey" label removed
- [ ] Markdown renders properly (bullets, bold, code)
- [ ] Agent/Chat toggle switches modes
- [ ] Web search returns Canadian vendors
- [ ] Image generation works for design mockups
- [ ] YouTube videos recommended for DIY tasks
- [ ] PDF downloads immediately when requested
- [ ] DIY plan creates immediately when requested
- [ ] Visual aids display correctly

---

## Next Steps

1. Start with Phase 1 (Quick Wins)
2. Test with user's exact conversation
3. Move to Phase 2 (Core Features)
4. Iterate based on feedback

