'use client';

import { useState } from 'react';
import { X, Sparkles, Loader2 } from 'lucide-react';
import { designAPI } from '@/lib/api/design';

interface TransformationPanelProps {
  imageDataUrl: string;
  toolId: string;
  toolName: string;
  onClose: () => void;
  onComplete: (results: { image_urls: string[] }) => void;
}

// Tool configurations with their specific fields
const TOOL_CONFIGS: Record<string, any> = {
  paint: {
    fields: [
      { name: 'target_color', label: 'Wall Color', type: 'text', placeholder: 'e.g., Soft Gray, Navy Blue', required: true },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['matte', 'eggshell', 'satin', 'semi-gloss', 'gloss'], default: 'matte' },
      { name: 'walls_only', label: 'Walls Only (preserve ceiling)', type: 'checkbox', default: true },
      { name: 'preserve_trim', label: 'Preserve Trim & Molding', type: 'checkbox', default: true },
    ],
  },
  flooring: {
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['hardwood', 'tile', 'carpet', 'vinyl', 'laminate', 'stone'], required: true },
      { name: 'target_style', label: 'Style', type: 'text', placeholder: 'e.g., Oak, Marble, Herringbone' },
      { name: 'target_color', label: 'Color', type: 'text', placeholder: 'e.g., Light Oak, Dark Walnut' },
      { name: 'preserve_rugs', label: 'Preserve Rugs', type: 'checkbox', default: true },
    ],
  },
  cabinets: {
    fields: [
      { name: 'target_color', label: 'Cabinet Color', type: 'text', placeholder: 'e.g., White, Navy, Natural Wood', required: true },
      { name: 'target_finish', label: 'Finish', type: 'select', options: ['matte', 'satin', 'gloss', 'distressed', 'natural'], default: 'satin' },
      { name: 'target_style', label: 'Style', type: 'select', options: ['shaker', 'flat-panel', 'raised-panel', 'beadboard', 'louvered'], default: 'shaker' },
      { name: 'preserve_hardware', label: 'Preserve Hardware', type: 'checkbox', default: false },
    ],
  },
  countertops: {
    fields: [
      { name: 'target_material', label: 'Material', type: 'select', options: ['granite', 'quartz', 'marble', 'butcher block', 'concrete', 'laminate'], required: true },
      { name: 'target_color', label: 'Color', type: 'text', placeholder: 'e.g., White, Black, Gray' },
      { name: 'target_pattern', label: 'Pattern', type: 'text', placeholder: 'e.g., Veined, Speckled, Solid' },
      { name: 'edge_profile', label: 'Edge Profile', type: 'select', options: ['straight', 'beveled', 'bullnose', 'ogee', 'waterfall'], default: 'straight' },
    ],
  },
  lighting: {
    fields: [
      { name: 'fixture_style', label: 'Fixture Style', type: 'text', placeholder: 'e.g., Modern Pendant, Chandelier', required: true },
      { name: 'fixture_finish', label: 'Finish', type: 'select', options: ['brushed nickel', 'matte black', 'brass', 'chrome', 'bronze'], default: 'brushed nickel' },
      { name: 'num_fixtures', label: 'Number of Fixtures', type: 'number', default: 1, min: 1, max: 10 },
      { name: 'preserve_existing', label: 'Keep Existing Lights', type: 'checkbox', default: false },
    ],
  },
  virtual_staging: {
    fields: [
      { name: 'style_preset', label: 'Style', type: 'select', options: ['Modern', 'Traditional', 'Minimalist', 'Farmhouse', 'Industrial', 'Scandinavian', 'Bohemian', 'Coastal'], required: true, default: 'Modern' },
      { name: 'style_prompt', label: 'Additional Details', type: 'textarea', placeholder: 'Describe specific furniture or decor you want...' },
      { name: 'furniture_density', label: 'Furniture Amount', type: 'select', options: ['light', 'medium', 'heavy'], default: 'medium' },
      { name: 'lock_envelope', label: 'Preserve Room Structure', type: 'checkbox', default: true },
    ],
  },
  custom: {
    fields: [
      { name: 'prompt', label: 'Describe Your Transformation', type: 'textarea', placeholder: 'Describe exactly what you want to change...', required: true, rows: 4 },
    ],
  },
  // Add more tool configs for other categories
  wallpaper: {
    fields: [
      { name: 'pattern', label: 'Pattern', type: 'text', placeholder: 'e.g., Floral, Geometric, Striped', required: true },
      { name: 'color', label: 'Color Scheme', type: 'text', placeholder: 'e.g., Blue and White' },
      { name: 'accent_wall_only', label: 'Accent Wall Only', type: 'checkbox', default: false },
    ],
  },
  backsplash: {
    fields: [
      { name: 'material', label: 'Material', type: 'select', options: ['tile', 'glass', 'stone', 'metal', 'marble'], required: true },
      { name: 'pattern', label: 'Pattern', type: 'text', placeholder: 'e.g., Subway, Herringbone, Mosaic' },
      { name: 'color', label: 'Color', type: 'text', placeholder: 'e.g., White, Gray, Blue' },
    ],
  },
  fixtures: {
    fields: [
      { name: 'fixture_type', label: 'Fixture Type', type: 'select', options: ['faucet', 'sink', 'toilet', 'shower', 'tub'], required: true },
      { name: 'style', label: 'Style', type: 'text', placeholder: 'e.g., Modern, Traditional', required: true },
      { name: 'finish', label: 'Finish', type: 'select', options: ['chrome', 'brushed nickel', 'matte black', 'brass', 'bronze'], default: 'chrome' },
    ],
  },
  furniture: {
    fields: [
      { name: 'action', label: 'Action', type: 'select', options: ['Replace', 'Add', 'Remove'], default: 'Replace' },
      { name: 'style', label: 'Style', type: 'text', placeholder: 'e.g., Modern, Mid-Century', required: true },
      { name: 'color', label: 'Color Scheme', type: 'text', placeholder: 'e.g., Neutral, Bold' },
      { name: 'specific_items', label: 'Specific Items', type: 'text', placeholder: 'e.g., Sofa, Coffee Table' },
    ],
  },
  style_transfer: {
    fields: [
      { name: 'target_style', label: 'Target Style', type: 'select', options: ['Modern', 'Traditional', 'Minimalist', 'Farmhouse', 'Industrial', 'Scandinavian', 'Bohemian', 'Coastal', 'Mid-Century Modern'], required: true },
      { name: 'intensity', label: 'Intensity', type: 'select', options: ['subtle', 'moderate', 'dramatic'], default: 'moderate' },
      { name: 'preserve_layout', label: 'Preserve Layout', type: 'checkbox', default: true },
    ],
  },
  renovation: {
    fields: [
      { name: 'renovation_type', label: 'Renovation Type', type: 'select', options: ['minor', 'moderate', 'major', 'complete'], default: 'moderate' },
      { name: 'changes', label: 'Specific Changes', type: 'textarea', placeholder: 'Describe what you want to renovate...', required: true },
      { name: 'style', label: 'Style', type: 'text', placeholder: 'e.g., Modern, Traditional' },
    ],
  },
};

