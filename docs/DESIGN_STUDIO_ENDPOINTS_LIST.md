# Design Studio - Complete Endpoints List

## 📋 All Available Endpoints (25 Total)

### Base URL: `/api/v1/design`

---

## 🎨 Core Transformations (Digital Twin Required)

### 1. Paint Transformation
```
POST /transform-paint
```
Transform wall paint color while preserving everything else.

### 2. Flooring Transformation
```
POST /transform-flooring
```
Replace flooring material and style while keeping everything else intact.

### 3. Cabinet Transformation
```
POST /transform-cabinets
```
Update cabinet color and finish without changing layout.

### 4. Countertop Transformation
```
POST /transform-countertops
```
Replace countertop material and color while preserving cabinets.

### 5. Backsplash Transformation
```
POST /transform-backsplash
```
Update backsplash tile and pattern without affecting other elements.

### 6. Custom Transformation
```
POST /transform-custom
```
Apply custom transformations with user-defined prompts.

### 7. Prompted Transformation
```
POST /transform-prompted
```
Transform based on natural language prompt with product grounding.

---

## 🏡 Staging & Furniture (Digital Twin Required)

### 8. Virtual Staging
```
POST /virtual-staging
```
Add furniture and decor to empty or sparsely furnished rooms.

### 9. Unstaging
```
POST /unstage
```
Remove furniture and decor to see the empty space.

---

## 🎯 Precision Editing (Digital Twin Required)

### 10. Masked Editing
```
POST /edit-with-mask
```
Make precise changes to specific areas using custom masks.

### 11. Create Polygon Mask
```
POST /mask-from-polygon
```
Build a binary mask from polygon points (click-to-segment helper).

### 12. AI Segmentation
```
POST /segment
```
AI automatically detects and masks specific elements.

### 13. Precise Edit (Orchestrated)
```
POST /precise-edit
```
Orchestrates polygon/segment → masked edit for precise changes.

---

## 📤 Upload-Based Transformations (No Digital Twin Required)

### 14. Prompted Transformation (Upload)
```
POST /transform-prompted-upload
```
Transform uploaded images based on natural language prompt.

### 15. Virtual Staging (Upload)
```
POST /virtual-staging-upload
```
Virtual staging for uploaded images with product grounding.

### 16. Unstaging (Upload)
```
POST /unstage-upload
```
Remove furniture from uploaded images.

### 17. Masked Editing (Upload)
```
POST /edit-with-mask-upload
```
Masked edit for uploaded images.

### 18. AI Segmentation (Upload)
```
POST /segment-upload
```
AI segmentation for uploaded images.

### 19. Multi-Angle Views (Upload)
```
POST /multi-angle-upload
```
Generate different viewpoints of uploaded room images.

### 20. Image Enhancement (Upload)
```
POST /enhance-upload
```
Enhance image quality (denoise, deblur, sharpen, 2x upscale).

---

## 🔍 Analysis & Information

### 21. Analyze Image (Digital Twin)
```
POST /analyze-image
```
Get AI-powered design analysis for images in digital twin.

### 22. Analyze Uploaded Image
```
POST /analyze-uploaded-image
```
Get AI-powered design analysis for uploaded images.

---

## 📊 History & Management

### 23. Get Transformation History
```
GET /transformations/{room_image_id}
```
Retrieve all transformations for a specific room image.

### 24. Get Transformation Details
```
GET /transformation/{transformation_id}
```
Get detailed information about a specific transformation.

### 25. Select Favorite Variation
```
POST /transformation/{transformation_image_id}/select
```
Mark a specific transformation variation as favorite.

---

## 📈 Endpoint Categories Summary

### By Type
- **Core Transformations**: 7 endpoints
- **Staging & Furniture**: 2 endpoints
- **Precision Editing**: 4 endpoints
- **Upload-Based**: 7 endpoints
- **Analysis**: 2 endpoints
- **Management**: 3 endpoints

### By Authentication
- **Digital Twin Required**: 13 endpoints
- **No Digital Twin (Upload)**: 7 endpoints
- **Management/Info**: 5 endpoints

### By Functionality
- **Image Generation**: 15 endpoints
- **Image Analysis**: 2 endpoints
- **Mask Creation**: 3 endpoints
- **History/Management**: 5 endpoints

---

## 🎯 Most Popular Endpoints

Based on expected usage:

1. **POST /transform-paint** - Most requested transformation
2. **POST /virtual-staging-upload** - Real estate agents
3. **POST /transform-prompted-upload** - Most flexible
4. **POST /transform-flooring** - Second most popular
5. **POST /transform-cabinets** - Kitchen renovations

---

## 🚀 Quick Start Examples

### Example 1: Paint Transformation
```bash
curl -X POST "http://localhost:8000/api/v1/design/transform-paint" \
  -H "Content-Type: application/json" \
  -d '{
    "room_image_id": "uuid-here",
    "target_color": "soft gray",
    "target_finish": "matte",
    "walls_only": true,
    "preserve_trim": true,
    "num_variations": 4
  }'
```

