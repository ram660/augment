# Visual Chat Enhancement - Testing Checklist ✅

## Quick Start

### 1. Start Backend (Already Running ✅)
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
**Status:** ✅ Running on http://localhost:8000

### 2. Start Frontend
```bash
cd homeview-frontend
npm run dev
```
**Expected:** Frontend runs on http://localhost:3000

---

## Test Scenarios

### Scenario 1: Text-to-Image Generation (No Upload)

#### Test Case 1.1: Modern Bathroom
- [ ] Open chat at http://localhost:3000
- [ ] Type: **"Show me modern bathroom designs with white tiles"**
- [ ] Press Enter
- [ ] **Expected Results:**
  - [ ] Bot responds with text
  - [ ] Section header: "🎨 AI-Generated Design Concepts"
  - [ ] 3 images display in grid
  - [ ] Images are 16:9 aspect ratio
  - [ ] Hover shows overlay with view/download buttons
  - [ ] "Open in Design Studio" button appears
  - [ ] Images load from http://localhost:8000/generated_images/...

#### Test Case 1.2: Rustic Kitchen
- [ ] Type: **"Visualize a rustic farmhouse kitchen"**
- [ ] Press Enter
- [ ] **Expected Results:**
  - [ ] Intent detected as `design_visualization`
  - [ ] Style extracted as "rustic"
  - [ ] 3 images generated
  - [ ] Style badge shows "Rustic" or similar

#### Test Case 1.3: Scandinavian Living Room
- [ ] Type: **"Create a scandinavian living room design"**
- [ ] Press Enter
- [ ] **Expected Results:**
  - [ ] Style extracted as "scandinavian"
  - [ ] Images show scandinavian style elements
  - [ ] All 3 images load successfully

---

### Scenario 2: Image Upload & Transformation

#### Test Case 2.1: Upload Room Photo
- [ ] Click 📷 image upload button (bottom left of input)
- [ ] Select a room photo from your computer
- [ ] **Expected Results:**
  - [ ] File picker opens
  - [ ] Only image files are selectable
  - [ ] After selection, thumbnail preview appears
  - [ ] Preview is 96×96px with rounded corners
  - [ ] File name displays at bottom of thumbnail
  - [ ] Upload button changes color (primary blue)

#### Test Case 2.2: Remove Uploaded Image
- [ ] Hover over uploaded image thumbnail
- [ ] **Expected Results:**
  - [ ] Red X button appears in top-right corner
  - [ ] Click X button
  - [ ] Thumbnail disappears
  - [ ] Upload button returns to gray

#### Test Case 2.3: Transform Uploaded Image
- [ ] Upload a room photo again
- [ ] Type: **"Transform this to modern style"**
- [ ] Press Enter
- [ ] **Expected Results:**
  - [ ] Message sends with image
  - [ ] User message shows with image preview
  - [ ] Bot receives image and message
  - [ ] Bot generates 3 transformed variations
  - [ ] Variations display in grid
  - [ ] Style badges show "Modern", "Contemporary", etc.

---

### Scenario 3: UI/UX Testing

#### Test Case 3.1: Responsive Design
- [ ] **Desktop (1920×1080):**
  - [ ] Images display in 3-column grid
  - [ ] Grid has proper spacing
  - [ ] Images maintain 16:9 aspect ratio
  
- [ ] **Tablet (768×1024):**
  - [ ] Images display in 2-column grid
  - [ ] Layout adjusts smoothly
  
- [ ] **Mobile (375×667):**
  - [ ] Images display in 1-column grid
  - [ ] Images are full width
  - [ ] Touch interactions work

#### Test Case 3.2: Hover Interactions
- [ ] Hover over generated image
- [ ] **Expected Results:**
  - [ ] Border changes from gray to primary blue
  - [ ] Shadow increases
  - [ ] Black overlay appears (40% opacity)
  - [ ] View and Download buttons fade in
  - [ ] Transition is smooth (200ms)

#### Test Case 3.3: Image Actions
- [ ] Click 🔍 View button
- [ ] **Expected Results:**
  - [ ] Image opens in new tab at full size
  
- [ ] Click ⬇️ Download button
- [ ] **Expected Results:**
  - [ ] Image downloads to computer
  - [ ] File name is preserved

#### Test Case 3.4: Design Studio Button
- [ ] Click "Open in Design Studio" button
- [ ] **Expected Results:**
  - [ ] Console logs: "Open in Design Studio" + images array
  - [ ] (Future: Navigate to Design Studio with images)

---

### Scenario 4: Edge Cases

#### Test Case 4.1: No Images Generated
- [ ] Type: **"What is the weather today?"**
- [ ] Press Enter
- [ ] **Expected Results:**
  - [ ] Bot responds with text only
  - [ ] No image section appears
  - [ ] No errors in console

#### Test Case 4.2: Large Image Upload
- [ ] Upload a very large image (>10MB)
- [ ] **Expected Results:**
  - [ ] Upload succeeds or shows appropriate error
  - [ ] Thumbnail generates correctly
  - [ ] Backend handles large file

#### Test Case 4.3: Multiple Messages
- [ ] Send 3 different design requests in a row
- [ ] **Expected Results:**
  - [ ] Each message generates 3 images
  - [ ] Images don't overlap
  - [ ] Scroll works correctly
  - [ ] Performance is acceptable

#### Test Case 4.4: Network Error
- [ ] Stop backend server
- [ ] Try to send message
- [ ] **Expected Results:**
  - [ ] Error message displays
  - [ ] UI doesn't break
  - [ ] User can retry after backend restarts

