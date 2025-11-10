# Swagger UI Testing Guide - Journey APIs

## 🎯 Objective
Test the complete journey workflow including image uploads to verify Phase 1 and Phase 2.1 implementations.

## 📍 Access Swagger UI
**URL**: http://localhost:8000/docs

---

## 🧪 Test Sequence

### Test 1: Create a Kitchen Renovation Journey

**Endpoint**: `POST /api/v1/journey/start`

**Steps**:
1. Click on `POST /api/v1/journey/start`
2. Click "Try it out"
3. Paste this JSON in the Request body:

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "kitchen_renovation",
  "home_id": null,
  "conversation_id": null
}
```

4. Click "Execute"

**Expected Response** (200 OK):
```json
{
  "id": "some-uuid-here",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "kitchen_renovation",
  "status": "in_progress",
  "progress": 0,
  "steps": [
    {
      "id": "step-uuid-1",
      "step_id": "initial_consultation",
      "name": "Initial Consultation",
      "description": "...",
      "status": "in_progress",
      "step_number": 1,
      "progress": 0,
      "images": []
    },
    {
      "id": "step-uuid-2",
      "step_id": "design_planning",
      "name": "Design & Planning",
      ...
    }
    // ... more steps
  ],
  "created_at": "2025-11-10T...",
  "last_activity_at": "2025-11-10T..."
}
```

**✅ Success Criteria**:
- Status code: 200
- Journey has `id` field
- Status is "in_progress"
- Has 7 steps for kitchen_renovation
- First step status is "in_progress"

**📝 Important**: Copy the `id` field (journey ID) and the first step's `id` field - you'll need these for the next tests!

---

### Test 2: Get Journey Details

**Endpoint**: `GET /api/v1/journey/{journey_id}`

**Steps**:
1. Click on `GET /api/v1/journey/{journey_id}`
2. Click "Try it out"
3. Paste the journey ID from Test 1
4. Click "Execute"

**Expected Response** (200 OK):
- Same structure as Test 1
- Verify all steps are present
- Verify first step has empty `images` array

**✅ Success Criteria**:
- Status code: 200
- Journey data matches Test 1
- All steps visible

---

### Test 3: Upload Image to First Step

**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images`

**Steps**:
1. Click on `POST /api/v1/journey/{journey_id}/steps/{step_id}/images`
2. Click "Try it out"
3. Fill in the parameters:
   - `journey_id`: Paste journey ID from Test 1
   - `step_id`: Paste first step's ID from Test 1
   - `image_type`: Type "before"
   - `label`: Type "Kitchen before renovation"
4. Click "Choose File" and select any image from your computer (kitchen photo if you have one)
5. Click "Execute"

**Expected Response** (200 OK):
```json
{
  "id": "image-uuid",
  "journey_id": "your-journey-id",
  "step_id": "your-step-id",
  "filename": "your-image.jpg",
  "url": "/uploads/journeys/your-journey-id/your-step-id/unique-filename.jpg",
  "content_type": "image/jpeg",
  "file_size": 123456,
  "is_generated": false,
  "image_type": "before",
  "label": "Kitchen before renovation",
  "created_at": "2025-11-10T..."
}
```

**✅ Success Criteria**:
- Status code: 200
- Image has `id` and `url`
- `label` matches what you entered
- `image_type` is "before"
- `is_generated` is false

---

### Test 4: Upload Another Image (After Photo)

