# Design Studio - Quick Reference Card

## 🎯 For Developers Building the UI

This is your quick reference for implementing Design Studio features. Copy-paste ready!

---

## 📋 All Available Endpoints

### Paint & Color
```typescript
POST /api/v1/design/transform-paint
{
  room_image_id: UUID,
  target_color: string,
  target_finish: "matte" | "eggshell" | "satin" | "semi-gloss" | "gloss",
  walls_only: boolean,
  preserve_trim: boolean,
  num_variations: 1-4
}
```

### Flooring
```typescript
POST /api/v1/design/transform-flooring
{
  room_image_id: UUID,
  target_material: "hardwood" | "tile" | "carpet" | "vinyl" | "laminate",
  target_style: string,
  target_color?: string,
  preserve_rugs: boolean,
  num_variations: 1-4
}
```

### Kitchen - Cabinets
```typescript
POST /api/v1/design/transform-cabinets
{
  room_image_id: UUID,
  target_color: string,
  target_finish: "painted" | "stained" | "natural wood" | "glazed",
  target_style?: "shaker" | "flat panel" | "raised panel",
  preserve_hardware: boolean,
  num_variations: 1-4
}
```

### Kitchen - Countertops
```typescript
POST /api/v1/design/transform-countertops
{
  room_image_id: UUID,
  target_material: "granite" | "quartz" | "marble" | "butcher block" | "laminate" | "concrete",
  target_color: string,
  target_pattern?: "veined" | "speckled" | "solid",
  edge_profile: "standard" | "beveled" | "bullnose" | "waterfall",
  num_variations: 1-4
}
```

### Kitchen - Backsplash
```typescript
POST /api/v1/design/transform-backsplash
{
  room_image_id: UUID,
  target_material: "ceramic tile" | "glass tile" | "subway tile" | "mosaic" | "stone",
  target_pattern: "subway" | "herringbone" | "stacked" | "mosaic",
  target_color: string,
  grout_color?: string,
  num_variations: 1-4
}
```

### Lighting
```typescript
POST /api/v1/design/transform-lighting
{
  room_image_id: UUID,
  target_fixture_style: "modern" | "traditional" | "industrial" | "farmhouse",
  target_finish: "brushed nickel" | "oil-rubbed bronze" | "chrome" | "brass" | "black",
  adjust_ambiance?: "warmer" | "cooler" | "brighter" | "dimmer",
  num_variations: 1-4
}
```

### Furniture
```typescript
POST /api/v1/design/transform-furniture
{
  room_image_id: UUID,
  action: "add" | "remove" | "replace",
  furniture_description: string,
  placement?: string,
  num_variations: 1-4
}
```

### Virtual Staging (Digital Twin)
```typescript
POST /api/v1/design/virtual-staging
{
  room_image_id: UUID,
  style_preset?: "Modern" | "Scandinavian" | "Traditional" | "Farmhouse" | "Industrial" | "Coastal" | "Bohemian" | "Minimal",
  style_prompt?: string,
  furniture_density: "light" | "medium" | "full",
  lock_envelope: boolean,
  num_variations: 1-4
}
```

### Virtual Staging (Upload)
```typescript
POST /api/v1/design/virtual-staging-upload
{
  image_data_url: string,  // "data:image/jpeg;base64,..."
  style_preset?: string,
  style_prompt?: string,
  furniture_density: "light" | "medium" | "full",
  lock_envelope: boolean,
  num_variations: 1-4,
  enable_grounding: boolean  // Get product suggestions
}
```

### Unstaging
```typescript
POST /api/v1/design/unstaging
{
  room_image_id: UUID,
  strength: "light" | "medium" | "full",
  num_variations: 1-4
}

POST /api/v1/design/unstaging-upload
{
  image_data_url: string,
  strength: "light" | "medium" | "full",
  num_variations: 1-4
}
```

### Masked Editing
```typescript
POST /api/v1/design/edit-with-mask
{
  room_image_id: UUID,
  mask_data_url: string,  // White = editable area
  operation: "remove" | "replace",
  replacement_prompt?: string,
  num_variations: 1-4
}

POST /api/v1/design/edit-with-mask-upload
{
  image_data_url: string,
  mask_data_url: string,
  operation: "remove" | "replace",
  replacement_prompt?: string,
  num_variations: 1-4
}
```

### Polygon Mask Creation
```typescript
POST /api/v1/design/mask-from-polygon
{
  room_image_id?: UUID,
  width?: number,
  height?: number,
  points: [[x, y], [x, y], ...]  // Polygon vertices
}
// Returns: { mask_data_url: string }
```