---

### Scenario 5: Performance Testing

#### Test Case 5.1: Image Generation Speed
- [ ] Type: **"Show me modern kitchen designs"**
- [ ] Start timer
- [ ] **Expected Results:**
  - [ ] Response within 5-10 seconds
  - [ ] Loading indicator shows during generation
  - [ ] Images load progressively

#### Test Case 5.2: Image Loading
- [ ] Check browser Network tab
- [ ] **Expected Results:**
  - [ ] Images load from http://localhost:8000/generated_images/
  - [ ] Images are optimized size (<500KB each)
  - [ ] No 404 errors

#### Test Case 5.3: Memory Usage
- [ ] Generate 10 sets of images
- [ ] Check browser memory usage
- [ ] **Expected Results:**
  - [ ] Memory usage is reasonable (<500MB)
  - [ ] No memory leaks
  - [ ] Images are garbage collected

---

## Browser Compatibility

### Desktop Browsers
- [ ] **Chrome** (latest)
  - [ ] All features work
  - [ ] Images display correctly
  - [ ] Hover effects work
  
- [ ] **Firefox** (latest)
  - [ ] All features work
  - [ ] Images display correctly
  
- [ ] **Safari** (latest)
  - [ ] All features work
  - [ ] Images display correctly
  
- [ ] **Edge** (latest)
  - [ ] All features work
  - [ ] Images display correctly

### Mobile Browsers
- [ ] **iOS Safari**
  - [ ] Touch interactions work
  - [ ] Image upload works
  - [ ] Responsive layout correct
  
- [ ] **Android Chrome**
  - [ ] Touch interactions work
  - [ ] Image upload works
  - [ ] Responsive layout correct

---

## API Testing

### Test Case: API Response Format
- [ ] Open browser DevTools → Network tab
- [ ] Send message: **"Show me modern bathroom designs"**
- [ ] Find POST request to `/api/v1/chat/message`
- [ ] Check response JSON
- [ ] **Expected Structure:**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "Here are 3 modern bathroom...",
  "intent": "design_visualization",
  "generated_images": [
    {
      "type": "generated",
      "url": "generated_images/generated_abc123_0.png",
      "caption": "AI-generated design concept",
      "prompt": "A beautiful modern bathroom...",
      "style": "modern"
    },
    // ... 2 more images
  ],
  "suggested_actions": [...],
  "metadata": {...}
}
```

### Test Case: Multipart Upload
- [ ] Upload image and send message
- [ ] Check Network tab
- [ ] **Expected:**
  - [ ] Content-Type: multipart/form-data
  - [ ] Form fields: message, image, conversation_id, mode
  - [ ] Image file is included in request

---

## Console Checks

### No Errors
- [ ] Open browser console (F12)
- [ ] Perform all test scenarios
- [ ] **Expected:**
  - [ ] No red errors
  - [ ] No warnings about missing images
  - [ ] No CORS errors
  - [ ] No 404 errors

### Expected Logs
- [ ] Console should show:
  - [ ] "Open in Design Studio" when button clicked
  - [ ] API request/response logs (if enabled)
  - [ ] No unexpected errors

---

## Accessibility Testing

### Keyboard Navigation
- [ ] Tab through chat interface
- [ ] **Expected:**
  - [ ] All buttons are focusable
  - [ ] Focus indicators are visible
  - [ ] Enter key sends message
  - [ ] Escape key closes modals (if any)

### Screen Reader
- [ ] Use screen reader (NVDA/JAWS/VoiceOver)
- [ ] **Expected:**
  - [ ] Images have alt text
  - [ ] Buttons have labels
  - [ ] Content is readable

---

## Final Checklist

### Pre-Launch
- [ ] All test scenarios pass
- [ ] No console errors
- [ ] Performance is acceptable
- [ ] Mobile responsive works
- [ ] Images load correctly
- [ ] Upload works end-to-end
- [ ] Documentation is complete

### Post-Launch Monitoring
- [ ] Track image generation success rate
- [ ] Monitor API response times
- [ ] Check error logs
- [ ] Gather user feedback
- [ ] Measure engagement metrics

---

## Known Issues

### Current
- None - all features implemented and working

### Future Enhancements
1. Implement "Open in Design Studio" functionality
2. Add image lightbox for full-screen viewing
3. Add before/after comparison slider
4. Add image zoom and pan
5. Add social sharing

---

## Quick Commands

### Start Backend
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### Start Frontend
```bash
cd homeview-frontend
npm run dev
```

### Run Backend Tests
```bash
python test_image_generation.py
```

### Check Backend Logs
```bash
# Logs appear in terminal where backend is running
# Look for: "Generating images for intent: design_visualization"
```

### Check Generated Images
```bash
# Images saved to:
ls generated_images/
```

---

## Success Criteria

✅ **Feature is ready to launch when:**
- [ ] All test scenarios pass
- [ ] No critical bugs
- [ ] Performance is acceptable (<10s for image generation)
- [ ] UI/UX is polished
- [ ] Documentation is complete
- [ ] Team has reviewed and approved

---

## Contact

**Questions or Issues?**
- Check `docs/VISUAL_CHAT_COMPLETE_SUMMARY.md` for overview
- Check `docs/IMPLEMENTATION_COMPLETE.md` for backend details
- Check `docs/FRONTEND_INTEGRATION_COMPLETE.md` for frontend details

**Ready to test? Let's go! 🚀**

