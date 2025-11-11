import React, { useState } from 'react';
import './EnhancedTransformationPanel.css';

// Comprehensive transformation categories
const TRANSFORMATION_CATEGORIES = {
  surfaces: {
    label: 'Surfaces',
    icon: '🎨',
    description: 'Transform walls, floors, and surfaces',
    color: '#FF6B6B'
  },
  kitchen: {
    label: 'Kitchen & Bath',
    icon: '🍳',
    description: 'Kitchen and bathroom transformations',
    color: '#4ECDC4'
  },
  furniture: {
    label: 'Furniture & Decor',
    icon: '🛋️',
    description: 'Add, remove, or change furniture',
    color: '#95E1D3'
  },
  lighting: {
    label: 'Lighting',
    icon: '💡',
    description: 'Transform lighting and ambiance',
    color: '#FFE66D'
  },
  outdoor: {
    label: 'Outdoor & Exterior',
    icon: '🌳',
    description: 'Exterior and outdoor spaces',
    color: '#6BCF7F'
  },
  advanced: {
    label: 'Advanced Tools',
    icon: '⚡',
    description: 'Precision tools and custom edits',
    color: '#A8DADC'
  }
};

// All transformation tools organized by category
const TRANSFORMATION_TOOLS = {
  // SURFACES
  paint: {
    label: 'Paint Walls',
    icon: '🎨',
    category: 'surfaces',
    description: 'Change wall colors with any finish',
    endpoint: 'transform-paint',
    fields: [
      { name: 'target_color', label: 'Wall Color', type: 'color', placeholder: 'e.g., Soft Sage Green', required: true },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['matte', 'eggshell', 'satin', 'semi-gloss', 'gloss'], default: 'matte' },
      { name: 'walls_only', label: 'Walls Only (preserve ceiling)', type: 'checkbox', default: true },
      { name: 'preserve_trim', label: 'Preserve Trim & Molding', type: 'checkbox', default: true },
    ]
  },
  flooring: {
    label: 'Flooring',
    icon: '🪵',
    category: 'surfaces',
    description: 'Change flooring material and style',
    endpoint: 'transform-flooring',
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['hardwood', 'tile', 'carpet', 'vinyl', 'laminate', 'stone', 'bamboo', 'cork'], required: true },
      { name: 'target_style', label: 'Style', type: 'text', placeholder: 'e.g., wide plank oak, herringbone', required: true },
      { name: 'target_color', label: 'Color', type: 'text', placeholder: 'e.g., natural oak, gray' },
      { name: 'preserve_rugs', label: 'Preserve Area Rugs', type: 'checkbox', default: true },
    ]
  },
  wallpaper: {
    label: 'Wallpaper',
    icon: '📜',
    category: 'surfaces',
    description: 'Add or change wallpaper patterns',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'pattern_type', label: 'Pattern', type: 'select', options: ['floral', 'geometric', 'striped', 'textured', 'damask', 'modern', 'tropical', 'botanical'], required: true },
      { name: 'color_scheme', label: 'Color Scheme', type: 'text', placeholder: 'e.g., navy and gold, soft pastels' },
      { name: 'accent_wall_only', label: 'Accent Wall Only', type: 'checkbox', default: false },
    ]
  },
  accent_wall: {
    label: 'Accent Wall',
    icon: '🎯',
    category: 'surfaces',
    description: 'Create a stunning feature wall',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'wall_treatment', label: 'Treatment', type: 'select', options: ['paint', 'wallpaper', 'wood paneling', 'stone', 'brick', 'shiplap', 'board and batten'], required: true },
      { name: 'color_or_material', label: 'Color/Material', type: 'text', placeholder: 'e.g., deep navy, reclaimed wood', required: true },
      { name: 'which_wall', label: 'Which Wall', type: 'select', options: ['auto-detect', 'behind furniture', 'longest wall'], default: 'auto-detect' },
    ]
  },

  // KITCHEN & BATH
  cabinets: {
    label: 'Cabinets',
    icon: '🗄️',
    category: 'kitchen',
    description: 'Transform cabinet color and style',
    endpoint: 'transform-cabinets',
    fields: [
      { name: 'target_color', label: 'Cabinet Color', type: 'color', placeholder: 'e.g., white, navy', required: true },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['painted', 'stained', 'natural wood', 'glazed', 'two-tone'], default: 'painted' },
      { name: 'target_style', label: 'Style', type: 'select', options: ['shaker', 'flat panel', 'raised panel', 'glass front', 'open shelving'] },
      { name: 'preserve_hardware', label: 'Keep Existing Hardware', type: 'checkbox', default: false },
    ]
  },
  countertops: {
    label: 'Countertops',
    icon: '🪨',
    category: 'kitchen',
    description: 'Change countertop material',
    endpoint: 'transform-countertops',
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['granite', 'quartz', 'marble', 'butcher block', 'laminate', 'concrete', 'soapstone', 'quartzite'], required: true },
      { name: 'target_color', label: 'Color', type: 'text', placeholder: 'e.g., white with gray veining', required: true },
      { name: 'target_pattern', label: 'Pattern', type: 'select', options: ['solid', 'veined', 'speckled', 'dramatic veining'] },
      { name: 'edge_profile', label: 'Edge Profile', type: 'select', options: ['standard', 'beveled', 'bullnose', 'waterfall', 'ogee'], default: 'standard' },
    ]
  },
  backsplash: {
    label: 'Backsplash',
    icon: '🧱',
    category: 'kitchen',
    description: 'Update backsplash tile',
    endpoint: 'transform-backsplash',
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['ceramic tile', 'glass tile', 'subway tile', 'mosaic', 'stone', 'metal', 'marble'], required: true },
      { name: 'target_pattern', label: 'Pattern', type: 'select', options: ['subway', 'herringbone', 'stacked', 'mosaic', 'arabesque', 'hexagon', 'chevron'], required: true },
      { name: 'target_color', label: 'Tile Color', type: 'text', placeholder: 'e.g., white, blue', required: true },
      { name: 'grout_color', label: 'Grout Color', type: 'text', placeholder: 'e.g., gray, white', default: 'white' },
    ]
  },
  fixtures: {
    label: 'Fixtures',
    icon: '🚰',
    category: 'kitchen',
    description: 'Update faucets and fixtures',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'fixture_type', label: 'Type', type: 'select', options: ['faucet', 'sink', 'toilet', 'shower', 'bathtub', 'all fixtures'], required: true },
      { name: 'finish', label: 'Finish', type: 'select', options: ['chrome', 'brushed nickel', 'matte black', 'brass', 'bronze', 'gold', 'copper'], required: true },
      { name: 'style', label: 'Style', type: 'select', options: ['modern', 'traditional', 'farmhouse', 'industrial', 'contemporary', 'transitional'], required: true },
    ]
  },
  appliances: {
    label: 'Appliances',
    icon: '🔌',
    category: 'kitchen',
    description: 'Update appliance finish',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'finish', label: 'Finish', type: 'select', options: ['stainless steel', 'black stainless', 'white', 'black', 'panel-ready', 'slate', 'bisque'], required: true },
      { name: 'which_appliances', label: 'Which Appliances', type: 'select', options: ['all', 'refrigerator', 'stove/range', 'dishwasher', 'microwave'], default: 'all' },
    ]
  },

  // FURNITURE & DECOR
  virtual_staging: {
    label: 'Virtual Staging',
    icon: '🛋️',
    category: 'furniture',
    description: 'Add furniture to empty rooms',
    endpoint: 'virtual-staging',
    fields: [
      { name: 'style_preset', label: 'Design Style', type: 'select', options: ['Modern', 'Traditional', 'Minimalist', 'Farmhouse', 'Industrial', 'Scandinavian', 'Bohemian', 'Coastal', 'Mid-Century', 'Transitional'], required: true },
      { name: 'furniture_density', label: 'Furniture Amount', type: 'select', options: ['light', 'medium', 'full'], default: 'medium' },
      { name: 'lock_envelope', label: 'Preserve Room Structure', type: 'checkbox', default: true },
    ]
  },
  unstaging: {
    label: 'Unstaging',
    icon: '🧹',
    category: 'furniture',
    description: 'Remove furniture and decor',
    endpoint: 'unstage',
    fields: [
      { name: 'strength', label: 'Removal Strength', type: 'select', options: ['light', 'medium', 'full'], default: 'medium' },
    ]
  },
  furniture_swap: {
    label: 'Furniture Swap',
    icon: '🪑',
    category: 'furniture',
    description: 'Replace specific furniture pieces',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'item_to_replace', label: 'Item to Replace', type: 'select', options: ['sofa', 'chair', 'dining table', 'coffee table', 'bed', 'dresser', 'desk', 'all furniture'], required: true },
      { name: 'new_style', label: 'New Style', type: 'text', placeholder: 'e.g., modern sectional sofa, velvet armchair', required: true },
      { name: 'color_preference', label: 'Color', type: 'text', placeholder: 'e.g., gray, navy, natural wood' },
    ]
  },
  decor: {
    label: 'Decor & Accessories',
    icon: '🎨',
    category: 'furniture',
    description: 'Add or change decorative elements',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'decor_type', label: 'Type', type: 'select', options: ['artwork', 'plants', 'rugs', 'pillows', 'throw blankets', 'vases', 'lighting', 'all decor', 'custom'], required: true },
      { name: 'style', label: 'Style', type: 'text', placeholder: 'e.g., modern abstract art, tropical plants' },
      { name: 'color_scheme', label: 'Color Scheme', type: 'text', placeholder: 'e.g., earth tones, jewel tones' },
    ]
  },
  window_treatments: {
    label: 'Window Treatments',
    icon: '🪟',
    category: 'furniture',
    description: 'Add or change curtains and blinds',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'treatment_type', label: 'Type', type: 'select', options: ['curtains', 'drapes', 'blinds', 'shades', 'shutters', 'valance', 'roman shades'], required: true },
      { name: 'style', label: 'Style', type: 'select', options: ['modern', 'traditional', 'sheer', 'blackout', 'layered', 'minimalist'], required: true },
      { name: 'color', label: 'Color', type: 'text', placeholder: 'e.g., white, linen, navy' },
    ]
  },

  // LIGHTING
  lighting_fixtures: {
    label: 'Light Fixtures',
    icon: '💡',
    category: 'lighting',
    description: 'Change light fixtures',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'fixture_type', label: 'Type', type: 'select', options: ['pendant', 'chandelier', 'recessed', 'track', 'sconce', 'floor lamp', 'table lamp', 'ceiling fan with light'], required: true },
      { name: 'style', label: 'Style', type: 'select', options: ['modern', 'industrial', 'traditional', 'farmhouse', 'contemporary', 'art deco', 'mid-century'], required: true },
      { name: 'finish', label: 'Finish', type: 'select', options: ['brass', 'black', 'chrome', 'bronze', 'nickel', 'gold', 'copper', 'white'], required: true },
    ]
  },
  natural_light: {
    label: 'Natural Light',
    icon: '☀️',
    category: 'lighting',
    description: 'Adjust natural lighting',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'brightness', label: 'Brightness', type: 'select', options: ['much brighter', 'brighter', 'softer', 'golden hour', 'overcast', 'dramatic'], required: true },
      { name: 'time_of_day', label: 'Time of Day', type: 'select', options: ['morning', 'midday', 'afternoon', 'evening', 'auto'], default: 'auto' },
    ]
  },
  ambient_lighting: {
    label: 'Ambient Lighting',
    icon: '🌟',
    category: 'lighting',
    description: 'Change overall lighting mood',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'mood', label: 'Mood', type: 'select', options: ['warm & cozy', 'cool & crisp', 'neutral', 'dramatic', 'bright & airy', 'soft & romantic'], required: true },
      { name: 'color_temperature', label: 'Color Temperature', type: 'select', options: ['warm white (2700K)', 'soft white (3000K)', 'neutral white (3500K)', 'daylight (5000K)', 'cool white (6000K)'], default: 'soft white (3000K)' },
    ]
  },
  smart_lighting: {
    label: 'Smart Lighting',
    icon: '🎛️',
    category: 'lighting',
    description: 'Add smart lighting effects',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'effect', label: 'Effect', type: 'select', options: ['accent lighting', 'under-cabinet', 'cove lighting', 'LED strips', 'color-changing RGB', 'toe-kick lighting'], required: true },
      { name: 'color', label: 'Color', type: 'text', placeholder: 'e.g., warm white, RGB, blue' },
      { name: 'placement', label: 'Placement', type: 'text', placeholder: 'e.g., under cabinets, behind TV' },
    ]
  },

  // OUTDOOR & EXTERIOR
  exterior_paint: {
    label: 'Exterior Paint',
    icon: '🏠',
    category: 'outdoor',
    description: 'Change exterior paint colors',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'main_color', label: 'Main Color', type: 'color', placeholder: 'e.g., gray, white, blue', required: true },
      { name: 'trim_color', label: 'Trim Color', type: 'color', placeholder: 'e.g., white, cream' },
      { name: 'accent_color', label: 'Accent Color (door, shutters)', type: 'color', placeholder: 'e.g., black, red' },
    ]
  },
  landscaping: {
    label: 'Landscaping',
    icon: '🌳',
    category: 'outdoor',
    description: 'Add or modify landscaping',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'style', label: 'Style', type: 'select', options: ['modern', 'traditional', 'xeriscape', 'cottage garden', 'tropical', 'zen', 'native plants'], required: true },
      { name: 'elements', label: 'Elements', type: 'select', options: ['plants & flowers', 'trees', 'shrubs', 'complete landscape', 'custom'], required: true },
      { name: 'maintenance', label: 'Maintenance Level', type: 'select', options: ['low', 'medium', 'high'], default: 'medium' },
      { name: 'color_palette', label: 'Color Palette', type: 'text', placeholder: 'e.g., greens and purples, colorful' },
    ]
  },
  deck_patio: {
    label: 'Deck/Patio',
    icon: '🪵',
    category: 'outdoor',
    description: 'Add or modify outdoor living spaces',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'type', label: 'Type', type: 'select', options: ['wood deck', 'composite deck', 'stone patio', 'concrete patio', 'brick pavers', 'flagstone'], required: true },
      { name: 'color', label: 'Color/Finish', type: 'text', placeholder: 'e.g., natural wood, gray composite', required: true },
      { name: 'features', label: 'Additional Features', type: 'text', placeholder: 'e.g., built-in seating, pergola, fire pit' },
      { name: 'size', label: 'Size', type: 'select', options: ['small', 'medium', 'large', 'full backyard'], default: 'medium' },
    ]
  },
  outdoor_furniture: {
    label: 'Outdoor Furniture',
    icon: '🪑',
    category: 'outdoor',
    description: 'Add outdoor furniture and accessories',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'furniture_type', label: 'Type', type: 'select', options: ['dining set', 'lounge seating', 'fire pit area', 'grill station', 'complete outdoor room'], required: true },
      { name: 'style', label: 'Style', type: 'select', options: ['modern', 'traditional', 'coastal', 'rustic', 'contemporary', 'bohemian'], required: true },
      { name: 'material', label: 'Material', type: 'select', options: ['wicker/rattan', 'metal', 'wood', 'teak', 'aluminum', 'mixed materials'], required: true },
      { name: 'cushion_color', label: 'Cushion Color', type: 'text', placeholder: 'e.g., navy, beige, striped' },
    ]
  },
  pool_spa: {
    label: 'Pool/Spa',
    icon: '🏊',
    category: 'outdoor',
    description: 'Add or visualize pool and spa',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'type', label: 'Type', type: 'select', options: ['swimming pool', 'hot tub/spa', 'plunge pool', 'natural pool', 'pool with spa'], required: true },
      { name: 'shape', label: 'Shape', type: 'select', options: ['rectangular', 'kidney', 'freeform', 'geometric', 'lap pool'], required: true },
      { name: 'finish', label: 'Finish', type: 'select', options: ['blue plaster', 'pebble', 'tile', 'dark plaster', 'natural'], default: 'blue plaster' },
      { name: 'surroundings', label: 'Surroundings', type: 'text', placeholder: 'e.g., stone deck, tropical plants' },
    ]
  },

  // ADVANCED TOOLS
  precise_edit: {
    label: 'Precise Edit',
    icon: '🎯',
    category: 'advanced',
    description: 'Edit specific areas with precision',
    endpoint: 'segment-anything',
    fields: [
      { name: 'mode', label: 'Selection Mode', type: 'select', options: ['click to select', 'draw polygon', 'auto-detect object'], required: true },
      { name: 'operation', label: 'Operation', type: 'select', options: ['replace', 'remove', 'modify'], required: true },
      { name: 'replacement_prompt', label: 'Replace/Modify With', type: 'textarea', placeholder: 'Describe what to add or how to modify', required: true },
    ]
  },
  custom_prompt: {
    label: 'Custom Prompt',
    icon: '✨',
    category: 'advanced',
    description: 'Describe any transformation you imagine',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'prompt', label: 'Describe Your Vision', type: 'textarea', placeholder: 'Describe exactly what you want to change... Be as detailed as possible for best results.', required: true },
      { name: 'preserve_layout', label: 'Preserve Room Layout', type: 'checkbox', default: true },
      { name: 'enable_grounding', label: 'Enable Product Suggestions', type: 'checkbox', default: true },
      { name: 'style_reference', label: 'Style Reference', type: 'text', placeholder: 'e.g., modern farmhouse, industrial loft' },
    ]
  },
  style_transfer: {
    label: 'Style Transfer',
    icon: '🎨',
    category: 'advanced',
    description: 'Apply a complete style transformation',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'target_style', label: 'Target Style', type: 'select', options: ['Modern', 'Traditional', 'Minimalist', 'Farmhouse', 'Industrial', 'Scandinavian', 'Bohemian', 'Coastal', 'Mid-Century Modern', 'Art Deco', 'Rustic', 'Contemporary', 'Transitional', 'Eclectic'], required: true },
      { name: 'intensity', label: 'Transformation Intensity', type: 'select', options: ['subtle (keep most elements)', 'moderate (balanced change)', 'dramatic (complete transformation)'], default: 'moderate (balanced change)' },
      { name: 'preserve_layout', label: 'Preserve Room Layout', type: 'checkbox', default: true },
      { name: 'color_palette', label: 'Color Palette', type: 'text', placeholder: 'e.g., warm neutrals, cool blues' },
    ]
  },
  multi_room: {
    label: 'Multi-Room',
    icon: '🏠',
    category: 'advanced',
    description: 'Apply consistent changes across rooms',
    endpoint: 'transform-prompted',
    fields: [
      { name: 'transformation', label: 'Transformation Type', type: 'select', options: ['paint colors', 'flooring', 'design style', 'lighting mood', 'furniture style'], required: true },
      { name: 'consistency', label: 'Consistency Level', type: 'select', options: ['exact match', 'coordinated (similar)', 'complementary (harmonious)'], default: 'coordinated (similar)' },
      { name: 'details', label: 'Details', type: 'textarea', placeholder: 'Describe the look you want across all rooms' },
    ]
  },
  before_after: {
    label: 'Before/After',
    icon: '🔄',
    category: 'advanced',
    description: 'Create before/after comparisons',
    endpoint: 'create-comparison',
    fields: [
      { name: 'layout', label: 'Layout', type: 'select', options: ['side-by-side', 'slider', 'grid (2x2)', 'vertical stack'], default: 'side-by-side' },
      { name: 'include_labels', label: 'Include Labels', type: 'checkbox', default: true },
      { name: 'add_watermark', label: 'Add Watermark', type: 'checkbox', default: false },
    ]
  },
  ai_suggestions: {
    label: 'AI Suggestions',
    icon: '🤖',
    category: 'advanced',
    description: 'Get AI-powered design recommendations',
    endpoint: 'ai-suggestions',
    fields: [
      { name: 'focus_area', label: 'Focus Area', type: 'select', options: ['overall design', 'color palette', 'furniture layout', 'lighting', 'budget-friendly options', 'trending styles'], required: true },
      { name: 'budget_range', label: 'Budget Range', type: 'select', options: ['budget-friendly', 'mid-range', 'high-end', 'luxury', 'no preference'], default: 'no preference' },
      { name: 'preferences', label: 'Your Preferences', type: 'textarea', placeholder: 'Tell us what you like, dislike, or want to achieve...' },
    ]
  },
};