### AI Segmentation
```typescript
POST /api/v1/design/segment
{
  room_image_id: UUID,
  segment_class: "floor" | "walls" | "cabinets" | "furniture" | "windows" | "doors",
  points?: [{x: number, y: number}],
  num_masks: 1-4
}
// Returns: { mask_data_urls: string[] }

POST /api/v1/design/segment-upload
{
  image_data_url: string,
  segment_class: string,
  points?: [{x: number, y: number}],
  num_masks: 1-4
}
```

### Precise Edit (Orchestrated)
```typescript
POST /api/v1/design/precise-edit
{
  room_image_id: UUID,
  mode: "polygon" | "segment",
  points?: [[x, y], ...],
  points_normalized?: [[x, y], ...],  // 0..1 range
  segment_class?: string,
  operation: "remove" | "replace",
  replacement_prompt?: string,
  num_variations: 1-4
}
```

### Freeform Prompt
```typescript
POST /api/v1/design/transform-prompted
{
  room_image_id: UUID,
  prompt: string,
  enable_grounding: boolean,
  num_variations: 1-4
}

POST /api/v1/design/transform-prompted-upload
{
  image_data_url: string,
  prompt: string,
  enable_grounding: boolean,
  num_variations: 1-4
}
```

### Multi-Angle Views
```typescript
POST /api/v1/design/multi-angle
{
  room_image_id: UUID,
  num_angles: 1-4,
  yaw_degrees: 1-15,
  pitch_degrees: 0-15
}

POST /api/v1/design/multi-angle-upload
{
  image_data_url: string,
  num_angles: 1-4,
  yaw_degrees: 1-15,
  pitch_degrees: 0-15
}
```

### Image Enhancement
```typescript
POST /api/v1/design/enhance
{
  room_image_id: UUID,
  upscale_2x: boolean
}

POST /api/v1/design/enhance-upload
{
  image_data_url: string,
  upscale_2x: boolean
}
```

### Analysis & Ideas
```typescript
POST /api/v1/design/analyze
{
  room_image_id: UUID
}
// Returns: room analysis with colors, materials, furniture, etc.

POST /api/v1/design/ideas
{
  room_image_id: UUID,
  max_ideas: 1-6
}
// Returns: themed transformation ideas
```

---

## 🎨 UI Component Checklist

### ✅ Core Components
- [ ] DesignStudioMain.tsx
- [ ] ToolSelector.tsx
- [ ] ImageUploader.tsx
- [ ] ImageSelector.tsx (from digital twin)
- [ ] LoadingSpinner.tsx
- [ ] ErrorMessage.tsx
- [ ] Toast.tsx

### ✅ Transform Controls (12 components)
- [ ] PaintControls.tsx
- [ ] FlooringControls.tsx
- [ ] CabinetControls.tsx
- [ ] CountertopControls.tsx
- [ ] BacksplashControls.tsx
- [ ] LightingControls.tsx
- [ ] FurnitureControls.tsx
- [ ] StagingControls.tsx
- [ ] UnstagingControls.tsx
- [ ] MaskingControls.tsx
- [ ] PromptControls.tsx
- [ ] CommonControls.tsx

### ✅ Results & Products
- [ ] ResultsGallery.tsx
- [ ] ResultCard.tsx
- [ ] ComparisonView.tsx (before/after slider)
- [ ] ImageActions.tsx (download, share, save)
- [ ] ProductList.tsx
- [ ] ProductCard.tsx
- [ ] ProductFilters.tsx

### ✅ Utilities
- [ ] apiClient.ts
- [ ] imageUtils.ts
- [ ] types.ts

---

## 🔧 Common Code Snippets

