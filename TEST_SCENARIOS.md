# Test Scenarios for Universal Chat (All Personas)

## Test Philosophy
The chat is now **universal and persona-agnostic**. It responds based on the user's actual questions and needs, not their persona label.

## Test Setup
- **Personas to Test:** Homeowner, DIY Worker, Contractor
- **Expected Universal Behavior:**
  - Canvas only appears when there are canvas-worthy items (images, designs, products, cost estimates, DIY plans)
  - Action chips appear based on user's questions and intent, not persona label
  - PDF export works for all personas and never claims inability
  - Suggested questions don't repeat across consecutive messages
  - Both DIY and contractor pathways offered neutrally unless user chooses one

---

## Test Case 1: PDF Export Request (Primary Issue)

### Steps:
1. Start fresh conversation with persona=contractor
2. Send: "Create a DIY plan for painting my living room, 12x20"
3. Wait for response
4. Send: "yes create me pdf doc with cost breakdown"

### Expected Results:
- ✅ AI should acknowledge it CAN create PDFs
- ✅ AI should either:
  - Create the PDF immediately if a DIY plan exists, OR
  - Offer to create a DIY plan first, then export it
- ❌ AI should NEVER say "I am unable to create PDF documents directly"
- ✅ "Export as PDF" action chip should appear

### Current Issue (Before Fix):
- AI incorrectly states: "I can provide you with a cost breakdown in this chat. However, I am unable to create PDF documents directly."

---

## Test Case 2: Canvas Visibility

### Steps:
1. Start fresh conversation
2. Send: "Hello"
3. Verify canvas is NOT visible
4. Send: "Create a DIY plan for painting my living room"
5. Wait for response with DIY plan metadata
6. Verify canvas IS now visible

### Expected Results:
- ✅ Canvas hidden when no canvas-worthy items exist
- ✅ Canvas appears when messages contain: images, designs, products, cost_estimate, or diy_plan metadata

---

## Test Case 3: Universal Actions Based on Intent (Not Persona)

### Steps:
1. Start conversation with persona=contractor
2. Send: "I want to paint my living room"
3. Check suggested actions
4. Send: "How do I do this myself?"
5. Check if DIY plan chip appears
6. Send: "Should I hire someone for this?"
7. Check if contractor quotes chip appears

### Expected Results:
- ✅ Actions appear based on what user ASKS, not their persona label
- ✅ When user asks "how do I do this myself" → "Create DIY Plan" chip appears (even for contractor persona)
- ✅ When user asks "should I hire someone" → "Get Contractor Quotes" chip appears (even for contractor persona)
- ✅ When user asks about costs → "Get Detailed Cost Estimate" chip appears
- ✅ Generic questions → both pathways offered neutrally

### Key Principle:
The chat is universal. A contractor might want DIY guidance for their own home. A homeowner might want contractor quotes. Respond to what they ASK, not what their label says.

---

## Test Case 4: No Repetitive Suggested Questions

### Steps:
1. Start conversation
2. Send: "I want to paint my living room"
3. Note the suggested questions
4. Send: "yes"
5. Check if the same questions repeat

### Expected Results:
- ✅ Suggested questions should NOT repeat across consecutive messages
- ✅ Questions should be context-aware and progress the conversation
- ✅ If all intent-specific questions were recently asked, fallback questions should be used (but also filtered)

### Current Issue (Before Fix):
- Same 4 questions repeat on every message:
  - "Which room or area are we focusing on?"
  - "What are the dimensions and current materials?"
  - "What is your budget and timeline?"
  - "Do you prefer DIY plan or contractor quotes?"

---

## Test Case 5: Friendly Missing Info Prompts

### Steps:
1. Start conversation
2. Trigger an action that requires missing info (e.g., export PDF without a plan)

### Expected Results:
- ✅ Prompt should be conversational and helpful
- ✅ Should offer to create the missing prerequisite (e.g., "Would you like me to create a DIY plan first?")
- ❌ Should NOT use rigid format: "I can run that, but I need: X. Please provide these details."

### Example Good Response:
"I can export a polished PDF for you. I don't see a DIY plan yet — would you like me to create one now and then export it?"

### Example Bad Response (Before Fix):
"I can run that, but I need: plan_to_export. Please provide these details."

---

## Test Case 6: Cost Estimate Flow

### Steps:
1. Send: "Estimated costs for painting your living room?"
2. Wait for response
3. Check suggested actions and questions

### Expected Results:
- ✅ "Get Detailed Cost Estimate" action chip should appear
- ✅ Relevant questions about dimensions, materials, budget should appear
- ✅ Questions should not repeat if asked in previous messages
- ✅ For contractor persona, no "Get Contractor Quotes" chip

---

## Test Case 7: Universal Chat for All Personas

### Steps:
1. Test with persona=homeowner:
   - Send: "How much to paint my living room?"
   - Expected: Cost estimate chip + both DIY and contractor options offered
2. Test with persona=diy_worker:
   - Send: "Should I hire a contractor for this?"
   - Expected: Contractor quotes chip appears (even though persona is DIY worker)
3. Test with persona=contractor:
   - Send: "How do I install this flooring myself?"
   - Expected: DIY plan chip appears (contractor might want to DIY their own home)

### Expected Results:
- ✅ All personas get relevant actions based on their QUESTIONS
- ✅ No persona is locked into a single pathway
- ✅ System responds universally and adapts to user needs
- ✅ Both DIY and contractor pathways offered neutrally

---

## Verification Checklist

After implementing fixes, verify:

- [ ] PDF export never claims inability (for ANY persona)
- [ ] Canvas only appears when needed (images, designs, products, estimates, plans)
- [ ] Actions appear based on user's QUESTIONS, not persona label
- [ ] Suggested questions don't repeat across consecutive messages
- [ ] Missing info prompts are friendly and conversational
- [ ] System prompt explicitly states PDF export capability
- [ ] Intent classification detects PDF-related keywords (pdf, export, document, download, printable, print)
- [ ] Universal guidance: responds to what user ASKS, not what their persona label says
- [ ] Both DIY and contractor pathways offered neutrally unless user chooses one

---

## Implementation Summary

### Files Modified:
1. `backend/api/chat.py`
   - Enhanced `_ask_for()` helper with context-aware, friendly messages
   - Added `_has_recent_action()` to avoid repeating action chips
   - Added `_has_recent_question()` to avoid repeating questions
   - **Made action suggestions universal:** Actions now based on user's questions/intent, not persona label
   - **Keyword detection:** Checks user message for keywords like "diy", "contractor", "hire", "myself" to suggest relevant actions
   - Broadened PDF intent detection keywords
   - Added PDF export action chip when intent is "pdf_request"

2. `backend/workflows/chat_workflow.py`
   - Updated system prompt to explicitly state PDF export capability
   - Added CRITICAL instruction: "You CAN create and export PDFs. Never say 'I cannot create PDF documents'"
   - **Replaced persona-specific guidance with universal guidance:** System now responds based on user's questions, not persona label
   - Instructs AI to offer BOTH DIY and contractor pathways neutrally unless user chooses one
   - Adapts tone and detail to match what user is asking for

3. `homeview-frontend/components/chat/ChatInterface.tsx`
   - Canvas now conditionally renders only when messages contain canvas-worthy items
   - Checks for: images, designs, products, cost_estimate, diy_plan metadata
   - Hidden by default; appears only when needed

