# Design Studio - Implementation Guide

## Overview
This document provides the complete implementation plan for the Design Studio tab in HomeView AI, including UI components, API integration, and user workflows.

---

## 🎨 UI Architecture

### Main Layout
```
┌─────────────────────────────────────────────────────────────┐
│  HomeView AI                                                 │
│  [Chat] [Design Studio] [Explore] [Communities] [Jobs]      │
└─────────────────────────────────────────────────────────────┘
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Design Studio                                       │   │
│  │  ┌──────────────┬──────────────┬──────────────┐    │   │
│  │  │ Quick Tools  │ Kitchen/Bath │ Surfaces     │    │   │
│  │  └──────────────┴──────────────┴──────────────┘    │   │
│  │                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────────────┐ │   │
│  │  │                 │  │                         │ │   │
│  │  │  Image Upload   │  │   Transformation        │ │   │
│  │  │  or Select      │  │   Controls              │ │   │
│  │  │                 │  │                         │ │   │
│  │  └─────────────────┘  └─────────────────────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐ │   │
│  │  │                                               │ │   │
│  │  │         Results Gallery (1-4 variations)     │ │   │
│  │  │                                               │ │   │
│  │  └──────────────────────────────────────────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐ │   │
│  │  │  Product Suggestions (if enabled)            │ │   │
│  │  └──────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Component Structure

### Core Components

```typescript
src/components/DesignStudio/
├── DesignStudioMain.tsx              // Main container
├── ToolSelector/
│   ├── QuickTools.tsx                // Most popular tools
│   ├── KitchenBathTools.tsx          // Kitchen/bath specific
│   ├── SurfacesTools.tsx             // Paint, flooring, etc.
│   ├── FurnitureTools.tsx            // Furniture transformations
│   ├── PrecisionTools.tsx            // Advanced editing
│   └── AdvancedTools.tsx             // Analysis, enhancement
├── ImageInput/
│   ├── ImageUploader.tsx             // Drag-drop upload
│   ├── ImageSelector.tsx             // Select from digital twin
│   └── ImagePreview.tsx              // Show selected image
├── TransformControls/
│   ├── PaintControls.tsx             // Paint-specific controls
│   ├── FlooringControls.tsx          // Flooring options
│   ├── CabinetControls.tsx           // Cabinet options
│   ├── CountertopControls.tsx        // Countertop options
│   ├── BacksplashControls.tsx        // Backsplash options
│   ├── LightingControls.tsx          // Lighting options
│   ├── FurnitureControls.tsx         // Furniture options
│   ├── StagingControls.tsx           // Virtual staging
│   ├── MaskingControls.tsx           // Masked editing
│   ├── PromptControls.tsx            // Freeform prompt
│   └── CommonControls.tsx            // Shared controls
├── ResultsGallery/
│   ├── ResultsGrid.tsx               // Grid of variations
│   ├── ResultCard.tsx                // Single result card
│   ├── ComparisonView.tsx            // Before/after slider
│   └── ImageActions.tsx              // Download, share, save
├── ProductSuggestions/
│   ├── ProductList.tsx               // List of suggested products
│   ├── ProductCard.tsx               // Single product card
│   └── ProductFilters.tsx            // Filter by category, price
├── Shared/
│   ├── LoadingSpinner.tsx            // Loading states
│   ├── ErrorMessage.tsx              // Error handling
│   ├── ProgressBar.tsx               // Generation progress
│   └── Toast.tsx                     // Success/error toasts
└── utils/
    ├── apiClient.ts                  // API integration
    ├── imageUtils.ts                 // Image processing
    └── types.ts                      // TypeScript types
```

---

## 🔧 Key Components Implementation

### 1. DesignStudioMain.tsx

```typescript
import React, { useState } from 'react';
import { ToolSelector } from './ToolSelector';
import { ImageInput } from './ImageInput';
import { TransformControls } from './TransformControls';
import { ResultsGallery } from './ResultsGallery';
import { ProductSuggestions } from './ProductSuggestions';