### API Client Setup
```typescript
// src/utils/apiClient.ts
const API_BASE = '/api/v1/design';

export const designAPI = {
  transformPaint: async (roomImageId: string, params: PaintParams) => {
    const response = await fetch(`${API_BASE}/transform-paint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_image_id: roomImageId, ...params })
    });
    if (!response.ok) throw new Error('Transformation failed');
    return response.json();
  },
  
  // Add more methods...
};
```

### Image Upload to Base64
```typescript
// src/utils/imageUtils.ts
export const imageToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};
```

### Loading State Hook
```typescript
// src/hooks/useTransform.ts
export const useTransform = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<TransformResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const transform = async (endpoint: string, params: any) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await designAPI[endpoint](params);
      setResults(data.image_urls.map((url, i) => ({ url, index: i })));
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, results, error, transform };
};
```

### Color Picker Component
```typescript
// src/components/ColorPicker.tsx
export const ColorPicker: React.FC<{
  value: string;
  onChange: (color: string) => void;
}> = ({ value, onChange }) => {
  const popularColors = [
    { name: 'Soft Gray', hex: '#D3D3D3' },
    { name: 'Warm Beige', hex: '#F5F5DC' },
    { name: 'Navy Blue', hex: '#000080' },
    { name: 'Sage Green', hex: '#9DC183' },
    { name: 'Warm White', hex: '#FAF9F6' }
  ];

  return (
    <div className="color-picker">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Color name or hex"
      />
      <div className="color-swatches">
        {popularColors.map(color => (
          <button
            key={color.hex}
            style={{ backgroundColor: color.hex }}
            onClick={() => onChange(color.name)}
            title={color.name}
          />
        ))}
      </div>
    </div>
  );
};
```

### Results Gallery
```typescript
// src/components/ResultsGallery.tsx
export const ResultsGallery: React.FC<{
  results: string[];
  onSelect: (url: string) => void;
}> = ({ results, onSelect }) => {
  return (
    <div className="results-gallery">
      <h3>Results ({results.length} variations)</h3>
      <div className="results-grid">
        {results.map((url, index) => (
          <div key={index} className="result-card">
            <img src={url} alt={`Variation ${index + 1}`} />
            <div className="result-actions">
              <button onClick={() => onSelect(url)}>Select</button>
              <button onClick={() => downloadImage(url)}>Download</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 🎯 Tool Categories for UI

### Quick Tools (Most Popular)
1. Paint Walls
2. Change Flooring
3. Virtual Staging
4. Freeform Prompt

### Kitchen & Bath
1. Cabinets
2. Countertops
3. Backsplash
4. Fixtures

### Surfaces & Materials
1. Paint & Color
2. Flooring
3. Lighting
4. Materials

### Furniture & Decor
1. Add Furniture
2. Remove Furniture
3. Replace Furniture
4. Virtual Staging

### Precision Tools
1. Masked Editing
2. Polygon Selection
3. AI Segmentation
4. Custom Prompts

### Advanced
1. Multi-Angle Views
2. Image Enhancement
3. Design Analysis
4. Transformation Ideas

---

## 📱 Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 640px) {
  .design-studio {
    flex-direction: column;
  }
  .tools-grid {
    grid-template-columns: 1fr;
  }
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
  .tools-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop */
@media (min-width: 1025px) {
  .tools-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

---

## ⚡ Performance Tips

1. **Lazy Load Images**
```typescript
<img loading="lazy" src={url} alt="..." />
```

2. **Debounce User Input**
```typescript
const debouncedOnChange = useMemo(
  () => debounce(onChange, 300),
  [onChange]
);
```

3. **Memoize Expensive Components**
```typescript
export const ResultCard = React.memo(({ result }) => {
  // Component code
});
```

4. **Virtual Scrolling for Large Lists**
```typescript
import { FixedSizeList } from 'react-window';
```

5. **Compress Images Before Upload**
```typescript
import imageCompression from 'browser-image-compression';

const compressedFile = await imageCompression(file, {
  maxSizeMB: 1,
  maxWidthOrHeight: 1920
});
```

---

## 🎨 Design Tokens

```typescript
// src/styles/tokens.ts
export const colors = {
  primary: '#4F46E5',
  secondary: '#10B981',
  accent: '#F59E0B',
  background: '#F9FAFB',
  text: '#111827',
  border: '#E5E7EB',
  error: '#EF4444',
  success: '#10B981'
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px'
};

export const typography = {
  fontFamily: 'Inter, sans-serif',
  fontSize: {
    sm: '14px',
    md: '16px',
    lg: '18px',
    xl: '24px'
  }
};
```

---

## 🚀 Getting Started Checklist

- [ ] Clone repository
- [ ] Install dependencies (`npm install`)
- [ ] Set up environment variables
- [ ] Create component structure
- [ ] Implement API client
- [ ] Build core components
- [ ] Add transformation controls
- [ ] Test on mobile
- [ ] Optimize performance
- [ ] Deploy to staging

---

## 📚 Full Documentation

- **Features**: `DESIGN_STUDIO_FEATURES.md`
- **Implementation**: `DESIGN_STUDIO_IMPLEMENTATION.md`
- **API Reference**: `DESIGN_STUDIO_API_REFERENCE.md`
- **Customer Guide**: `DESIGN_STUDIO_CUSTOMER_GUIDE.md`
- **Summary**: `DESIGN_STUDIO_SUMMARY.md`

---

**Ready to build? Let's make the best design tool ever! 🚀**

