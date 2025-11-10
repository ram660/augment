# Phase 2: Image Upload Integration with Journey Steps

## Overview
Integrate image upload functionality into the chat workflow so that when users upload images during a conversation, they are automatically attached to the current journey step.

## Current State Analysis

### ✅ Existing Infrastructure
1. **Image Upload Endpoints**:
   - `POST /api/v1/journey/{journey_id}/steps/{step_id}/images` - Upload image to specific step
   - `POST /api/v1/chat/stream-multipart` - Chat with file uploads (images, PDFs)

2. **Image Storage**:
   - Local file system: `uploads/chat/{conversation_id}/` for chat attachments
   - Local file system: `uploads/journeys/{journey_id}/{step_id}/` for journey images
   - GCS and Firebase storage clients available for cloud storage

3. **Image Analysis**:
   - Gemini AI analysis for design images (styles, colors, materials)
   - Analysis results stored in attachment metadata

4. **Journey Persistence**:
   - `JourneyPersistenceService.add_image()` - Add image to journey step
   - Images linked to steps via `journey_images` table
   - Support for labels, image_type, and metadata

### 🎯 What Needs to Be Done

#### Task 1: Update ChatWorkflow to Handle Image Attachments
**File**: `backend/workflows/chat_workflow.py`

**Changes**:
1. Accept `attachments` parameter in workflow state
2. In `_manage_journey()` node:
   - Check if user has active journey
   - If journey exists and attachments present, save images to current step
3. In `_save_conversation()` node:
   - Include attachment information in conversation metadata

**Implementation**:
```python
# In _manage_journey() after tracking active journey:
if active_journey and state.get("attachments"):
    attachments = state.get("attachments", [])
    image_attachments = [att for att in attachments if att.get("type") == "image"]
    
    if image_attachments and journey and current_step:
        for att in image_attachments:
            try:
                # Copy image from chat uploads to journey uploads
                # Add to journey step
                await self.journey_persistence_service.add_image(
                    journey_id=str(journey.id),
                    step_id=str(current_step.id),
                    filename=att["filename"],
                    file_path=att["path"],
                    url=att["url"],
                    content_type=att["content_type"],
                    file_size=att.get("file_size", 0),
                    is_generated=False,
                    image_type="user_upload",
                    label=att.get("label", "User uploaded image"),
                    metadata=att.get("analysis", {})
                )
            except Exception as e:
                logger.warning(f"Failed to attach image to journey step: {e}")
```

#### Task 2: Update Chat API to Pass Attachments to Workflow
**File**: `backend/api/chat.py`

**Changes**:
1. In `stream_message_multipart()`:
   - Pass `attachments` list to workflow state
   - Include file_size in attachment metadata

**Implementation**:
```python
# After saving attachments (around line 1896):
# Pass attachments to workflow
result = await chat_workflow.execute({
    "user_message": message,
    "user_id": str(current_user.id) if current_user else None,
    "conversation_id": str(conversation.id),
    "home_id": str(resolved_home_uuid) if resolved_home_uuid else None,
    "persona": conversation.persona,
    "scenario": conversation.scenario,
    "mode": "agent",
    "attachments": attachments,  # NEW: Pass attachments
    "image_urls": image_urls,
    "attachment_summaries": attachment_summaries,
})
```

#### Task 3: Add Image Display to Journey Response
**File**: `backend/api/journey.py`

**Changes**:
1. Update `JourneyResponse` model to include images in steps
2. Ensure images are eager-loaded when fetching journeys

**Already Done**: Images are already included in journey responses via `selectinload(JourneyStep.images)`

#### Task 4: Create Integration Tests
**File**: `backend/tests/test_chat_image_journey_integration.py` (NEW)

**Tests**:
1. `test_image_upload_attaches_to_active_journey_step`
2. `test_multiple_images_attach_to_same_step`
3. `test_image_upload_without_journey_saves_to_chat_only`
4. `test_image_analysis_metadata_saved_to_journey`

#### Task 5: Update Frontend to Display Journey Images
**File**: `homeview-frontend/src/components/journey/` (Future)

**Changes**:
1. Display images in journey timeline
2. Show image analysis results
3. Allow users to add labels to images
4. Gallery view for all journey images

## Implementation Order

### Phase 2.1: Backend Integration (Today)
1. ✅ Update `ChatWorkflow._manage_journey()` to handle attachments
2. ✅ Update `chat.py` to pass attachments to workflow
3. ✅ Create integration tests
4. ✅ Test via Swagger UI and Postman

### Phase 2.2: Image Management Features (This Week)
1. Add image labeling UI in chat
2. Add image reordering within steps
3. Add image deletion from journey
4. Add bulk image upload to journey

### Phase 2.3: Advanced Features (Next Week)
1. Image comparison (before/after)
2. Image annotations and markup
3. Image-based search within journey
4. Export journey with images to PDF

## Success Metrics

### Phase 2.1 Success Criteria:
- ✅ Images uploaded during chat automatically attach to current journey step
- ✅ Image analysis metadata saved to journey
- ✅ All integration tests passing
- ✅ Manual testing via Swagger UI successful

### Phase 2.2 Success Criteria:
- Users can label images during upload
- Users can reorder images within a step
- Users can delete images from journey
- Bulk upload works correctly

### Phase 2.3 Success Criteria:
- Before/after comparison works
- Image annotations persist correctly
- Image search returns relevant results
- PDF export includes all images

## API Examples

### Upload Image During Chat (Existing)
```bash
curl -X POST "http://localhost:8000/api/v1/chat/stream-multipart" \
  -F "message=Here's a photo of my current kitchen" \
  -F "files=@kitchen_before.jpg"
```

### Result After Integration
- Image saved to: `uploads/chat/{conversation_id}/kitchen_before.jpg`
- Image also linked to: Journey Step (if active journey exists)
- Image analysis stored in journey metadata
- User can see image in both chat history and journey timeline

### Upload Image Directly to Journey Step (Existing)
```bash
curl -X POST "http://localhost:8000/api/v1/journey/{journey_id}/steps/{step_id}/images" \
  -F "file=@kitchen_before.jpg" \
  -F "label=Before Photo" \
  -F "image_type=before"
```

## Database Schema (Already Exists)

```sql
CREATE TABLE journey_images (
    id UUID PRIMARY KEY,
    journey_id UUID REFERENCES journeys(id),
    step_id UUID REFERENCES journey_steps(id),
    filename VARCHAR(255),
    file_path TEXT,
    url TEXT,
    content_type VARCHAR(100),
    file_size INTEGER,
    is_generated BOOLEAN DEFAULT FALSE,
    image_type VARCHAR(50),  -- 'before', 'after', 'inspiration', 'user_upload'
    label VARCHAR(255),
    metadata JSONB,  -- Stores AI analysis results
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Next Steps After Phase 2.1

1. **Document Upload Support** (Phase 2.4)
   - PDF quotes attached to journey
   - Document parsing and extraction
   - Cost tracking from documents

2. **Web Search Integration** (Phase 2.5)
   - Search results saved to journey
   - Product recommendations linked to steps
   - Cost estimates from web data

3. **Frontend Development** (Phase 2.6)
   - Journey timeline UI
   - Image gallery component
   - Step progress visualization
   - Multimodal content display

## Notes

- Image upload is already working in chat
- Journey image storage is already implemented
- We just need to connect the two systems
- This is a relatively simple integration task
- Should take ~2-3 hours to complete Phase 2.1