export default function EnhancedTransformationPanel({ roomImage, onTransform, onClose }) {
  const [selectedCategory, setSelectedCategory] = useState('surfaces');
  const [selectedTool, setSelectedTool] = useState('paint');
  const [formData, setFormData] = useState({});
  const [numVariations, setNumVariations] = useState(2);
  const [isLoading, setIsLoading] = useState(false);

  const currentTool = TRANSFORMATION_TOOLS[selectedTool];
  const toolsInCategory = Object.entries(TRANSFORMATION_TOOLS).filter(
    ([_, tool]) => tool.category === selectedCategory
  );

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const payload = {
        room_image_id: roomImage.id,
        ...formData,
        num_variations: numVariations
      };

      const response = await fetch(`/api/v1/design/${currentTool.endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const result = await response.json();
      onTransform(result);
    } catch (error) {
      console.error('Transformation failed:', error);
      alert(`Transformation failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="enhanced-transformation-panel">
      {/* Header */}
      <div className="panel-header">
        <h2>✨ Design Studio</h2>
        <p className="subtitle">Transform anything you imagine</p>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      {/* Category Selector */}
      <div className="category-selector">
        {Object.entries(TRANSFORMATION_CATEGORIES).map(([key, category]) => (
          <button
            key={key}
            className={`category-btn ${selectedCategory === key ? 'active' : ''}`}
            onClick={() => {
              setSelectedCategory(key);
              const firstTool = Object.entries(TRANSFORMATION_TOOLS).find(([_, t]) => t.category === key);
              if (firstTool) setSelectedTool(firstTool[0]);
            }}
            style={{ '--category-color': category.color }}
          >
            <span className="category-icon">{category.icon}</span>
            <span className="category-label">{category.label}</span>
          </button>
        ))}
      </div>

      {/* Tool Grid */}
      <div className="tool-grid">
        {toolsInCategory.map(([key, tool]) => (
          <button
            key={key}
            className={`tool-card ${selectedTool === key ? 'active' : ''}`}
            onClick={() => setSelectedTool(key)}
          >
            <span className="tool-icon">{tool.icon}</span>
            <span className="tool-label">{tool.label}</span>
          </button>
        ))}
      </div>

      {/* Tool Description */}
      <div className="tool-description">
        <h3>{currentTool.icon} {currentTool.label}</h3>
        <p>{currentTool.description}</p>
      </div>

      {/* Transformation Form */}
      <form onSubmit={handleSubmit} className="transformation-form">
        <div className="form-fields">
          {currentTool.fields.map((field) => (
            <div key={field.name} className="form-field">
              <label>
                {field.label}
                {field.required && <span className="required">*</span>}
              </label>
              {renderField(field)}
            </div>
          ))}

          {/* Number of Variations */}
          <div className="form-field">
            <label>Number of Variations</label>
            <div className="variation-selector">
              {[1, 2, 3, 4].map(num => (
                <button
                  key={num}
                  type="button"
                  className={`variation-btn ${numVariations === num ? 'active' : ''}`}
                  onClick={() => setNumVariations(num)}
                >
                  {num}
                </button>
              ))}
            </div>
            <small>More variations = more options to choose from</small>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="form-actions">
          <button type="submit" className="transform-btn" disabled={isLoading}>
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Transforming...
              </>
            ) : (
              <>
                <span>✨</span>
                Transform
              </>
            )}
          </button>
        </div>
      </form>

      {/* Quick Tips */}
      <div className="quick-tips">
        <h4>💡 Pro Tips</h4>
        <ul>
          <li>Be specific with colors and styles for best results</li>
          <li>Generate multiple variations to see different options</li>
          <li>Use "Preserve" options to keep elements you like</li>
          <li>Try the Custom Prompt tool for unique transformations</li>
        </ul>
      </div>
    </div>
  );

  function renderField(field) {
    const value = formData[field.name] ?? field.default ?? '';

    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            className="text-input"
          />
        );

      case 'color':
        return (
          <div className="color-input-group">
            <input
              type="text"
              value={value}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              required={field.required}
              className="text-input"
            />
            <input
              type="color"
              value={value.startsWith('#') ? value : '#000000'}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              className="color-picker"
            />
          </div>
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            required={field.required}
            className="select-input"
          >
            {!field.required && <option value="">-- Select --</option>}
            {field.options.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );

      case 'checkbox':
        return (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleFieldChange(field.name, e.target.checked)}
              className="checkbox-input"
            />
            <span className="checkbox-text">Yes</span>
          </label>
        );

      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            rows={4}
            className="textarea-input"
          />
        );

      default:
        return null;
    }
  }
}

