# Gemini Cookbook Features Implementation

This document summarizes the advanced Gemini AI capabilities implemented in HomeView AI based on Google Gemini Cookbook examples.

## 📚 Source Notebooks Analyzed

1. **Spatial Understanding** - Bounding boxes, segmentation masks, 3D spatial reasoning
2. **Guess the Shape** - Multi-image sequence analysis and pattern recognition
3. **Market a Jet Backpack** - Structured content generation with TypedDict schemas
4. **Video Understanding** - Video frame analysis, YouTube integration, temporal understanding

---

## ✅ Implemented Features

### 1. Enhanced Spatial Analysis ⭐⭐⭐

#### Backend Methods (`backend/integrations/gemini/client.py`)

**`analyze_with_bounding_boxes()`** - Lines 440-520
- Detects objects in images with normalized bounding box coordinates
- Returns coordinates in format: `{y_min, x_min, y_max, x_max}` (0-1000 scale)
- Supports targeted detection (specific objects) or full scene analysis
- Includes confidence scores for each detected object

**`analyze_with_segmentation()`** - Lines 522-590
- Segments objects with pixel-precise masks
- Returns base64 encoded PNG masks for each segment
- Experimental feature - availability varies by region
- Perfect for precise object isolation and editing

#### API Endpoints (`backend/api/design.py`)

**`POST /api/v1/design/analyze-bounding-boxes`** - Lines 2910-2950
- Request: `{image_data_url, objects_to_detect?, room_hint?}`
- Response: `{objects: [{label, confidence, bounding_box}], image_dimensions}`
- Use case: Identify furniture placement, measure object sizes

**`POST /api/v1/design/analyze-segmentation`** - Lines 2970-3010
- Request: `{image_data_url, objects_to_segment?, room_hint?}`
- Response: `{segments: [{label, confidence, bounding_box, mask}]}`
- Use case: Precise object selection for editing, material replacement

---

### 2. Multi-Image Sequence Analysis ⭐⭐⭐

#### Backend Method

**`analyze_multi_image_sequence()`** - Lines 592-675
- Analyzes sequences of 2+ images to detect patterns and changes
- Supports 4 sequence types:
  - **transformation**: Track design changes across iterations
  - **before_after**: Compare renovation results
  - **progress**: Monitor construction/renovation stages
  - **variations**: Compare design alternatives

#### API Endpoint

**`POST /api/v1/design/analyze-sequence`** - Lines 3030-3065
- Request: `{image_data_urls: [url1, url2, ...], sequence_type, custom_prompt?}`
- Response: `{analysis: {changes, progression_quality, recommendations, ...}}`
- Use cases:
  - Before/after renovation comparisons
  - Design iteration tracking
  - Contractor progress monitoring
  - A/B testing design variations

---

### 3. Structured Content Generation ⭐⭐

#### Backend Methods

**`generate_structured_content()`** - Lines 1822-1890
- Enforces JSON schema using TypedDict classes
- Guarantees consistent response structure
- Supports multimodal generation (text + image)
- Uses `response_mime_type="application/json"` for strict formatting

**`generate_diy_instructions()`** - Lines 1892-1955
- Pre-built schema for DIY project instructions
- Returns structured data:
  ```python
  {
    "title": str,
    "difficulty": "beginner|intermediate|advanced",
    "estimated_time": str,
    "estimated_cost": str,
    "materials": [str],
    "tools": [str],
    "steps": [str],
    "safety_tips": [str],
    "pro_tips": [str]
  }
  ```

#### API Endpoint

**`POST /api/v1/design/generate-diy-instructions`** - Lines 3085-3115
- Request: `{project_description, reference_image_url?}`
- Response: `{instructions: {...}}`
- Use cases:
  - Generate step-by-step renovation guides
  - Create material shopping lists
  - Estimate project complexity and cost
  - Provide safety guidance

---

### 4. Video Analysis Capabilities ⭐⭐

#### Backend Methods

**`analyze_video()`** - Lines 1680-1780
- Analyzes local video files or YouTube URLs
- Supports File API upload for large videos
- Configurable parameters:
  - **fps**: Frames per second (default: 1, increase for fast-changing content)
  - **start_offset_seconds**: Clip start time
  - **end_offset_seconds**: Clip end time
- Analysis types:
  - **summary**: 3-5 sentence summary with timestamps
  - **search**: Scene-by-scene captions with timecodes
  - **extract_text**: OCR from video frames
  - **tutorial**: DIY instruction extraction

**`analyze_youtube_video()`** - Lines 1782-1800
- Simplified wrapper for YouTube URL analysis
- No download required - direct API integration
- Supports clipping intervals

#### API Endpoints