### Example 2: Virtual Staging (Upload)
```bash
curl -X POST "http://localhost:8000/api/v1/design/virtual-staging-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data_url": "data:image/jpeg;base64,...",
    "style_preset": "Modern",
    "furniture_density": "medium",
    "lock_envelope": true,
    "num_variations": 2,
    "enable_grounding": true
  }'
```

### Example 3: Freeform Prompt (Upload)
```bash
curl -X POST "http://localhost:8000/api/v1/design/transform-prompted-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data_url": "data:image/jpeg;base64,...",
    "prompt": "modern farmhouse kitchen with white cabinets and butcher block counters",
    "enable_grounding": true,
    "num_variations": 2
  }'
```

---

## 🔄 Typical Response Format

### Success Response
```json
{
  "success": true,
  "message": "Successfully generated 4 variations",
  "transformation_id": "uuid",
  "num_variations": 4,
  "transformation_type": "paint",
  "original_image_id": "uuid",
  "status": "completed",
  "image_urls": [
    "https://storage.googleapis.com/.../variation_1.jpg",
    "https://storage.googleapis.com/.../variation_2.jpg",
    "https://storage.googleapis.com/.../variation_3.jpg",
    "https://storage.googleapis.com/.../variation_4.jpg"
  ]
}
```

### With Product Grounding
```json
{
  "success": true,
  "image_urls": ["url1", "url2"],
  "products": [
    {
      "name": "Modern Gray Sectional",
      "brand": "Article",
      "price": "$1,299 CAD",
      "url": "https://...",
      "image_url": "https://...",
      "availability": "In stock - Canada"
    }
  ]
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information"
}
```

---

## ⚡ Performance Characteristics

### Processing Times
- **Paint/Flooring**: 5-10 seconds
- **Kitchen (Cabinets/Counters)**: 8-12 seconds
- **Virtual Staging**: 10-15 seconds
- **Freeform Prompts**: 10-20 seconds
- **Multi-Angle**: 15-25 seconds
- **Enhancement**: 5-10 seconds
- **Analysis**: 3-5 seconds

### Rate Limits
- **Per IP**: 100 requests per hour
- **Per User**: 500 requests per day
- **Burst**: 10 requests per minute

### Image Constraints
- **Max Upload Size**: 10 MB
- **Supported Formats**: JPEG, PNG, WebP
- **Recommended Resolution**: 1024x1024 to 2048x2048
- **Max Resolution**: 4096x4096

---

## 🎨 Transformation Type Codes

Used in `transformation_type` field:

- `paint` - Paint transformation
- `flooring` - Flooring transformation
- `cabinets` - Cabinet transformation
- `countertops` - Countertop transformation
- `backsplash` - Backsplash transformation
- `lighting` - Lighting transformation
- `furniture` - Furniture transformation
- `virtual_staging` - Virtual staging
- `unstaging` - Unstaging
- `masked_edit` - Masked editing
- `segment` - AI segmentation
- `precise_edit` - Precise editing
- `prompted` - Freeform prompt
- `custom` - Custom transformation
- `multi_angle` - Multi-angle views
- `enhance` - Image enhancement

---

## 🔐 Authentication

### Digital Twin Endpoints
Require authentication via JWT token:
```
Authorization: Bearer <jwt_token>
```

### Upload Endpoints
No authentication required (open access):
- All `-upload` endpoints
- Analysis endpoints
- Public transformations

---

## 📝 Notes

1. **Image Data URLs**: Must be in format `data:image/jpeg;base64,...` or raw base64
2. **Mask Images**: Must be single-channel (L) PNG with white = editable area
3. **UUIDs**: All IDs are UUID v4 format
4. **Variations**: Most endpoints support 1-4 variations (default varies by type)
5. **Product Grounding**: Only available for upload endpoints with `enable_grounding: true`
6. **Processing**: All transformations are asynchronous but return when complete

---

## 🚀 Next Steps

1. **Test Endpoints**: Use the examples above to test each endpoint
2. **Build UI**: Create components for each transformation type
3. **Integrate API**: Use the API client from `DESIGN_STUDIO_QUICK_REFERENCE.md`
4. **Add Analytics**: Track usage of each endpoint
5. **Optimize**: Monitor performance and optimize slow endpoints

---

## 📚 Related Documentation

- **API Reference**: `DESIGN_STUDIO_API_REFERENCE.md` - Full API specs
- **Features**: `DESIGN_STUDIO_FEATURES.md` - What each endpoint does
- **Implementation**: `DESIGN_STUDIO_IMPLEMENTATION.md` - How to build UI
- **Quick Reference**: `DESIGN_STUDIO_QUICK_REFERENCE.md` - Code snippets

---

**Complete endpoint list for HomeView AI Design Studio! 🎨**