export const DesignStudioMain: React.FC = () => {
  const [selectedTool, setSelectedTool] = useState<string>('paint');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [results, setResults] = useState<TransformResult[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleTransform = async (params: TransformParams) => {
    setIsLoading(true);
    try {
      const response = await transformImage(selectedTool, selectedImage, params);
      setResults(response.images);
      if (response.products) {
        setProducts(response.products);
      }
    } catch (error) {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="design-studio">
      <ToolSelector 
        selectedTool={selectedTool} 
        onSelectTool={setSelectedTool} 
      />
      
      <div className="studio-workspace">
        <ImageInput 
          onImageSelect={setSelectedImage}
          selectedImage={selectedImage}
        />
        
        <TransformControls
          tool={selectedTool}
          onTransform={handleTransform}
          isLoading={isLoading}
        />
      </div>

      {isLoading && <LoadingSpinner />}
      
      {results.length > 0 && (
        <>
          <ResultsGallery 
            results={results}
            originalImage={selectedImage}
          />
          
          {products.length > 0 && (
            <ProductSuggestions products={products} />
          )}
        </>
      )}
    </div>
  );
};
```

### 2. QuickTools.tsx (Most Popular)

```typescript
export const QuickTools: React.FC = () => {
  const quickTools = [
    {
      id: 'paint',
      name: 'Paint Walls',
      icon: '🎨',
      description: 'Change wall colors instantly',
      popular: true
    },
    {
      id: 'flooring',
      name: 'Change Flooring',
      icon: '🪵',
      description: 'Try different flooring materials',
      popular: true
    },
    {
      id: 'virtual-staging',
      name: 'Virtual Staging',
      icon: '🛋️',
      description: 'Furnish empty rooms',
      popular: true
    },
    {
      id: 'prompted',
      name: 'Freeform Prompt',
      icon: '✨',
      description: 'Describe any transformation',
      popular: true
    }
  ];

  return (
    <div className="quick-tools">
      <h3>Quick Transform</h3>
      <div className="tools-grid">
        {quickTools.map(tool => (
          <ToolCard key={tool.id} tool={tool} />
        ))}
      </div>
    </div>
  );
};
```

### 3. PaintControls.tsx

```typescript
interface PaintControlsProps {
  onTransform: (params: PaintTransformParams) => void;
  isLoading: boolean;
}

export const PaintControls: React.FC<PaintControlsProps> = ({ 
  onTransform, 
  isLoading 
}) => {
  const [targetColor, setTargetColor] = useState('');
  const [targetFinish, setTargetFinish] = useState('matte');
  const [wallsOnly, setWallsOnly] = useState(true);
  const [preserveTrim, setPreserveTrim] = useState(true);
  const [numVariations, setNumVariations] = useState(4);

  const finishes = ['matte', 'eggshell', 'satin', 'semi-gloss', 'gloss'];
  
  const popularColors = [
    { name: 'Soft Gray', hex: '#D3D3D3' },
    { name: 'Warm Beige', hex: '#F5F5DC' },
    { name: 'Navy Blue', hex: '#000080' },
    { name: 'Sage Green', hex: '#9DC183' },
    { name: 'Warm White', hex: '#FAF9F6' }
  ];

  const handleSubmit = () => {
    onTransform({
      target_color: targetColor,
      target_finish: targetFinish,
      walls_only: wallsOnly,
      preserve_trim: preserveTrim,
      num_variations: numVariations
    });
  };

  return (
    <div className="paint-controls">
      <h3>Paint Transformation</h3>
      
      {/* Color Input */}
      <div className="control-group">
        <label>Wall Color</label>
        <input 
          type="text" 
          value={targetColor}
          onChange={(e) => setTargetColor(e.target.value)}
          placeholder="e.g., 'soft gray' or '#D3D3D3'"
        />
        
        {/* Popular Colors */}
        <div className="color-swatches">
          {popularColors.map(color => (
            <button
              key={color.hex}
              className="color-swatch"
              style={{ backgroundColor: color.hex }}
              onClick={() => setTargetColor(color.name)}
              title={color.name}
            />
          ))}
        </div>
      </div>

      {/* Finish Selection */}
      <div className="control-group">
        <label>Paint Finish</label>
        <select 
          value={targetFinish}
          onChange={(e) => setTargetFinish(e.target.value)}
        >
          {finishes.map(finish => (
            <option key={finish} value={finish}>
              {finish.charAt(0).toUpperCase() + finish.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Options */}
      <div className="control-group">
        <label>
          <input 
            type="checkbox"
            checked={wallsOnly}
            onChange={(e) => setWallsOnly(e.target.checked)}
          />
          Walls only (preserve ceiling)
        </label>
        
        <label>
          <input 
            type="checkbox"
            checked={preserveTrim}
            onChange={(e) => setPreserveTrim(e.target.checked)}
          />
          Preserve trim and molding
        </label>
      </div>

      {/* Number of Variations */}
      <div className="control-group">
        <label>Number of Variations: {numVariations}</label>
        <input 
          type="range"
          min="1"
          max="4"
          value={numVariations}
          onChange={(e) => setNumVariations(parseInt(e.target.value))}
        />
      </div>

      {/* Submit Button */}
      <button 
        className="transform-button"
        onClick={handleSubmit}
        disabled={isLoading || !targetColor}
      >
        {isLoading ? 'Generating...' : 'Transform Paint'}
      </button>
    </div>
  );
};
```

### 4. ResultsGallery.tsx

```typescript
interface ResultsGalleryProps {
  results: TransformResult[];
  originalImage: string;
}

export const ResultsGallery: React.FC<ResultsGalleryProps> = ({ 
  results, 
  originalImage 
}) => {
  const [selectedResult, setSelectedResult] = useState<TransformResult | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'comparison'>('grid');

  return (
    <div className="results-gallery">
      <div className="gallery-header">
        <h3>Results ({results.length} variations)</h3>
        <div className="view-controls">
          <button 
            className={viewMode === 'grid' ? 'active' : ''}
            onClick={() => setViewMode('grid')}
          >
            Grid View
          </button>
          <button 
            className={viewMode === 'comparison' ? 'active' : ''}
            onClick={() => setViewMode('comparison')}
          >
            Compare
          </button>
        </div>
      </div>

      {viewMode === 'grid' ? (
        <div className="results-grid">
          {results.map((result, index) => (
            <ResultCard
              key={index}
              result={result}
              index={index}
              onSelect={() => setSelectedResult(result)}
            />
          ))}
        </div>
      ) : (
        <ComparisonView
          original={originalImage}
          transformed={selectedResult || results[0]}
        />
      )}
    </div>
  );
};
```

### 5. StagingControls.tsx

```typescript
export const StagingControls: React.FC<StagingControlsProps> = ({
  onTransform,
  isLoading
}) => {
  const [stylePreset, setStylePreset] = useState('Modern');
  const [stylePrompt, setStylePrompt] = useState('');
  const [furnitureDensity, setFurnitureDensity] = useState('medium');
  const [lockEnvelope, setLockEnvelope] = useState(true);
  const [enableGrounding, setEnableGrounding] = useState(true);
  const [numVariations, setNumVariations] = useState(2);

  const stylePresets = [
    'Modern', 'Scandinavian', 'Traditional', 'Farmhouse',
    'Industrial', 'Coastal', 'Bohemian', 'Minimal'
  ];

  const densityOptions = [
    { value: 'light', label: 'Light (minimal furniture)' },
    { value: 'medium', label: 'Medium (balanced)' },
    { value: 'full', label: 'Full (well-furnished)' }
  ];

  return (
    <div className="staging-controls">
      <h3>Virtual Staging</h3>

      {/* Style Preset */}
      <div className="control-group">
        <label>Style Preset</label>
        <div className="style-grid">
          {stylePresets.map(style => (
            <button
              key={style}
              className={`style-button ${stylePreset === style ? 'active' : ''}`}
              onClick={() => setStylePreset(style)}
            >
              {style}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Style Prompt */}
      <div className="control-group">
        <label>Custom Style (optional)</label>
        <textarea
          value={stylePrompt}
          onChange={(e) => setStylePrompt(e.target.value)}
          placeholder="e.g., 'warm tones with natural materials'"
          rows={2}
        />
      </div>

      {/* Furniture Density */}
      <div className="control-group">
        <label>Furniture Amount</label>
        {densityOptions.map(option => (
          <label key={option.value} className="radio-label">
            <input
              type="radio"
              value={option.value}
              checked={furnitureDensity === option.value}
              onChange={(e) => setFurnitureDensity(e.target.value)}
            />
            {option.label}
          </label>
        ))}
      </div>

      {/* Options */}
      <div className="control-group">
        <label>
          <input
            type="checkbox"
            checked={lockEnvelope}
            onChange={(e) => setLockEnvelope(e.target.checked)}
          />
          Preserve walls, floors, and windows
        </label>
        
        <label>
          <input
            type="checkbox"
            checked={enableGrounding}
            onChange={(e) => setEnableGrounding(e.target.checked)}
          />
          Suggest real products (Canada)
        </label>
      </div>

      <button
        className="transform-button"
        onClick={() => onTransform({
          style_preset: stylePreset,
          style_prompt: stylePrompt,
          furniture_density: furnitureDensity,
          lock_envelope: lockEnvelope,
          enable_grounding: enableGrounding,
          num_variations: numVariations
        })}
        disabled={isLoading}
      >
        {isLoading ? 'Staging...' : 'Stage Room'}
      </button>
    </div>
  );
};
```

---

## 🔌 API Integration

### API Client (apiClient.ts)

```typescript
const API_BASE = '/api/v1/design';

export const designAPI = {
  // Paint transformation
  transformPaint: async (roomImageId: string, params: PaintTransformParams) => {
    return await fetch(`${API_BASE}/transform-paint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_image_id: roomImageId, ...params })
    }).then(res => res.json());
  },

  // Flooring transformation
  transformFlooring: async (roomImageId: string, params: FlooringTransformParams) => {
    return await fetch(`${API_BASE}/transform-flooring`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_image_id: roomImageId, ...params })
    }).then(res => res.json());
  },

  // Virtual staging (upload)
  virtualStagingUpload: async (imageDataUrl: string, params: StagingParams) => {
    return await fetch(`${API_BASE}/virtual-staging-upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data_url: imageDataUrl, ...params })
    }).then(res => res.json());
  },

  // Prompted transformation (upload)
  transformPromptedUpload: async (imageDataUrl: string, params: PromptedParams) => {
    return await fetch(`${API_BASE}/transform-prompted-upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data_url: imageDataUrl, ...params })
    }).then(res => res.json());
  },

  // ... more endpoints
};
```

---

## 🎯 User Workflows

### Workflow 1: Quick Paint Change
```
1. User lands on Design Studio
2. "Paint Walls" is pre-selected (most popular)
3. User uploads/selects image
4. User picks color from swatches or types name
5. User clicks "Transform Paint"
6. Loading spinner shows progress
7. 4 variations appear in gallery
8. User can download, save, or share
```

### Workflow 2: Complete Kitchen Makeover
```
1. User selects "Kitchen/Bath" category
2. User uploads kitchen image
3. User transforms cabinets → white shaker
4. User saves favorite result
5. User transforms countertops → quartz
6. User transforms backsplash → subway tile
7. User gets product suggestions for all materials
8. User saves complete transformation to project
9. User can request contractor quotes
```

### Workflow 3: Virtual Staging
```
1. User selects "Virtual Staging"
2. User uploads empty room photo
3. User selects "Modern" style preset
4. User enables product grounding
5. User clicks "Stage Room"
6. 2-3 variations generated
7. Product suggestions appear below
8. User clicks products to see details/prices
9. User saves staged images for listing
```

---

## 📱 Mobile Responsiveness

- Stack layout on mobile (image above, controls below)
- Touch-friendly controls (larger buttons, sliders)
- Swipe gestures for result gallery
- Optimized image loading for mobile networks
- Progressive enhancement for advanced features

---

## ⚡ Performance Optimization

1. **Image Optimization**
   - Compress uploads before sending
   - Lazy load result images
   - Use WebP format where supported

2. **API Optimization**
   - Show progress indicators
   - Cache recent transformations
   - Implement request cancellation

3. **UI Optimization**
   - Virtual scrolling for large galleries
   - Debounce user inputs
   - Optimize re-renders with React.memo

---

## 🎨 Design System

### Colors
- Primary: #4F46E5 (Indigo)
- Secondary: #10B981 (Green)
- Accent: #F59E0B (Amber)
- Background: #F9FAFB
- Text: #111827

### Typography
- Headings: Inter Bold
- Body: Inter Regular
- Monospace: JetBrains Mono

### Spacing
- Base unit: 4px
- Small: 8px
- Medium: 16px
- Large: 24px
- XLarge: 32px

---

## 🚀 Next Steps

1. Implement core components (DesignStudioMain, ToolSelector, ImageInput)
2. Build transformation controls for each tool type
3. Integrate API client with backend endpoints
4. Implement results gallery with comparison view
5. Add product suggestions component
6. Test on mobile devices
7. Optimize performance
8. Add analytics tracking

See `DESIGN_STUDIO_FEATURES.md` for complete feature list.