**`POST /api/v1/design/analyze-video`** - Lines 3135-3175
- Request: `{video_url, analysis_type, custom_prompt?, fps?, start_offset_seconds?, end_offset_seconds?}`
- Response: `{analysis: {raw_text, structured?}}`
- Supports both YouTube URLs and uploaded video paths

**`POST /api/v1/design/analyze-video-upload`** - Lines 3195-3240
- Multipart form upload for video files
- Temporary file handling with automatic cleanup
- Same analysis capabilities as URL-based endpoint

---

## 🎯 Use Cases in HomeView AI

### Design Studio Enhancements

1. **Precise Object Detection**
   - Identify all furniture and fixtures with bounding boxes
   - Calculate exact dimensions and placement
   - Generate material quantity estimates per object

2. **Before/After Comparisons**
   - Analyze transformation sequences
   - Highlight specific changes made
   - Rate improvement quality
   - Suggest further enhancements

3. **DIY Project Planning**
   - Generate complete renovation guides from descriptions
   - Extract instructions from tutorial videos
   - Create shopping lists with quantities
   - Estimate costs and difficulty

4. **Video Tutorial Integration**
   - Analyze YouTube DIY videos
   - Extract step-by-step instructions with timestamps
   - Identify tools and materials mentioned
   - Generate text summaries for quick reference

### Chat Workflow Integration

1. **Multi-Step Project Planning**
   - Use structured content generation for consistent project plans
   - Track progress with sequence analysis
   - Generate DIY instructions for each phase

2. **Contractor Documentation**
   - Analyze contractor work videos
   - Extract progress updates with timestamps
   - Compare before/after results
   - Verify work quality

---

## 🔧 Technical Implementation Details

### Key Technologies

- **Gemini 2.5 Flash Vision**: Image and video understanding
- **Gemini 2.5 Flash**: Text generation and structured output
- **File API**: Large video upload and processing
- **TypedDict**: Schema enforcement for structured responses

### Coordinate Systems

- **Bounding Boxes**: Normalized coordinates (0-1000 scale)
  - Format: `[y_min, x_min, y_max, x_min]`
  - Easy conversion to pixel coordinates: `pixel = (normalized / 1000) * image_dimension`

- **Segmentation Masks**: Base64 encoded PNG images
  - Dimensions match bounding box region
  - Binary mask: white = object, black = background

### Video Processing

- **FPS Selection**:
  - 1 FPS: Default, good for most content
  - 2-4 FPS: Moderate motion (room tours)
  - 8-24 FPS: Fast motion (time-lapses, action)

- **Clipping**: Reduces processing time and cost
  - Specify start/end in seconds
  - Useful for long videos with relevant segments

---

## 📊 Logging and Monitoring

All new methods include comprehensive logging:

```python
logger.info(f"[BoundingBoxes] Detected {len(objects)} objects")
logger.info(f"[Segmentation] Segmented {len(segments)} objects")
logger.info(f"[MultiImage] Analyzed {len(images)} images, type={sequence_type}")
logger.info(f"[Video] Analysis complete, type={analysis_type}")
logger.info(f"[DIY] Generated instructions for: {project_description[:50]}")
```

Error handling with detailed stack traces:
```python
logger.error(f"analyze_with_bounding_boxes failed: {e}", exc_info=True)
```

---

## 🚀 Next Steps

### Frontend Integration (Recommended)

1. **Design Studio UI**
   - Add "Detect Objects" button to show bounding boxes overlay
   - Add "Compare Variations" for multi-image analysis
   - Add "Generate DIY Guide" button for project planning

2. **Chat Integration**
   - Enable video URL input for tutorial analysis
   - Show structured DIY instructions in chat responses
   - Display before/after comparisons inline

3. **Communities Tab**
   - Allow users to share before/after sequences
   - Display DIY instructions for popular projects
   - Embed analyzed tutorial videos

### Additional Enhancements

1. **Cost Estimation**
   - Integrate with product grounding for accurate pricing
   - Add regional price variations (CAD for Vancouver)
   - Include labor cost estimates

2. **3D Spatial Understanding**
   - Estimate room depth and perspective
   - Generate 3D bounding boxes
   - Calculate volume for material quantities

3. **Real-time Video Analysis**
   - Stream analysis for live contractor feeds
   - Progress tracking dashboards
   - Automated quality checks

---

## 📖 References

- [Gemini Spatial Understanding](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Spatial_understanding.ipynb)
- [Multi-Image Reasoning](https://github.com/google-gemini/cookbook/blob/main/examples/Guess_the_shape.ipynb)
- [Structured Output](https://github.com/google-gemini/cookbook/blob/main/examples/Market_a_Jet_Backpack.ipynb)
- [Video Understanding](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Video_understanding.ipynb)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)

---

**Implementation Date**: 2025-11-11  
**Status**: ✅ Backend Complete, Frontend Integration Pending