export default function TransformationPanel({
  imageDataUrl,
  toolId,
  toolName,
  onClose,
  onComplete,
}: TransformationPanelProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [numVariations, setNumVariations] = useState(3);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const config = TOOL_CONFIGS[toolId] || TOOL_CONFIGS.custom;

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Validate required fields
      const requiredFields = config.fields.filter((f: any) => f.required);
      for (const field of requiredFields) {
        if (!formData[field.name]) {
          throw new Error(`${field.label} is required`);
        }
      }

      let result;

      // Special handling for custom prompt tool
      if (toolId === 'custom') {
        result = await designAPI.transformPromptedUpload(imageDataUrl, formData.prompt, {
          numVariations,
          enableGrounding: true,
        });
      }
      // Special handling for virtual staging
      else if (toolId === 'virtual_staging') {
        result = await designAPI.virtualStagingUpload(imageDataUrl, {
          style_preset: formData.style_preset || 'Modern',
          style_prompt: formData.style_prompt,
          furniture_density: formData.furniture_density || 'medium',
          lock_envelope: formData.lock_envelope !== false,
          num_variations: numVariations,
          enableGrounding: true,
        });
      }
      // For all other tools, build a prompt and use transform-prompted-upload
      else {
        const prompt = designAPI.buildTransformationPrompt(toolId, formData);
        console.log('Generated prompt:', prompt);
        result = await designAPI.transformPromptedUpload(imageDataUrl, prompt, {
          numVariations,
          enableGrounding: true,
        });
      }

      onComplete(result);
    } catch (err: any) {
      console.error('Transformation failed:', err);
      setError(err.message || 'Transformation failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderField = (field: any) => {
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
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(field.name, parseInt(e.target.value))}
            min={field.min}
            max={field.max}
            required={field.required}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            required={field.required}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent capitalize"
          >
            {field.options.map((option: string) => (
              <option key={option} value={option} className="capitalize">
                {option}
              </option>
            ))}
          </select>
        );

      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            rows={field.rows || 3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
          />
        );

      case 'checkbox':
        return (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleFieldChange(field.name, e.target.checked)}
              className="w-5 h-5 text-primary border-gray-300 rounded focus:ring-2 focus:ring-primary"
            />
            <span className="text-sm text-gray-700">{field.label}</span>
          </label>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-primary/10 to-secondary/10">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{toolName}</h2>
            <p className="text-sm text-gray-600 mt-1">Configure your transformation</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {config.fields.map((field: any) => (
            <div key={field.name}>
              {field.type !== 'checkbox' && (
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </label>
              )}
              {renderField(field)}
            </div>
          ))}

          {/* Number of Variations */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Variations
            </label>
            <select
              value={numVariations}
              onChange={(e) => setNumVariations(parseInt(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value={1}>1 variation</option>
              <option value={2}>2 variations</option>
              <option value={3}>3 variations</option>
              <option value={4}>4 variations</option>
            </select>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-xl hover:shadow-lg transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Transforming...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Transformation
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

