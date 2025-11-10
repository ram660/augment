# Quick Test Guide - Universal Chat

## 🎯 Test Goal
Verify that the chat works universally for all personas and passes all test scenarios.

---

## ✅ Quick Test Checklist

### 1. PDF Export (CRITICAL)
**Test:** Send "create me pdf doc with cost breakdown"

**Expected:**
- ✅ AI says it CAN create PDFs
- ✅ AI offers to create DIY plan first if none exists
- ✅ "Export as PDF" action chip appears
- ❌ AI NEVER says "I am unable to create PDF documents"

**Pass/Fail:** ___________

---

### 2. Canvas Visibility
**Test A:** Send "Hello"
- ✅ Canvas should be HIDDEN (no canvas-worthy items yet)

**Test B:** Send "Create a DIY plan for painting my living room"
- ✅ Canvas should APPEAR (DIY plan is canvas-worthy)

**Pass/Fail:** ___________

---

### 3. Universal Actions (Not Persona-Locked)

#### Test with Persona = Contractor
**Test A:** Send "How do I install flooring myself?"
- ✅ "Create DIY Plan" chip should APPEAR (contractor wants DIY guidance for their own home)

**Test B:** Send "Should I hire someone for this?"
- ✅ "Get Contractor Quotes" chip should APPEAR (even though persona is contractor)

**Pass/Fail:** ___________

#### Test with Persona = Homeowner
**Test A:** Send "How much does it cost to paint a room?"
- ✅ "Get Detailed Cost Estimate" chip appears
- ✅ Both DIY and contractor options offered neutrally

**Pass/Fail:** ___________

#### Test with Persona = DIY Worker
**Test A:** Send "This is too complex, should I hire a pro?"
- ✅ "Get Contractor Quotes" chip should APPEAR (DIY worker can choose to hire help)

**Pass/Fail:** ___________

---

### 4. No Repetitive Questions
**Test:** 
1. Send "I want to paint my living room"
2. Note the suggested questions
3. Send "yes"
4. Check if same questions repeat

**Expected:**
- ✅ Questions should NOT repeat
- ✅ New, contextual questions should appear

**Pass/Fail:** ___________

---

### 5. Friendly Missing Info Prompts
**Test:** Trigger PDF export without a plan

**Expected:**
- ✅ Friendly message: "I can export a polished PDF for you. I don't see a DIY plan yet — would you like me to create one now and then export it?"
- ❌ NOT rigid: "I can run that, but I need: plan_to_export. Please provide these details."

**Pass/Fail:** ___________

---

### 6. Cost Estimate Flow
**Test:** Send "Estimated costs for painting your living room?"

**Expected:**
- ✅ "Get Detailed Cost Estimate" action chip appears
- ✅ Relevant questions about dimensions, materials appear
- ✅ Questions don't repeat if asked before
- ✅ Both DIY and contractor pathways offered

**Pass/Fail:** ___________

---

## 🚀 Full Test Scenario (End-to-End)

### Scenario: Contractor wants DIY guidance for their own home

1. **Set persona:** Contractor
2. **Send:** "I want to paint my own living room, 12x20"
3. **Expected:** 
   - DIY plan offered (even though persona is contractor)
   - Friendly, helpful response
   - Canvas hidden (no canvas items yet)
4. **Send:** "yes, create a step-by-step plan"
5. **Expected:**
   - DIY plan generated
   - Canvas appears (DIY plan is canvas-worthy)
   - "Export as PDF" chip appears
6. **Send:** "create me a pdf document"
7. **Expected:**
   - AI confirms it CAN create PDFs
   - PDF export action triggered
   - Download link provided
   - ❌ NEVER says "I cannot create PDF documents"

**Pass/Fail:** ___________

---

## 📊 Overall Test Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| PDF Export Works | ⬜ Pass / ⬜ Fail | |
| Canvas Visibility | ⬜ Pass / ⬜ Fail | |
| Universal Actions | ⬜ Pass / ⬜ Fail | |
| No Repetitive Questions | ⬜ Pass / ⬜ Fail | |
| Friendly Prompts | ⬜ Pass / ⬜ Fail | |
| Cost Estimate Flow | ⬜ Pass / ⬜ Fail | |
| End-to-End Scenario | ⬜ Pass / ⬜ Fail | |

---

## 🐛 If Tests Fail

### PDF Export Still Claims Inability
- Check backend logs for errors
- Verify system prompt includes CRITICAL instruction about PDF capability
- Check if intent classification is detecting "pdf" keywords

### Canvas Always Visible
- Check `ChatInterface.tsx` - should have conditional rendering based on `hasCanvasItems`
- Verify metadata contains images/designs/products/cost_estimate/diy_plan

### Actions Still Persona-Locked
- Check `backend/api/chat.py` - action suggestions should check user message keywords, not just persona
- Verify universal guidance in `chat_workflow.py`

### Questions Still Repeating
- Check `_has_recent_question()` helper in `backend/api/chat.py`
- Verify it's checking last 6 messages for duplicate questions

---

## 🎉 Success Criteria

**ALL of the following must be true:**

- ✅ PDF export works for all personas and never claims inability
- ✅ Canvas only appears when there are canvas-worthy items
- ✅ Actions appear based on user's QUESTIONS, not persona label
- ✅ Suggested questions don't repeat across consecutive messages
- ✅ Missing info prompts are friendly and conversational
- ✅ Both DIY and contractor pathways offered neutrally
- ✅ System responds universally to all users

**If all criteria met:** 🎊 **TESTS PASSED** 🎊

**If any criteria failed:** Review the specific test case and check the implementation notes in `TEST_SCENARIOS.md`

