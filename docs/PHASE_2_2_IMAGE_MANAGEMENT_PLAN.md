# Phase 2.2: Advanced Image Management Features

## 🎯 Overview
Add advanced image management capabilities to journey steps including:
- Image labeling and metadata updates
- Image reordering within steps
- Image deletion from journey
- Bulk image operations
- Image gallery view with filtering

## 📊 Current State (Phase 2.1 Complete)

### ✅ What's Working
1. **Image Upload**: Images automatically attach to current journey step during chat
2. **Image Storage**: Images stored in `uploads/journeys/{journey_id}/{step_id}/`
3. **Image Analysis**: Gemini AI analyzes images for styles, colors, materials
4. **Image Metadata**: Analysis results stored in `journey_images.metadata` JSONB field
5. **Image Retrieval**: Images included in journey API responses

### 🎯 What's Missing
1. **Update Image Labels**: Can't change image labels after upload
2. **Reorder Images**: No way to change image order within a step
3. **Delete Images**: No endpoint to remove images from journey
4. **Bulk Operations**: Can't upload/delete/update multiple images at once
5. **Image Filtering**: Can't filter images by type, step, or date range
6. **Image Gallery**: No dedicated endpoint for viewing all journey images

---

## 🚀 Phase 2.2 Implementation Tasks

### Task 1: Add Image Update Endpoint
**Endpoint**: `PUT /api/v1/journey/{journey_id}/images/{image_id}`

**Purpose**: Update image label, type, and metadata

**Request Model**:
```python
class UpdateImageRequest(BaseModel):
    """Request to update image metadata."""
    label: Optional[str] = None
    image_type: Optional[str] = None  # 'before', 'after', 'inspiration', 'user_upload'
    metadata: Optional[dict] = None
```

**Response**: Updated `ImageResponse`

**Implementation**:
1. Add `update_image()` method to `JourneyPersistenceService`
2. Add endpoint to `backend/api/journey.py`
3. Validate image belongs to journey
4. Update only provided fields

---

### Task 2: Add Image Reordering Endpoint
**Endpoint**: `PUT /api/v1/journey/{journey_id}/steps/{step_id}/images/reorder`

**Purpose**: Change the display order of images within a step

**Request Model**:
```python
class ReorderImagesRequest(BaseModel):
    """Request to reorder images within a step."""
    image_ids: List[str] = Field(..., description="Ordered list of image IDs")
```

**Response**: Success message with updated order

**Implementation**:
1. Add `display_order` column to `journey_images` table (migration needed)
2. Add `reorder_images()` method to `JourneyPersistenceService`
3. Add endpoint to `backend/api/journey.py`
4. Validate all image IDs belong to the step
5. Update display_order for each image

---

### Task 3: Add Image Deletion Endpoint
**Endpoint**: `DELETE /api/v1/journey/{journey_id}/images/{image_id}`

**Purpose**: Remove image from journey and delete file

**Response**: Success message

**Implementation**:
1. Add `delete_image()` method to `JourneyPersistenceService`
2. Add endpoint to `backend/api/journey.py`
3. Validate image belongs to journey
4. Delete file from filesystem
5. Delete database record
6. Handle errors gracefully (file not found, etc.)

---

### Task 4: Add Bulk Image Upload Endpoint
**Endpoint**: `POST /api/v1/journey/{journey_id}/steps/{step_id}/images/bulk`

**Purpose**: Upload multiple images to a step at once

**Request**: Multipart form data with multiple files

**Response**:
```python
class BulkImageUploadResponse(BaseModel):
    """Response for bulk image upload."""
    success_count: int
    failed_count: int
    images: List[ImageResponse]
    errors: List[dict]  # [{filename: str, error: str}]
```

**Implementation**:
1. Add `add_images_bulk()` method to `JourneyPersistenceService`
2. Add endpoint to `backend/api/journey.py`
3. Accept multiple files via `files: List[UploadFile]`
4. Process each file individually
5. Return success/failure summary

---

### Task 5: Add Image Gallery Endpoint with Filtering
**Endpoint**: `GET /api/v1/journey/{journey_id}/images`

**Purpose**: Get all images for a journey with filtering options

**Query Parameters**:
- `step_id`: Optional filter by step
- `image_type`: Optional filter by type ('before', 'after', etc.)
- `start_date`: Optional filter by creation date
- `end_date`: Optional filter by creation date
- `limit`: Max results (default 50)
- `offset`: Pagination offset

**Response**:
```python
class ImageGalleryResponse(BaseModel):
    """Response for image gallery."""
    journey_id: str
    total_images: int
    images: List[ImageResponse]
    grouped_by_step: Optional[Dict[str, List[ImageResponse]]]
```

**Implementation**:
1. Add `get_journey_images()` method to `JourneyPersistenceService`
2. Add endpoint to `backend/api/journey.py`
3. Support filtering by step, type, date range
4. Include step information with each image
5. Optional grouping by step

---

### Task 6: Add Bulk Image Delete Endpoint
**Endpoint**: `DELETE /api/v1/journey/{journey_id}/images/bulk`

**Purpose**: Delete multiple images at once

