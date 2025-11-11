# HomeView AI - New API Endpoints Usage Guide

This guide shows how to use the new Gemini Cookbook-based API endpoints in the frontend.

## 🎯 Quick Reference

| Feature | Endpoint | Use Case |
|---------|----------|----------|
| Object Detection | `POST /api/v1/design/analyze-bounding-boxes` | Identify furniture, measure placement |
| Segmentation | `POST /api/v1/design/analyze-segmentation` | Precise object selection for editing |
| Sequence Analysis | `POST /api/v1/design/analyze-sequence` | Before/after comparisons |
| DIY Instructions | `POST /api/v1/design/generate-diy-instructions` | Project planning guides |
| Video Analysis | `POST /api/v1/design/analyze-video` | YouTube tutorial extraction |
| Video Upload | `POST /api/v1/design/analyze-video-upload` | Analyze uploaded videos |

---

## 1. Bounding Box Object Detection

**Endpoint:** `POST /api/v1/design/analyze-bounding-boxes`

**Use Case:** Detect and locate objects in a room image with precise coordinates.

### Request

```typescript
interface BoundingBoxRequest {
  image_data_url: string;           // Base64 data URL
  objects_to_detect?: string[];     // Optional: specific objects
  room_hint?: string;               // Optional: "living room", "kitchen", etc.
}
```

### Response

```typescript
interface BoundingBoxResponse {
  objects: Array<{
    label: string;
    confidence: number;             // 0.0 - 1.0
    bounding_box: {
      y_min: number;                // Normalized 0-1000
      x_min: number;
      y_max: number;
      x_max: number;
    };
  }>;
  image_dimensions: {
    width: number;
    height: number;
  };
}
```

### Example Usage

```typescript
// In your React component
const detectObjects = async (imageDataUrl: string) => {
  const response = await fetch('/api/v1/design/analyze-bounding-boxes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_data_url: imageDataUrl,
      objects_to_detect: ['sofa', 'lamp', 'table'],
      room_hint: 'living room'
    })
  });
  
  const data = await response.json();
  
  // Convert normalized coordinates to pixels
  data.objects.forEach(obj => {
    const bbox = obj.bounding_box;
    const pixelBox = {
      x: (bbox.x_min / 1000) * data.image_dimensions.width,
      y: (bbox.y_min / 1000) * data.image_dimensions.height,
      width: ((bbox.x_max - bbox.x_min) / 1000) * data.image_dimensions.width,
      height: ((bbox.y_max - bbox.y_min) / 1000) * data.image_dimensions.height
    };
    
    // Draw bounding box on canvas
    drawBoundingBox(pixelBox, obj.label);
  });
};
```

---

## 2. Object Segmentation

**Endpoint:** `POST /api/v1/design/analyze-segmentation`

**Use Case:** Get pixel-precise masks for objects (experimental feature).

### Request

```typescript
interface SegmentationRequest {
  image_data_url: string;
  objects_to_segment?: string[];
  room_hint?: string;
}
```

### Response

```typescript
interface SegmentationResponse {
  segments: Array<{
    label: string;
    confidence: number;
    bounding_box: {
      y_min: number;
      x_min: number;
      y_max: number;
      x_max: number;
    };
    mask?: string;  // Base64 encoded PNG
  }>;
}
```

### Example Usage

```typescript
const segmentObjects = async (imageDataUrl: string) => {
  const response = await fetch('/api/v1/design/analyze-segmentation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_data_url: imageDataUrl,
      objects_to_segment: ['sofa', 'rug']
    })
  });
  
  const data = await response.json();
  
  // Display masks
  data.segments.forEach(seg => {
    if (seg.mask) {
      const maskImg = new Image();
      maskImg.src = `data:image/png;base64,${seg.mask}`;
      // Overlay mask on original image
    }
  });
};
```

---

## 3. Multi-Image Sequence Analysis

**Endpoint:** `POST /api/v1/design/analyze-sequence`

**Use Case:** Compare before/after, track progress, or analyze design variations.

### Request

```typescript
interface SequenceRequest {
  image_data_urls: string[];        // 2+ images in order
  sequence_type: 'transformation' | 'before_after' | 'progress' | 'variations';
  custom_prompt?: string;
}
```

### Response

```typescript
interface SequenceResponse {
  analysis: {
    // For before_after:
    changes_made?: string[];
    improvements?: string[];
    estimated_cost_range?: string;
    diy_feasibility?: 'low' | 'medium' | 'high';
    
    // For progress:
    stages?: Array<{ description: string; completion: number }>;
    current_stage?: string;
    estimated_completion?: number;
    
    // For variations:
    variations?: Array<{ style: string; pros: string[]; cons: string[] }>;
    best_option?: { index: number; reason: string };
  };
}
```

### Example Usage

```typescript
const compareBeforeAfter = async (beforeUrl: string, afterUrl: string) => {
  const response = await fetch('/api/v1/design/analyze-sequence', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_data_urls: [beforeUrl, afterUrl],
      sequence_type: 'before_after'
    })
  });
  
  const data = await response.json();
  
  // Display results
  console.log('Changes:', data.analysis.changes_made);
  console.log('Cost:', data.analysis.estimated_cost_range);
  console.log('DIY Feasibility:', data.analysis.diy_feasibility);
};
```

---

## 4. DIY Instructions Generation

