'use client';

import React, { useState } from 'react';
import { X, Sparkles, Loader2, ChevronLeft, ChevronRight, Download, Share2, RotateCcw, ExternalLink } from 'lucide-react';
import { designAPI } from '@/lib/api/design';

interface WorkspaceViewProps {
  originalImage: string;
  analysis: any;
  onBack: () => void;
}

interface TransformResult {
  image_urls: string[];
  summary?: string;
  products?: Array<{
    title: string;
    link: string;
    source: string;
    price?: string;
    image?: string;
  }>;
  sources?: Array<{
    title: string;
    link: string;
  }>;
}

export default function WorkspaceView({ originalImage, analysis, onBack }: WorkspaceViewProps) {
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [isTransforming, setIsTransforming] = useState(false);
  const [transformResult, setTransformResult] = useState<TransformResult | null>(null);
  const [selectedVariation, setSelectedVariation] = useState(0);
  const [numVariations, setNumVariations] = useState(3);
  const [showComparison, setShowComparison] = useState(false);
  // Normalize analysis fields to avoid rendering non-primitive values
  const summary: any = analysis?.summary ?? {};
  const ideas: string[] = Array.isArray(analysis?.ideas)
    ? (analysis.ideas as any[]).filter((x: any) => typeof x === 'string')
    : [];
  const styleTransformations: Array<{ style: string; description: string }> =
    Array.isArray(analysis?.style_transformations)
      ? (analysis.style_transformations as any[]).filter(
          (x: any) => x && typeof x.style === 'string' && typeof x.description === 'string'
        )
      : [];


  // Quick action tools
  const quickTools = [
    { id: 'paint', name: 'Change Paint', icon: '🎨', category: 'surfaces' },
    { id: 'flooring', name: 'New Flooring', icon: '🪵', category: 'surfaces' },
    { id: 'furniture', name: 'Add Furniture', icon: '🛋️', category: 'furniture' },
    { id: 'lighting', name: 'Update Lighting', icon: '💡', category: 'lighting' },
    { id: 'virtual_staging', name: 'Virtual Staging', icon: '🏡', category: 'advanced' },
    { id: 'style_transfer', name: 'Change Style', icon: '✨', category: 'advanced' },
  ];

  const handleCustomPromptSubmit = async () => {
    if (!customPrompt.trim()) return;

    setIsTransforming(true);
    try {
      const result = await designAPI.transformPromptedUpload(originalImage, customPrompt, {
        numVariations,
        enableGrounding: true,
      });
      setTransformResult(result);
      setSelectedVariation(0);
    } catch (error) {
      console.error('Transformation failed:', error);
      alert('Transformation failed. Please try again.');
    } finally {
      setIsTransforming(false);
    }
  };

  const handleQuickTool = async (toolId: string) => {
    setSelectedTool(toolId);

    // Extract style from analysis if available
    const currentStyle = (summary as any)?.styles?.[0] || 'modern';

    // Generate a smart prompt based on analysis
    let prompt = '';
    switch (toolId) {
      case 'paint':
        prompt = `Change the wall paint to a modern color that complements the ${currentStyle} style`;
        break;
      case 'flooring':
        prompt = `Replace the flooring with modern materials suitable for this room`;
        break;
      case 'furniture':
        prompt = `Add modern furniture pieces that match the ${currentStyle} style`;
        break;
      case 'lighting':
        prompt = `Update the lighting fixtures to modern style`;
        break;
      case 'virtual_staging':
        setIsTransforming(true);
        try {
          const result = await designAPI.virtualStagingUpload(originalImage, {
            style_preset: 'Modern',
            furniture_density: 'medium',
            lock_envelope: true,
            num_variations: numVariations,
            enableGrounding: true,
          });
          setTransformResult(result);
          setSelectedVariation(0);
        } catch (error) {
          console.error('Virtual staging failed:', error);
          alert('Virtual staging failed. Please try again.');
        } finally {
          setIsTransforming(false);
        }
        return;
      case 'style_transfer':
        prompt = `Transform this room to Modern style while preserving the layout`;
        break;
      default:
        prompt = `Transform this room with modern updates`;
    }

    setCustomPrompt(prompt);
    setIsTransforming(true);
    try {
      const result = await designAPI.transformPromptedUpload(originalImage, prompt, {
        numVariations,
        enableGrounding: true,
      });
      setTransformResult(result);
      setSelectedVariation(0);
    } catch (error) {
      console.error('Transformation failed:', error);
      alert('Transformation failed. Please try again.');
    } finally {
      setIsTransforming(false);
    }
  };

  const handleDownload = () => {
    if (!transformResult?.image_urls[selectedVariation]) return;
    const link = document.createElement('a');
    link.href = transformResult.image_urls[selectedVariation];
    link.download = `transformed-${Date.now()}.jpg`;
    link.click();
  };

  const handleReset = () => {
    setTransformResult(null);
    setCustomPrompt('');
    setSelectedTool(null);
    setSelectedVariation(0);
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Panel - Controls */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4"
          >
            <ChevronLeft className="w-5 h-5" />
            <span>Back to Analysis</span>
          </button>
          <h2 className="text-2xl font-bold text-gray-800">Transform Your Space</h2>
          <p className="text-gray-600 text-sm mt-1">Choose a tool or write your own prompt</p>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Custom Prompt */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              ✨ Describe Your Vision
            </label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="E.g., 'Change walls to soft gray, add modern furniture, update lighting to warm tones...'"
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
            <div className="mt-3 flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-xs text-gray-600 mb-1">Variations</label>
                <select
                  value={numVariations}
                  onChange={(e) => setNumVariations(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value={1}>1 variation</option>
                  <option value={2}>2 variations</option>
                  <option value={3}>3 variations</option>
                  <option value={4}>4 variations</option>
                </select>
              </div>
              <button
                onClick={handleCustomPromptSubmit}
                disabled={!customPrompt.trim() || isTransforming}
                className="flex-1 mt-5 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all"
              >
                {isTransforming ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </span>
                ) : (
                  'Generate'
                )}
              </button>
            </div>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="text-sm text-gray-500">or choose a quick tool</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          {/* Quick Tools */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              🚀 Quick Tools
            </label>
            <div className="grid grid-cols-2 gap-3">
              {quickTools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => handleQuickTool(tool.id)}
                  disabled={isTransforming}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    selectedTool === tool.id
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-purple-300 bg-white'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <div className="text-2xl mb-2">{tool.icon}</div>
                  <div className="text-sm font-semibold text-gray-800">{tool.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Transformation Ideas */}
          {ideas.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                💡 Transformation Ideas
              </label>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {ideas.map((idea: string, idx: number) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setCustomPrompt(idea);
                    }}
                    className="w-full p-3 text-left rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-all"
                  >
                    <div className="text-sm text-gray-700">{idea}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Style Transformations */}
          {styleTransformations.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                ✨ Style Transformations
              </label>
              <div className="space-y-2">
                {styleTransformations.map((style: any, idx: number) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setCustomPrompt(`Transform this room to ${style.style} style. ${style.description}`);
                    }}
                    className="w-full p-3 text-left rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
                  >
                    <div className="text-xs text-blue-600 font-semibold uppercase mb-1">
                      {style.style}
                    </div>
                    <div className="text-sm text-gray-700">{style.description}</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Results */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* Results Header */}
        {transformResult && (
          <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowComparison(!showComparison)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-all"
              >
                {showComparison ? 'Hide' : 'Show'} Original
              </button>
              {transformResult.image_urls.length > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSelectedVariation(Math.max(0, selectedVariation - 1))}
                    disabled={selectedVariation === 0}
                    className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm text-gray-600">
                    Variation {selectedVariation + 1} of {transformResult.image_urls.length}
                  </span>
                  <button
                    onClick={() => setSelectedVariation(Math.min(transformResult.image_urls.length - 1, selectedVariation + 1))}
                    disabled={selectedVariation === transformResult.image_urls.length - 1}
                    className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDownload}
                className="p-2 hover:bg-gray-100 rounded-lg"
                title="Download"
              >
                <Download className="w-5 h-5" />
              </button>
              <button
                onClick={handleReset}
                className="p-2 hover:bg-gray-100 rounded-lg"
                title="Reset"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Image Display */}
        <div className="flex-1 overflow-auto p-6">
          {!transformResult ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <img
                  src={originalImage}
                  alt="Original"
                  className="max-w-full max-h-[70vh] rounded-xl shadow-lg mx-auto mb-6"
                />
                <p className="text-gray-500">
                  {isTransforming ? 'Generating transformation...' : 'Your transformed image will appear here'}
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Image Comparison */}
              <div className={`grid ${showComparison ? 'grid-cols-2' : 'grid-cols-1'} gap-4`}>
                {showComparison && (
                  <div>
                    <div className="text-sm font-semibold text-gray-600 mb-2">Original</div>
                    <img
                      src={originalImage}
                      alt="Original"
                      className="w-full rounded-xl shadow-lg"
                    />
                  </div>
                )}
                <div>
                  {showComparison && (
                    <div className="text-sm font-semibold text-gray-600 mb-2">Transformed</div>
                  )}
                  <img
                    src={transformResult.image_urls[selectedVariation]}
                    alt="Transformed"
                    className="w-full rounded-xl shadow-lg"
                  />
                </div>
              </div>

              {/* Variation Thumbnails */}
              {transformResult.image_urls.length > 1 && (
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-3">All Variations</div>
                  <div className="grid grid-cols-4 gap-3">
                    {transformResult.image_urls.map((url, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedVariation(idx)}
                        className={`relative rounded-lg overflow-hidden border-2 transition-all ${
                          selectedVariation === idx
                            ? 'border-purple-500 ring-2 ring-purple-200'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                      >
                        <img src={url} alt={`Variation ${idx + 1}`} className="w-full aspect-square object-cover" />
                        <div className="absolute top-1 right-1 bg-black/50 text-white text-xs px-2 py-1 rounded">
                          {idx + 1}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              {transformResult.summary && (
                <div className="bg-white rounded-xl p-5 border border-gray-200">
                  <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-500" />
                    Changes Made
                  </h3>
                  <p className="text-gray-700">{typeof transformResult.summary === 'string' ? transformResult.summary : JSON.stringify(transformResult.summary)}</p>
                </div>
              )}

              {/* Product Recommendations */}
              {transformResult.products && transformResult.products.length > 0 && (
                <div className="bg-white rounded-xl p-5 border border-gray-200">
                  <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    🛒 Product Recommendations
                  </h3>
                  <div className="space-y-3">
                    {transformResult.products.map((product, idx) => (
                      <a
                        key={idx}
                        href={product.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-all group"
                      >
                        {product.image && (
                          <img src={product.image} alt={product.title} className="w-16 h-16 rounded object-cover" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-800 group-hover:text-purple-600 truncate">
                            {product.title}
                          </div>
                          <div className="text-xs text-gray-500">{product.source}</div>
                          {product.price && (
                            <div className="text-sm font-semibold text-green-600 mt-1">{product.price}</div>
                          )}
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-purple-600 flex-shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