**Request Model**:
```python
class BulkDeleteImagesRequest(BaseModel):
    """Request to delete multiple images."""
    image_ids: List[str] = Field(..., description="List of image IDs to delete")
```

**Response**:
```python
class BulkDeleteResponse(BaseModel):
    """Response for bulk delete."""
    success_count: int
    failed_count: int
    deleted_ids: List[str]
    errors: List[dict]  # [{image_id: str, error: str}]
```

**Implementation**:
1. Add `delete_images_bulk()` method to `JourneyPersistenceService`
2. Add endpoint to `backend/api/journey.py`
3. Validate all images belong to journey
4. Delete files and database records
5. Return success/failure summary

---

## 🗄️ Database Changes

### Migration: Add display_order to journey_images

**File**: `backend/migrations/add_image_display_order.py`

```python
"""Add display_order to journey_images table."""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add display_order column
    op.add_column('journey_images', 
        sa.Column('display_order', sa.Integer(), nullable=True)
    )
    
    # Set default display_order based on created_at
    op.execute("""
        UPDATE journey_images
        SET display_order = subquery.row_num
        FROM (
            SELECT id, 
                   ROW_NUMBER() OVER (PARTITION BY step_id ORDER BY created_at) as row_num
            FROM journey_images
        ) AS subquery
        WHERE journey_images.id = subquery.id
    """)
    
    # Make display_order non-nullable
    op.alter_column('journey_images', 'display_order', nullable=False)
    
    # Add index for efficient ordering queries
    op.create_index('ix_journey_images_step_order', 
                    'journey_images', 
                    ['step_id', 'display_order'])

def downgrade():
    op.drop_index('ix_journey_images_step_order', table_name='journey_images')
    op.drop_column('journey_images', 'display_order')
```

---

## 📝 Service Layer Updates

### JourneyPersistenceService New Methods

**File**: `backend/services/journey_persistence_service.py`

```python
async def update_image(
    self,
    journey_id: str,
    image_id: str,
    label: Optional[str] = None,
    image_type: Optional[str] = None,
    metadata: Optional[dict] = None
) -> JourneyImage:
    """Update image metadata."""
    # Implementation details...

async def delete_image(
    self,
    journey_id: str,
    image_id: str
) -> bool:
    """Delete image from journey and filesystem."""
    # Implementation details...

async def reorder_images(
    self,
    journey_id: str,
    step_id: str,
    image_ids: List[str]
) -> List[JourneyImage]:
    """Reorder images within a step."""
    # Implementation details...

async def add_images_bulk(
    self,
    journey_id: str,
    step_id: str,
    files: List[UploadFile]
) -> Tuple[List[JourneyImage], List[dict]]:
    """Upload multiple images at once."""
    # Implementation details...

async def delete_images_bulk(
    self,
    journey_id: str,
    image_ids: List[str]
) -> Tuple[List[str], List[dict]]:
    """Delete multiple images at once."""
    # Implementation details...

async def get_journey_images(
    self,
    journey_id: str,
    step_id: Optional[str] = None,
    image_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> List[JourneyImage]:
    """Get journey images with filtering."""
    # Implementation details...
```

---

## 🧪 Testing Strategy

### Unit Tests
**File**: `backend/tests/test_journey_image_management.py`

Test cases:
1. `test_update_image_label()` - Update image label
2. `test_update_image_type()` - Change image type
3. `test_update_image_metadata()` - Update metadata
4. `test_delete_image()` - Delete single image
5. `test_reorder_images()` - Change image order
6. `test_bulk_upload_images()` - Upload multiple images
7. `test_bulk_delete_images()` - Delete multiple images
8. `test_get_journey_images_filtered()` - Filter images by step/type/date
9. `test_image_not_found()` - Handle missing images
10. `test_unauthorized_image_access()` - Validate ownership

### Integration Tests
**File**: `backend/tests/test_journey_image_api.py`

Test full API endpoints with real database and file operations.

---

## 📋 Implementation Order

1. **Database Migration** (5 min)
   - Add `display_order` column
   - Run migration

2. **Service Layer** (30 min)
   - Implement all 6 new methods in `JourneyPersistenceService`

3. **API Endpoints** (30 min)
   - Add 6 new endpoints to `backend/api/journey.py`

4. **Unit Tests** (20 min)
   - Write tests for service methods

5. **Integration Tests** (20 min)
   - Write tests for API endpoints

6. **Documentation** (10 min)
   - Update API docs
   - Add usage examples

**Total Estimated Time**: ~2 hours

---

## ✅ Success Criteria

- [ ] Can update image labels via API
- [ ] Can reorder images within a step
- [ ] Can delete single image
- [ ] Can upload multiple images at once
- [ ] Can delete multiple images at once
- [ ] Can filter images by step, type, date
- [ ] All tests passing
- [ ] API documentation updated

---

## 🔄 Next Steps After Phase 2.2

**Phase 2.3: Document Upload Support**
- PDF quotes attached to journey
- Document parsing and extraction
- Cost tracking from documents

**Phase 2.4: Web Search Integration**
- Search results saved to journey
- Product recommendations linked to steps
- Cost estimates from web data

