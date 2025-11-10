# Design Studio API Reference

## Base URL
```
/api/v1/design
```

All endpoints are prefixed with `/api/v1/design`.

---

## 🎨 Paint Transformations

### Transform Paint
**Endpoint**: `POST /transform-paint`

Transform wall paint color while preserving everything else.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "target_color": "soft gray",
  "target_finish": "matte",
  "walls_only": true,
  "preserve_trim": true,
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required): ID of the room image to transform
- `target_color` (string, required): Target wall color (e.g., 'soft gray', '#F5F5DC')
- `target_finish` (string, default: "matte"): Paint finish (matte, eggshell, satin, semi-gloss, gloss)
- `walls_only` (boolean, default: true): If true, only change walls (not ceiling)
- `preserve_trim` (boolean, default: true): If true, keep trim/molding original color
- `num_variations` (integer, 1-4, default: 4): Number of variations to generate

**Response**:
```json
{
  "success": true,
  "message": "Successfully generated 4 paint transformation variations",
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

---

## 🪵 Flooring Transformations

### Transform Flooring
**Endpoint**: `POST /transform-flooring`

Replace flooring material and style while keeping everything else intact.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "target_material": "hardwood",
  "target_style": "wide plank oak",
  "target_color": "natural",
  "preserve_rugs": true,
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required): ID of the room image
- `target_material` (string, required): Flooring material (hardwood, tile, carpet, vinyl, laminate)
- `target_style` (string, required): Style details (e.g., 'wide plank oak', 'herringbone pattern')
- `target_color` (string, optional): Optional color specification
- `preserve_rugs` (boolean, default: true): If true, keep area rugs unchanged
- `num_variations` (integer, 1-4, default: 4): Number of variations

**Response**: Same structure as paint transformation

---

## 🏠 Kitchen Transformations

### Transform Cabinets
**Endpoint**: `POST /transform-cabinets`

Update cabinet color and finish without changing layout.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "target_color": "white",
  "target_finish": "painted",
  "target_style": "shaker",
  "preserve_hardware": false,
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `target_color` (string, required): Desired cabinet color
- `target_finish` (string, default: "painted"): Finish type (painted, stained, natural wood, glazed)
- `target_style` (string, optional): Optional style (shaker, flat panel, raised panel)
- `preserve_hardware` (boolean, default: false): If true, keep existing hardware
- `num_variations` (integer, 1-4, default: 4)

---

### Transform Countertops
**Endpoint**: `POST /transform-countertops`

Replace countertop material and color.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "target_material": "quartz",
  "target_color": "white with gray veining",
  "target_pattern": "veined",
  "edge_profile": "standard",
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `target_material` (string, required): Material (granite, quartz, marble, butcher block, laminate, concrete)
- `target_color` (string, required): Color specification
- `target_pattern` (string, optional): Optional pattern (veined, speckled, solid)
- `edge_profile` (string, default: "standard"): Edge style (standard, beveled, bullnose, waterfall)
- `num_variations` (integer, 1-4, default: 4)

---

### Transform Backsplash
**Endpoint**: `POST /transform-backsplash`

Update backsplash tile and pattern.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "target_material": "subway tile",
  "target_pattern": "subway",
  "target_color": "white",
  "grout_color": "gray",
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `target_material` (string, required): Material (ceramic tile, glass tile, subway tile, mosaic, stone)
- `target_pattern` (string, required): Pattern/layout (subway, herringbone, stacked, mosaic)
- `target_color` (string, required): Tile color
- `grout_color` (string, optional): Optional grout color
- `num_variations` (integer, 1-4, default: 4)

---

## 💡 Lighting Transformations

### Transform Lighting
**Endpoint**: `POST /transform-lighting`

Update light fixtures and adjust room ambiance.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "target_fixture_style": "modern",
  "target_finish": "brushed nickel",
  "adjust_ambiance": "warmer",
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `target_fixture_style` (string, required): Fixture style (modern, traditional, industrial, farmhouse)
- `target_finish` (string, required): Finish (brushed nickel, oil-rubbed bronze, chrome, brass, black)
- `adjust_ambiance` (string, optional): Optional ambiance (warmer, cooler, brighter, dimmer)
- `num_variations` (integer, 1-4, default: 4)

---

## 🛋️ Furniture Transformations

### Transform Furniture
**Endpoint**: `POST /transform-furniture`

Add, remove, or replace furniture.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "action": "add",
  "furniture_description": "modern gray sectional sofa",
  "placement": "against the wall",
  "num_variations": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `action` (string, required): Action (add, remove, replace)
- `furniture_description` (string, required): Description of furniture item
- `placement` (string, optional): Optional placement description
- `num_variations` (integer, 1-4, default: 4)

---

## 🏡 Virtual Staging & Unstaging

### Virtual Staging (Digital Twin)
**Endpoint**: `POST /virtual-staging`

Add furniture and decor to empty or sparsely furnished rooms.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "style_preset": "Modern",
  "style_prompt": "warm tones with natural materials",
  "furniture_density": "medium",
  "lock_envelope": true,
  "num_variations": 2
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `style_preset` (string, optional): Style preset (Modern, Scandinavian, Traditional, Farmhouse, Industrial, Coastal, Bohemian, Minimal)
- `style_prompt` (string, optional): Custom style cues or theme
- `furniture_density` (string, default: "medium"): Amount of furniture (light, medium, full)
- `lock_envelope` (boolean, default: true): Preserve floors/walls/ceilings/windows/doors exactly
- `num_variations` (integer, 1-4, default: 2)

---

### Virtual Staging (Upload)
**Endpoint**: `POST /virtual-staging-upload`

Virtual staging for uploaded images (no digital twin required).

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "style_preset": "Modern",
  "style_prompt": "warm tones",
  "furniture_density": "medium",
  "lock_envelope": true,
  "num_variations": 2,
  "enable_grounding": true
}
```

