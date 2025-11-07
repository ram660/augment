import React, { useState } from 'react';
import './TransformationPanel.css';

const TRANSFORMATION_TYPES = {
  paint: {
    label: '🎨 Paint',
    fields: [
      { name: 'target_color', label: 'Color', type: 'color', placeholder: 'e.g., Soft Sage Green' },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['matte', 'eggshell', 'satin', 'semi-gloss', 'gloss'] },
      { name: 'walls_only', label: 'Walls Only', type: 'checkbox', default: true },
      { name: 'preserve_trim', label: 'Preserve Trim', type: 'checkbox', default: true },
    ]
  },
  flooring: {
    label: '🪵 Flooring',
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['hardwood', 'tile', 'carpet', 'vinyl', 'laminate', 'concrete'] },
      { name: 'target_style', label: 'Style', type: 'text', placeholder: 'e.g., wide plank oak' },
      { name: 'target_color', label: 'Color', type: 'text', placeholder: 'e.g., natural honey' },
      { name: 'preserve_rugs', label: 'Preserve Rugs', type: 'checkbox', default: true },
    ]
  },
  cabinets: {
    label: '🗄️ Cabinets',
    fields: [
      { name: 'target_color', label: 'Color', type: 'color', placeholder: 'e.g., Navy Blue' },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['painted', 'stained', 'natural wood', 'glazed'] },
      { name: 'target_style', label: 'Style', type: 'select', options: ['shaker', 'flat panel', 'raised panel', 'glass front', 'open shelving'] },
      { name: 'preserve_hardware', label: 'Preserve Hardware', type: 'checkbox', default: false },
    ]
  },
  countertops: {
    label: '🪨 Countertops',
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['granite', 'quartz', 'marble', 'butcher block', 'laminate', 'concrete'] },
      { name: 'target_color', label: 'Color', type: 'text', placeholder: 'e.g., white with gray veining' },
      { name: 'target_pattern', label: 'Pattern', type: 'text', placeholder: 'e.g., marble-look' },
      { name: 'edge_profile', label: 'Edge Profile', type: 'select', options: ['standard', 'beveled', 'bullnose', 'waterfall'] },
    ]
  },
  backsplash: {
    label: '🧱 Backsplash',
    fields: [
      { name: 'target_material', label: 'Material', type: 'text', placeholder: 'e.g., ceramic tile' },
      { name: 'target_pattern', label: 'Pattern', type: 'text', placeholder: 'e.g., subway tile' },
      { name: 'target_color', label: 'Color', type: 'color', placeholder: 'e.g., white' },
      { name: 'grout_color', label: 'Grout Color', type: 'text', placeholder: 'e.g., light gray' },
    ]
  },
  lighting: {
    label: '💡 Lighting',
    fields: [
      { name: 'target_fixture_style', label: 'Fixture Style', type: 'text', placeholder: 'e.g., modern industrial' },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['brushed nickel', 'oil-rubbed bronze', 'chrome', 'brass', 'matte black', 'white'] },
      { name: 'adjust_ambiance', label: 'Ambiance', type: 'select', options: ['', 'warmer', 'cooler', 'brighter', 'dimmer'] },
    ]
  },
  furniture: {
    label: '🛋️ Furniture',
    fields: [
      { name: 'action', label: 'Action', type: 'select', options: ['add', 'remove', 'replace'] },
      { name: 'furniture_description', label: 'Description', type: 'text', placeholder: 'e.g., mid-century modern sofa in charcoal gray' },
      { name: 'placement', label: 'Placement', type: 'text', placeholder: 'e.g., center of the room' },
    ]
  },
};

const TransformationPanel = ({ roomImage, onTransform, onClose }) => {
  const [selectedType, setSelectedType] = useState('paint');
  const [formData, setFormData] = useState({});
  const [numVariations, setNumVariations] = useState(2);
  const [isLoading, setIsLoading] = useState(false);

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
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

      const response = await fetch(`/api/design/transform-${selectedType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      onTransform(result);
    } catch (error) {
      console.error('Transformation failed:', error);
      alert(`Transformation failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const renderField = (field) => {
    const value = formData[field.name] ?? field.default ?? '';

    switch (field.type) {
      case 'text':
      case 'color':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            className="transformation-input"
          />
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="transformation-select"
          >
            {field.options.map(option => (
              <option key={option} value={option}>{option || '(none)'}</option>
            ))}
          </select>
        );

      case 'checkbox':
        return (
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => handleFieldChange(field.name, e.target.checked)}
            className="transformation-checkbox"
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="transformation-panel">
      <div className="transformation-header">
        <h2>🎨 Design Transformation</h2>
        <button onClick={onClose} className="close-button">✕</button>
      </div>

      <div className="transformation-content">
        {/* Room Image Preview */}
        <div className="room-preview">
          <img src={roomImage.image_url || roomImage.url} alt="Room" />
          <p className="room-name">{roomImage.name || 'Room Image'}</p>
        </div>

        {/* Transformation Type Selector */}
        <div className="type-selector">
          <label>Transformation Type</label>
          <div className="type-buttons">
            {Object.entries(TRANSFORMATION_TYPES).map(([key, config]) => (
              <button
                key={key}
                onClick={() => {
                  setSelectedType(key);
                  setFormData({});
                }}
                className={`type-button ${selectedType === key ? 'active' : ''}`}
              >
                {config.label}
              </button>
            ))}
          </div>
        </div>

        {/* Transformation Form */}
        <form onSubmit={handleSubmit} className="transformation-form">
          <div className="form-fields">
            {TRANSFORMATION_TYPES[selectedType].fields.map(field => (
              <div key={field.name} className="form-field">
                <label>{field.label}</label>
                {renderField(field)}
              </div>
            ))}

            {/* Number of Variations */}
            <div className="form-field">
              <label>Number of Variations</label>
              <select
                value={numVariations}
                onChange={(e) => setNumVariations(parseInt(e.target.value))}
                className="transformation-select"
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
                <option value={4}>4</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="generate-button"
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Generating...
              </>
            ) : (
              <>
                ✨ Generate Transformation
              </>
            )}
          </button>
        </form>

        {/* Info */}
        <div className="transformation-info">
          <p>💡 <strong>Tip:</strong> The AI will preserve all other elements of the room and only modify the selected feature.</p>
          <p>⏱️ Generation typically takes 10-30 seconds per variation.</p>
        </div>
      </div>
    </div>
  );
};

export default TransformationPanel;

