# 🛠️ Design Studio - Developer Guide

## Quick Start

### Using the Enhanced Transformation Panel

```jsx
import EnhancedTransformationPanel from '../components/Studio/EnhancedTransformationPanel';

function MyComponent() {
  const [showPanel, setShowPanel] = useState(false);
  const [roomImage, setRoomImage] = useState(null);

  return (
    <>
      <button onClick={() => setShowPanel(true)}>
        Transform Room
      </button>

      {showPanel && (
        <EnhancedTransformationPanel
          roomImage={roomImage}
          onTransform={(result) => {
            console.log('Transformation complete:', result);
            setShowPanel(false);
          }}
          onClose={() => setShowPanel(false)}
        />
      )}
    </>
  );
}
```

---

## Component Props

### EnhancedTransformationPanel

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `roomImage` | Object | Yes | Room image object with `id` and `image_url` |
| `onTransform` | Function | Yes | Callback when transformation completes |
| `onClose` | Function | Yes | Callback when panel is closed |

#### roomImage Object Structure:
```javascript
{
  id: 'room-123',           // Required: Room image ID
  image_url: '/path/to/image.jpg',  // Required: Image URL
  name: 'Living Room',      // Optional: Display name
  transformationType: 'paint'  // Optional: Pre-select tool
}
```

#### onTransform Callback:
```javascript
onTransform(result) {
  // result structure:
  {
    transformation_id: 'trans-456',
    image_urls: ['url1.jpg', 'url2.jpg', 'url3.jpg'],
    metadata: { /* transformation details */ }
  }
}
```

---

## Adding New Transformation Tools

### Step 1: Define the Tool

Add to `TRANSFORMATION_TOOLS` object in `EnhancedTransformationPanel.jsx`:

```javascript
const TRANSFORMATION_TOOLS = {
  // ... existing tools
  
  my_new_tool: {
    label: 'My New Tool',
    icon: '🎨',
    category: 'surfaces',  // or kitchen, furniture, lighting, outdoor, advanced
    description: 'What this tool does',
    endpoint: 'transform-my-tool',  // Backend API endpoint
    fields: [
      {
        name: 'field_name',
        label: 'Field Label',
        type: 'text',  // text, color, select, checkbox, textarea
        placeholder: 'e.g., example value',
        required: true,  // optional
        default: 'default value',  // optional
        options: ['option1', 'option2']  // for select type
      },
      // ... more fields
    ]
  }
};
```

### Step 2: Add to Category

Update `TRANSFORMATION_CATEGORIES` to include your tool:

```javascript
const TRANSFORMATION_CATEGORIES = {
  surfaces: {
    label: 'Surfaces',
    icon: '🎨',
    description: 'Transform walls, floors, and surfaces',
    color: '#FF6B6B',
    tools: ['paint', 'flooring', 'wallpaper', 'accent_wall', 'my_new_tool']  // Add here
  },
  // ... other categories
};
```

### Step 3: Create Backend Endpoint

Ensure your backend has the corresponding endpoint:

```python
# backend/api/design.py

@router.post("/transform-my-tool")
async def transform_my_tool(request: MyToolRequest):
    # Your transformation logic
    return {
        "transformation_id": "trans-123",
        "image_urls": ["result1.jpg", "result2.jpg"],
        "metadata": {}
    }
```

---

## Field Types Reference

### Text Input
```javascript
{
  name: 'color_name',
  label: 'Color Name',
  type: 'text',
  placeholder: 'e.g., Soft Sage Green',
  required: true
}
```

### Color Picker
```javascript
{
  name: 'wall_color',
  label: 'Wall Color',
  type: 'color',
  placeholder: 'e.g., #A8DADC',
  required: true
}
```
Renders both text input and color picker.

### Select Dropdown
```javascript
{
  name: 'finish',
  label: 'Finish',
  type: 'select',
  options: ['matte', 'eggshell', 'satin', 'semi-gloss', 'gloss'],
  default: 'matte',
  required: true
}
```

### Checkbox
```javascript
{
  name: 'preserve_trim',
  label: 'Preserve Trim & Molding',
  type: 'checkbox',
  default: true
}
```

### Textarea
```javascript
{
  name: 'custom_prompt',
  label: 'Describe Your Vision',
  type: 'textarea',
  placeholder: 'Describe what you want...',
  required: true
}
```

---

## API Integration

### Request Format

All transformations send a POST request to `/api/v1/design/{endpoint}`:

```javascript
const payload = {
  room_image_id: roomImage.id,
  ...formData,  // All form field values
  num_variations: numVariations  // 1-4
};

const response = await fetch(`/api/v1/design/${currentTool.endpoint}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});
```

### Response Format

Expected response structure:

```javascript
{
  "transformation_id": "trans-123",
  "image_urls": [
    "https://storage.../variation1.jpg",
    "https://storage.../variation2.jpg"
  ],
  "metadata": {
    "tool": "paint",
    "parameters": { /* form data */ },
    "processing_time": 12.5
  }
}
```

---

## Styling Customization

### Category Colors

Customize category colors in `TRANSFORMATION_CATEGORIES`:

```javascript
const TRANSFORMATION_CATEGORIES = {
  surfaces: {
    color: '#FF6B6B'  // Red
  },
  kitchen: {
    color: '#4ECDC4'  // Teal
  },
  // ... etc
};
```

### CSS Variables

Override in `EnhancedTransformationPanel.css`:

```css
.enhanced-transformation-panel {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --category-color: #FF6B6B;
  --border-radius: 12px;
  --spacing: 16px;
}
```

---

## Common Patterns

### Pre-selecting a Tool

```javascript
<EnhancedTransformationPanel
  roomImage={{
    id: 'room-123',
    image_url: '/image.jpg',
    transformationType: 'paint'  // Pre-select paint tool
  }}
  onTransform={handleTransform}
  onClose={handleClose}