**Parameters**: Same as above, plus:
- `image_data_url` (string, required): Base64 data URL of the image
- `enable_grounding` (boolean, default: false): If true, suggest products using Google Search grounding

**Response**:
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

---

### Unstaging
**Endpoint**: `POST /unstaging`

Remove furniture and decor to see the empty space.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "strength": "medium",
  "num_variations": 2
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `strength` (string, default: "medium"): Removal strength (light, medium, full)
- `num_variations` (integer, 1-4, default: 2)

---

### Unstaging (Upload)
**Endpoint**: `POST /unstaging-upload`

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "strength": "medium",
  "num_variations": 2
}
```

---

## 🎯 Precision Editing Tools

### Masked Editing
**Endpoint**: `POST /edit-with-mask`

Make precise changes to specific areas using custom masks.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "mask_data_url": "data:image/png;base64,...",
  "operation": "replace",
  "replacement_prompt": "modern pendant light",
  "num_variations": 2
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `mask_data_url` (string, required): Base64 data URL for mask (white = editable)
- `operation` (string, required): Operation (remove, replace)
- `replacement_prompt` (string, optional): Description for replace operation
- `num_variations` (integer, 1-4, default: 2)

---

### Masked Editing (Upload)
**Endpoint**: `POST /edit-with-mask-upload`

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "mask_data_url": "data:image/png;base64,...",
  "operation": "replace",
  "replacement_prompt": "modern pendant light",
  "num_variations": 2
}
```

---

### Create Polygon Mask
**Endpoint**: `POST /mask-from-polygon`

Build a binary mask from polygon points (click-to-segment helper).

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "points": [[100, 200], [300, 200], [300, 400], [100, 400]]
}
```

**Parameters**:
- `room_image_id` (UUID, optional): If provided, infer width/height from this image
- `width` (integer, optional): Mask width in pixels (required if no room_image_id)
- `height` (integer, optional): Mask height in pixels (required if no room_image_id)
- `points` (array, required): List of [x,y] points defining a polygon

**Response**:
```json
{
  "mask_data_url": "data:image/png;base64,..."
}
```

---

### AI Segmentation
**Endpoint**: `POST /segment`

AI automatically detects and masks specific elements.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "segment_class": "floor",
  "points": [{"x": 100, "y": 200}],
  "num_masks": 1
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `segment_class` (string, required): Target class (floor, walls, cabinets, furniture, windows, doors)
- `points` (array, optional): Optional point hints as {'x':int,'y':int}
- `num_masks` (integer, 1-4, default: 1)

**Response**:
```json
{
  "mask_data_urls": [
    "data:image/png;base64,..."
  ]
}
```

---

### AI Segmentation (Upload)
**Endpoint**: `POST /segment-upload`

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "segment_class": "floor",
  "points": [{"x": 100, "y": 200}],
  "num_masks": 1
}
```

---

### Precise Edit (Orchestrated)
**Endpoint**: `POST /precise-edit`

