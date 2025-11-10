# Phase 2.2: Image Management Testing Guide

## Prerequisites

- Backend server running on http://localhost:8000
- Swagger UI open at http://localhost:8000/docs
- Test user ID: `550e8400-e29b-41d4-a716-446655440000`
- Test images ready for upload

## Test Scenario 1: Image Reordering

### Step 1: Create Journey
**Endpoint**: `POST /api/v1/journey/start`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "kitchen_renovation"
}
```

**Save**: `journey_id` and first step's `id` from response

### Step 2: Upload 3 Images
**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images`

Upload 3 different images, one at a time:
- Image 1: kitchen_before_1.jpg
- Image 2: kitchen_before_2.jpg
- Image 3: kitchen_before_3.jpg

**Save**: All 3 `image_id` values

### Step 3: Get Images (Before Reorder)
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?step_id={step_id}`

**Expected**: Images in order 1, 2, 3 (display_order: 1, 2, 3)

### Step 4: Reorder Images
**Endpoint**: `PUT /api/v1/journey/{journey_id}/steps/{step_id}/images/reorder`

```json
{
  "image_ids": [
    "{image_3_id}",
    "{image_1_id}",
    "{image_2_id}"
  ]
}
```

**Expected**: Success response with reordered images

### Step 5: Verify Reorder
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?step_id={step_id}`

**Expected**: Images now in order 3, 1, 2 (display_order: 1, 2, 3)

---

## Test Scenario 2: Image Metadata Update

### Step 1: Upload Image
**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images`

Upload an image with:
- image_type: "user_upload"
- label: "Original kitchen"

**Save**: `image_id`

### Step 2: Update Metadata
**Endpoint**: `PUT /api/v1/journey/{journey_id}/images/{image_id}`

```json
{
  "label": "Kitchen - Before Renovation",
  "image_type": "before",
  "metadata": {
    "room": "kitchen",
    "condition": "needs_work",
    "notes": "Outdated cabinets and countertops"
  }
}
```

**Expected**: Updated image with new metadata

### Step 3: Verify Update
**Endpoint**: `GET /api/v1/journey/{journey_id}`

**Expected**: Image has updated label, type, and metadata

---

## Test Scenario 3: Single Image Deletion

### Step 1: Upload Image
**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images`

Upload a test image

**Save**: `image_id` and `file_path`

### Step 2: Delete Image
**Endpoint**: `DELETE /api/v1/journey/{journey_id}/images/{image_id}?delete_file=true`

**Expected**: Success message

### Step 3: Verify Deletion
**Endpoint**: `GET /api/v1/journey/{journey_id}/images`

**Expected**: Image not in list

**Manual Check**: Verify file deleted from filesystem at `file_path`

---

## Test Scenario 4: Bulk Image Upload

### Step 1: Bulk Upload
**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images/bulk`

**Form Data**:
- files: Select 5 images
- image_type: "inspiration"

**Expected**: Response with:
```json
{
  "success_count": 5,
  "failed_count": 0,
  "images": [...],
  "errors": []
}
```

### Step 2: Verify Upload
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?step_id={step_id}`

**Expected**: 5 images with display_order 1-5

---

## Test Scenario 5: Bulk Image Deletion

### Step 1: Upload 5 Images
Use bulk upload from Scenario 4

**Save**: All 5 `image_id` values

### Step 2: Bulk Delete 3 Images
**Endpoint**: `DELETE /api/v1/journey/{journey_id}/images/bulk?delete_files=true`

```json
{
  "image_ids": [
    "{image_1_id}",
    "{image_3_id}",
    "{image_5_id}"
  ]
}
```

**Expected**: Response with:
```json
{
  "success_count": 3,
  "failed_count": 0,
  "deleted_ids": [...],
  "errors": []
}
```

### Step 3: Verify Deletion
**Endpoint**: `GET /api/v1/journey/{journey_id}/images`

**Expected**: Only 2 images remain (images 2 and 4)

---

## Test Scenario 6: Image Gallery Filtering

### Setup: Create Journey with Multiple Images

1. Create journey
2. Upload 3 images to step 1 (type: "before")
3. Upload 3 images to step 2 (type: "inspiration")
4. Upload 2 images to step 3 (type: "after")

### Test 6.1: Filter by Step
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?step_id=initial_consultation`

**Expected**: Only images from step 1 (3 images)

### Test 6.2: Filter by Image Type
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?image_type=inspiration`