**Endpoint:** `POST /api/v1/design/generate-diy-instructions`

**Use Case:** Generate step-by-step project guides with materials and tools.

### Request

```typescript
interface DIYRequest {
  project_description: string;
  reference_image_url?: string;     // Optional image
}
```

### Response

```typescript
interface DIYResponse {
  instructions: {
    title: string;
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    estimated_time: string;
    estimated_cost: string;
    materials: string[];
    tools: string[];
    steps: string[];
    safety_tips: string[];
    pro_tips: string[];
  };
}
```

### Example Usage

```typescript
const generateDIYGuide = async (project: string) => {
  const response = await fetch('/api/v1/design/generate-diy-instructions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_description: project
    })
  });
  
  const data = await response.json();
  const instructions = data.instructions;
  
  // Render in UI
  return (
    <div className="diy-guide">
      <h2>{instructions.title}</h2>
      <div className="meta">
        <span>Difficulty: {instructions.difficulty}</span>
        <span>Time: {instructions.estimated_time}</span>
        <span>Cost: {instructions.estimated_cost}</span>
      </div>
      
      <section>
        <h3>Materials</h3>
        <ul>
          {instructions.materials.map(m => <li key={m}>{m}</li>)}
        </ul>
      </section>
      
      <section>
        <h3>Steps</h3>
        <ol>
          {instructions.steps.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
      </section>
    </div>
  );
};
```

---

## 5. Video Analysis (YouTube)

**Endpoint:** `POST /api/v1/design/analyze-video`

**Use Case:** Extract instructions from YouTube DIY tutorials.

### Request

```typescript
interface VideoRequest {
  video_url: string;                // YouTube URL or video path
  analysis_type: 'summary' | 'search' | 'extract_text' | 'tutorial';
  custom_prompt?: string;
  fps?: number;                     // Default: 1
  start_offset_seconds?: number;
  end_offset_seconds?: number;
}
```

### Response

```typescript
interface VideoResponse {
  analysis: {
    raw_text: string;
    structured?: {
      // For tutorial type:
      steps?: Array<{ timestamp: string; instruction: string }>;
      materials?: string[];
      tools?: string[];
      safety_warnings?: string[];
      difficulty?: string;
    };
  };
}
```

### Example Usage

```typescript
const analyzeYouTubeTutorial = async (youtubeUrl: string) => {
  const response = await fetch('/api/v1/design/analyze-video', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_url: youtubeUrl,
      analysis_type: 'tutorial'
    })
  });
  
  const data = await response.json();
  
  // Display tutorial steps with timestamps
  if (data.analysis.structured?.steps) {
    data.analysis.structured.steps.forEach(step => {
      console.log(`[${step.timestamp}] ${step.instruction}`);
    });
  }
};
```

---

## 6. Video Upload Analysis

**Endpoint:** `POST /api/v1/design/analyze-video-upload`

**Use Case:** Analyze contractor work videos or user-uploaded tutorials.

### Request (Multipart Form)

```typescript
const formData = new FormData();
formData.append('file', videoFile);
formData.append('analysis_type', 'tutorial');
formData.append('custom_prompt', 'Extract renovation steps');
```

### Example Usage

```typescript
const analyzeUploadedVideo = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('analysis_type', 'tutorial');
  
  const response = await fetch('/api/v1/design/analyze-video-upload', {
    method: 'POST',
    body: formData  // No Content-Type header - browser sets it
  });
  
  const data = await response.json();
  return data.analysis;
};
```

---

## 🎨 UI Integration Examples

### Design Studio: Object Detection Overlay

```tsx
const ObjectDetectionOverlay = ({ imageUrl }: { imageUrl: string }) => {
  const [objects, setObjects] = useState([]);
  
  const detectObjects = async () => {
    const response = await fetch('/api/v1/design/analyze-bounding-boxes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data_url: imageUrl })
    });
    const data = await response.json();
    setObjects(data.objects);
  };
  
  return (
    <div className="relative">
      <img src={imageUrl} alt="Room" />
      {objects.map((obj, i) => (
        <div
          key={i}
          className="absolute border-2 border-blue-500"
          style={{
            left: `${(obj.bounding_box.x_min / 1000) * 100}%`,
            top: `${(obj.bounding_box.y_min / 1000) * 100}%`,
            width: `${((obj.bounding_box.x_max - obj.bounding_box.x_min) / 1000) * 100}%`,
            height: `${((obj.bounding_box.y_max - obj.bounding_box.y_min) / 1000) * 100}%`
          }}
        >
          <span className="bg-blue-500 text-white px-2 py-1 text-xs">
            {obj.label} ({(obj.confidence * 100).toFixed(0)}%)
          </span>
        </div>
      ))}
    </div>
  );
};
```

---

## 📝 Notes

- All image inputs should be base64 data URLs: `data:image/jpeg;base64,/9j/4AAQ...`
- Bounding box coordinates are normalized (0-1000) for easy scaling
- Video analysis may take 30-60 seconds for processing
- Segmentation masks are experimental and may not always be available

---

## 🚀 Next Steps

1. Add these endpoints to `homeview-frontend/lib/api/design.ts`
2. Create UI components for displaying results
3. Integrate into Design Studio workflow
4. Add loading states and error handling
5. Test with real user images and videos

See `GEMINI_COOKBOOK_IMPLEMENTATION.md` for complete technical documentation.