/>
```

### Handling Errors

```javascript
const handleTransform = async (result) => {
  try {
    if (!result.image_urls || result.image_urls.length === 0) {
      throw new Error('No images generated');
    }
    // Process result
  } catch (error) {
    console.error('Transformation error:', error);
    alert(`Error: ${error.message}`);
  }
};
```

### Loading States

The component handles loading states internally, but you can track them:

```javascript
const [isTransforming, setIsTransforming] = useState(false);

<EnhancedTransformationPanel
  roomImage={roomImage}
  onTransform={(result) => {
    setIsTransforming(false);
    // Handle result
  }}
  onClose={() => setShowPanel(false)}
/>
```

---

## Testing

### Unit Tests

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import EnhancedTransformationPanel from './EnhancedTransformationPanel';

test('renders all categories', () => {
  render(
    <EnhancedTransformationPanel
      roomImage={{ id: '1', image_url: '/test.jpg' }}
      onTransform={jest.fn()}
      onClose={jest.fn()}
    />
  );
  
  expect(screen.getByText('Surfaces')).toBeInTheDocument();
  expect(screen.getByText('Kitchen & Bath')).toBeInTheDocument();
  // ... etc
});

test('switches tools when category changes', () => {
  render(<EnhancedTransformationPanel {...props} />);
  
  fireEvent.click(screen.getByText('Kitchen & Bath'));
  expect(screen.getByText('Cabinets')).toBeInTheDocument();
});
```

### Integration Tests

```javascript
test('submits transformation request', async () => {
  const mockTransform = jest.fn();
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        transformation_id: 'test-123',
        image_urls: ['url1.jpg']
      })
    })
  );

  render(
    <EnhancedTransformationPanel
      roomImage={{ id: '1', image_url: '/test.jpg' }}
      onTransform={mockTransform}
      onClose={jest.fn()}
    />
  );

  // Fill form and submit
  fireEvent.change(screen.getByPlaceholderText(/color/i), {
    target: { value: 'Sage Green' }
  });
  fireEvent.click(screen.getByText('Transform'));

  await waitFor(() => {
    expect(mockTransform).toHaveBeenCalledWith({
      transformation_id: 'test-123',
      image_urls: ['url1.jpg']
    });
  });
});
```

---

## Performance Optimization

### Lazy Loading

```javascript
import { lazy, Suspense } from 'react';

const EnhancedTransformationPanel = lazy(() => 
  import('./components/Studio/EnhancedTransformationPanel')
);

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <EnhancedTransformationPanel {...props} />
    </Suspense>
  );
}
```

### Memoization

```javascript
import { useMemo } from 'react';

const toolsInCategory = useMemo(() => 
  Object.entries(TRANSFORMATION_TOOLS).filter(
    ([_, tool]) => tool.category === selectedCategory
  ),
  [selectedCategory]
);
```

---

## Troubleshooting

### Panel Not Showing
- Check z-index conflicts
- Ensure parent has proper positioning
- Verify showPanel state is true

### Form Not Submitting
- Check required fields are filled
- Verify API endpoint exists
- Check network tab for errors
- Ensure roomImage has valid id

### Styling Issues
- Clear browser cache
- Check CSS import order
- Verify CSS file is loaded
- Check for conflicting styles

### API Errors
- Verify endpoint URL is correct
- Check request payload format
- Ensure backend is running
- Check CORS settings

---

## Best Practices

### 1. Always Validate Input
```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  
  // Validate required fields
  const requiredFields = currentTool.fields.filter(f => f.required);
  const missingFields = requiredFields.filter(f => !formData[f.name]);
  
  if (missingFields.length > 0) {
    alert(`Please fill in: ${missingFields.map(f => f.label).join(', ')}`);
    return;
  }
  
  // Proceed with transformation
};
```

### 2. Handle Errors Gracefully
```javascript
try {
  const response = await fetch(endpoint, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const result = await response.json();
  onTransform(result);
} catch (error) {
  console.error('Transformation failed:', error);
  alert(`Transformation failed: ${error.message}`);
}
```

### 3. Provide User Feedback
```javascript
// Show loading state
setIsLoading(true);

// Show progress if available
if (result.progress) {
  setProgress(result.progress);
}

// Show success message
toast.success('Transformation complete!');
```

### 4. Clean Up State
```javascript
const handleClose = () => {
  setFormData({});
  setSelectedTool('paint');
  setSelectedCategory('surfaces');
  onClose();
};
```

---

## Resources

### Documentation
- [Design Studio Complete Guide](./DESIGN_STUDIO_COMPLETE.md)
- [Design Studio Showcase](./DESIGN_STUDIO_SHOWCASE.md)
- [Improvements Summary](./DESIGN_STUDIO_IMPROVEMENTS_SUMMARY.md)

### API Documentation
- Backend API: `/api/v1/design/docs`
- Transformation endpoints: `/api/v1/design/*`

### Support
- GitHub Issues: [Report bugs or request features]
- Developer Slack: #design-studio channel
- Email: dev@homeviewai.com

---

**Happy Coding! 🚀**