Orchestrates polygon/segment → masked edit for precise changes.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "mode": "polygon",
  "points": [[100, 200], [300, 200], [300, 400], [100, 400]],
  "operation": "replace",
  "replacement_prompt": "hardwood flooring",
  "num_variations": 2
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `mode` (string, default: "polygon"): Mode (polygon, segment)
- `points` (array, optional): Polygon points [[x,y],...] for polygon mode
- `points_normalized` (array, optional): Normalized points [[x,y] in 0..1]
- `segment_class` (string, optional): Class for segmentation
- `operation` (string, required): Operation (remove, replace)
- `replacement_prompt` (string, optional): Description for replace
- `num_variations` (integer, 1-4, default: 2)

---

## ✨ Freeform Transformations

### Prompted Transformation
**Endpoint**: `POST /transform-prompted`

Transform based on natural language prompt.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "prompt": "modern farmhouse kitchen with white cabinets and butcher block counters",
  "enable_grounding": true,
  "num_variations": 2
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `prompt` (string, required): Natural language transformation description
- `enable_grounding` (boolean, default: false): Suggest real products
- `num_variations` (integer, 1-4, default: 2)

**Response**: Includes image_urls and optional products array

---

### Prompted Transformation (Upload)
**Endpoint**: `POST /transform-prompted-upload`

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "prompt": "cozy reading nook with built-in shelves",
  "enable_grounding": true,
  "num_variations": 2
}
```

---

## 📐 Advanced Tools

### Multi-Angle Views
**Endpoint**: `POST /multi-angle`

Generate different viewpoints of the same room.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "num_angles": 3,
  "yaw_degrees": 6,
  "pitch_degrees": 4
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `num_angles` (integer, 1-4, default: 3)
- `yaw_degrees` (integer, 1-15, default: 6): Horizontal rotation
- `pitch_degrees` (integer, 0-15, default: 4): Vertical tilt

---

### Multi-Angle Views (Upload)
**Endpoint**: `POST /multi-angle-upload`

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "num_angles": 3,
  "yaw_degrees": 6,
  "pitch_degrees": 4
}
```

---

### Image Enhancement
**Endpoint**: `POST /enhance`

Improve image quality and resolution.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "upscale_2x": true
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `upscale_2x` (boolean, default: true): Attempt 2x upscaling

---

### Image Enhancement (Upload)
**Endpoint**: `POST /enhance-upload`

**Request Body**:
```json
{
  "image_data_url": "data:image/jpeg;base64,...",
  "upscale_2x": true
}
```

---

## 🔍 Analysis & Ideas

### Room Analysis
**Endpoint**: `POST /analyze`

Get AI-powered design analysis and insights.

**Request Body**:
```json
{
  "room_image_id": "uuid"
}
```

**Response**:
```json
{
  "room_type": "living room",
  "style": "modern",
  "colors": ["gray", "white", "navy"],
  "materials": ["hardwood flooring", "fabric sofa"],
  "furniture": ["sectional sofa", "coffee table"],
  "lighting": "natural light from windows",
  "strengths": ["good natural light", "open layout"],
  "opportunities": ["add accent colors", "update lighting fixtures"]
}
```

---

### Transformation Ideas
**Endpoint**: `POST /ideas`

Get AI-generated transformation suggestions.

**Request Body**:
```json
{
  "room_image_id": "uuid",
  "max_ideas": 5
}
```

**Parameters**:
- `room_image_id` (UUID, required)
- `max_ideas` (integer, 1-6, default: 3)

**Response**:
```json
{
  "ideas_by_theme": {
    "Modern Refresh": [
      "Paint walls in soft gray",
      "Replace flooring with wide plank hardwood",
      "Add modern pendant lights"
    ],
    "Budget-Friendly": [
      "Paint cabinets white",
      "Update hardware to brushed nickel",
      "Add peel-and-stick backsplash"
    ]
  }
}
```

---

## 📊 Comparison Tools

### Compare Transformations
**Endpoint**: `POST /compare`

Compare original vs transformed images.

**Request Body**:
```json
{
  "original_image_id": "uuid",
  "transformed_image_id": "uuid"
}
```

**Response**: Returns comparison image with side-by-side or slider view

---

## 🔄 Common Response Patterns

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "transformation_id": "uuid",
  "image_urls": ["url1", "url2"],
  "products": []  // Optional
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

## 📝 Notes

1. **Image Data URLs**: Must be in format `data:image/jpeg;base64,...` or raw base64
2. **Mask Images**: Must be single-channel (L) PNG with white = editable area
3. **Rate Limiting**: Applied per IP address
4. **Processing Time**: Typically 5-15 seconds per transformation
5. **Product Grounding**: Only available for Canadian retailers when enabled

---

## 🚀 Quick Start Examples

See `DESIGN_STUDIO_FEATURES.md` for complete feature descriptions and use cases.