**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images`

**Steps**:
1. Same as Test 3, but:
   - `image_type`: Type "after"
   - `label`: Type "Kitchen design inspiration"
2. Upload a different image
3. Click "Execute"

**✅ Success Criteria**:
- Status code: 200
- Second image uploaded successfully

---

### Test 5: Get Journey with Images

**Endpoint**: `GET /api/v1/journey/{journey_id}`

**Steps**:
1. Click on `GET /api/v1/journey/{journey_id}`
2. Click "Try it out"
3. Paste the journey ID
4. Click "Execute"

**Expected Response** (200 OK):
```json
{
  "id": "your-journey-id",
  "steps": [
    {
      "id": "first-step-id",
      "step_id": "initial_consultation",
      "name": "Initial Consultation",
      "images": [
        {
          "id": "image-1-id",
          "filename": "...",
          "url": "/uploads/journeys/.../...",
          "label": "Kitchen before renovation",
          "image_type": "before"
        },
        {
          "id": "image-2-id",
          "filename": "...",
          "url": "/uploads/journeys/.../...",
          "label": "Kitchen design inspiration",
          "image_type": "after"
        }
      ]
    }
  ]
}
```

**✅ Success Criteria**:
- Status code: 200
- First step now has 2 images in `images` array
- Both images have correct labels and types
- Image URLs are present

---

### Test 6: Get All Journey Images

**Endpoint**: `GET /api/v1/journey/{journey_id}/images`

**Steps**:
1. Click on `GET /api/v1/journey/{journey_id}/images`
2. Click "Try it out"
3. Paste the journey ID
4. Click "Execute"

**Expected Response** (200 OK):
```json
{
  "journey_id": "your-journey-id",
  "total_images": 2,
  "images": [
    {
      "id": "image-1-id",
      "step_id": "first-step-id",
      "step_name": "Initial Consultation",
      "filename": "...",
      "url": "/uploads/journeys/.../...",
      "label": "Kitchen before renovation",
      "image_type": "before",
      "created_at": "..."
    },
    {
      "id": "image-2-id",
      "step_id": "first-step-id",
      "step_name": "Initial Consultation",
      "filename": "...",
      "url": "/uploads/journeys/.../...",
      "label": "Kitchen design inspiration",
      "image_type": "after",
      "created_at": "..."
    }
  ]
}
```

**✅ Success Criteria**:
- Status code: 200
- `total_images` is 2
- Both images listed with full details

---

### Test 7: Update Step Status

**Endpoint**: `PUT /api/v1/journey/{journey_id}/steps/{step_id}`

**Steps**:
1. Click on `PUT /api/v1/journey/{journey_id}/steps/{step_id}`
2. Click "Try it out"
3. Fill in:
   - `journey_id`: Your journey ID
   - `step_id`: First step ID
4. Paste this JSON:

```json
{
  "status": "completed",
  "progress": 100,
  "data": {
    "notes": "Initial consultation completed. Uploaded before and inspiration photos.",
    "completed_via": "manual_test"
  }
}
```

5. Click "Execute"

**Expected Response** (200 OK):
```json
{
  "id": "first-step-id",
  "status": "completed",
  "progress": 100,
  "data": {
    "notes": "...",
    "completed_via": "manual_test"
  }
}
```

**✅ Success Criteria**:
- Status code: 200
- Step status is now "completed"
- Progress is 100

---

### Test 8: List User Journeys

**Endpoint**: `GET /api/v1/journey/user/{user_id}`

**Steps**:
1. Click on `GET /api/v1/journey/user/{user_id}`
2. Click "Try it out"
3. Enter user_id: `550e8400-e29b-41d4-a716-446655440000`
4. (Optional) Add query parameter `status=in_progress`
5. Click "Execute"

**Expected Response** (200 OK):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_journeys": 1,
  "journeys": [
    {
      "id": "your-journey-id",
      "template_id": "kitchen_renovation",
      "status": "in_progress",
      "progress": 14.28,
      "current_step": "design_planning",
      "total_steps": 7,
      "completed_steps": 1,
      "created_at": "...",
      "last_activity_at": "..."
    }
  ]
}
```

**✅ Success Criteria**:
- Status code: 200
- Journey appears in list
- Progress is ~14% (1 of 7 steps completed)
- `completed_steps` is 1

---

## 🎉 **Bonus Test: Create Bathroom Renovation Journey**

Repeat Test 1 with:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "bathroom_upgrade"
}
```

Then verify Test 8 shows 2 journeys for this user!

---

## 📊 **Test Results Checklist**

Mark each test as you complete it:

- [ ] Test 1: Create Journey ✅
- [ ] Test 2: Get Journey Details ✅
- [ ] Test 3: Upload First Image ✅
- [ ] Test 4: Upload Second Image ✅
- [ ] Test 5: Get Journey with Images ✅
- [ ] Test 6: Get All Journey Images ✅
- [ ] Test 7: Update Step Status ✅
- [ ] Test 8: List User Journeys ✅
- [ ] Bonus: Create Second Journey ✅

---

## 🐛 **Troubleshooting**

### Issue: 404 Not Found
- **Solution**: Make sure backend server is running on http://localhost:8000
- Check terminal for errors

### Issue: 400 Bad Request
- **Solution**: Check JSON syntax
- Verify user_id is a valid UUID format
- Verify template_id is one of: `kitchen_renovation`, `bathroom_upgrade`, `diy_project`

### Issue: 500 Internal Server Error
- **Solution**: Check backend terminal logs
- Look for Python exceptions
- Verify database is initialized

### Issue: Image upload fails
- **Solution**: Verify file is an image (jpg, png, etc.)
- Check file size (should be < 10MB)
- Verify `uploads/journeys/` directory exists and is writable

---

## 📝 **Notes**

- All tests use the same user_id for consistency
- Images are stored in `uploads/journeys/{journey_id}/{step_id}/`
- Journey progress auto-calculates based on completed steps
- First step of each journey starts as "in_progress"
- You can upload multiple images to the same step

---

## ✅ **Success Indicators**

If all tests pass, you've successfully verified:

1. ✅ Journey creation works
2. ✅ Journey persistence works
3. ✅ Image upload works
4. ✅ Images attach to steps correctly
5. ✅ Journey retrieval includes images
6. ✅ Step status updates work
7. ✅ User journey listing works
8. ✅ Multi-journey support works

**Congratulations! Phase 1 and Phase 2.1 are fully functional!** 🎉