**Expected**: Only inspiration images (3 images)

### Test 6.3: Filter by Date Range
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?start_date=2025-11-09T00:00:00&end_date=2025-11-09T23:59:59`

**Expected**: Only images uploaded today

### Test 6.4: Pagination
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?limit=5&offset=0`

**Expected**: First 5 images

**Endpoint**: `GET /api/v1/journey/{journey_id}/images?limit=5&offset=5`

**Expected**: Next 3 images (total 8)

### Test 6.5: Combined Filters
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?step_id=initial_consultation&image_type=before&limit=2`

**Expected**: First 2 "before" images from step 1

---

## Test Scenario 7: Error Handling

### Test 7.1: Reorder with Invalid Image ID
**Endpoint**: `PUT /api/v1/journey/{journey_id}/steps/{step_id}/images/reorder`

```json
{
  "image_ids": [
    "invalid-uuid-123",
    "{valid_image_id}"
  ]
}
```

**Expected**: 404 error - "Image invalid-uuid-123 not found in step"

### Test 7.2: Update Non-Existent Image
**Endpoint**: `PUT /api/v1/journey/{journey_id}/images/00000000-0000-0000-0000-000000000000`

```json
{
  "label": "Test"
}
```

**Expected**: 404 error - "Image not found in journey"

### Test 7.3: Delete Already Deleted Image
**Endpoint**: `DELETE /api/v1/journey/{journey_id}/images/{deleted_image_id}`

**Expected**: 404 error - "Image not found in journey"

### Test 7.4: Bulk Upload with Invalid File
**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images/bulk`

**Form Data**:
- files: 1 image file + 1 text file

**Expected**: Response with:
```json
{
  "success_count": 1,
  "failed_count": 1,
  "images": [...],
  "errors": [
    {
      "filename": "document.txt",
      "error": "File must be an image"
    }
  ]
}
```

---

## Test Scenario 8: Display Order Auto-Assignment

### Step 1: Upload Images Without Specifying Order
Upload 5 images one by one to the same step

### Step 2: Verify Auto-Assignment
**Endpoint**: `GET /api/v1/journey/{journey_id}/images?step_id={step_id}`

**Expected**: Images have display_order 1, 2, 3, 4, 5 in chronological order

### Step 3: Delete Middle Image
Delete image with display_order 3

### Step 4: Upload New Image
Upload a new image

**Expected**: New image gets display_order 5 (not 3)

---

## Success Criteria

All tests should pass with:
- ✅ Correct HTTP status codes (200, 404, 500)
- ✅ Proper response formats matching schemas
- ✅ Data persistence across requests
- ✅ File system operations working correctly
- ✅ Error messages clear and helpful
- ✅ Display order maintained correctly
- ✅ Filtering and pagination working as expected

---

## Quick Test Commands (cURL)

### Create Journey
```bash
curl -X POST "http://localhost:8000/api/v1/journey/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"550e8400-e29b-41d4-a716-446655440000","template_id":"kitchen_renovation"}'
```

### Upload Image
```bash
curl -X POST "http://localhost:8000/api/v1/journey/{journey_id}/steps/{step_id}/images" \
  -F "file=@kitchen.jpg" \
  -F "image_type=before" \
  -F "label=Kitchen Before"
```

### Get Images
```bash
curl "http://localhost:8000/api/v1/journey/{journey_id}/images"
```

### Update Image
```bash
curl -X PUT "http://localhost:8000/api/v1/journey/{journey_id}/images/{image_id}" \
  -H "Content-Type: application/json" \
  -d '{"label":"Updated Label","image_type":"after"}'
```

### Delete Image
```bash
curl -X DELETE "http://localhost:8000/api/v1/journey/{journey_id}/images/{image_id}"
```

### Reorder Images
```bash
curl -X PUT "http://localhost:8000/api/v1/journey/{journey_id}/steps/{step_id}/images/reorder" \
  -H "Content-Type: application/json" \
  -d '{"image_ids":["id1","id2","id3"]}'
```

---

## Notes

- Replace `{journey_id}`, `{step_id}`, and `{image_id}` with actual UUIDs from responses
- Use Swagger UI for easier interactive testing
- Check backend logs for detailed error messages
- Verify file system changes manually when testing deletion
- Test with various image formats (JPG, PNG, WebP)
- Test with large images to verify file size handling

