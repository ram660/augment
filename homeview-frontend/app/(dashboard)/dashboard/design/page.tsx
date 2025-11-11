'use client';

import { Suspense, useState, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, Upload, Loader2, Save, RefreshCw, Palette, Home, Sofa, Zap, Edit3, ArrowRight, Package, ExternalLink, Download, Share2 } from 'lucide-react';
import { designAPI } from '@/lib/api/design';
import { projectsAPI } from '@/lib/api/projects';

// Import components
import BeforeAfterSlider from '@/components/studio/BeforeAfterSlider';

interface PresetOption {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  prompt: string;
}

const PRESET_OPTIONS: PresetOption[] = [
  {
    id: 'paint',
    name: 'Paint Walls',
    description: 'Change wall colors and finishes',
    icon: <Palette className="w-6 h-6" />,
    prompt: 'Transform the wall paint color to a modern, fresh look with a neutral color palette'
  },
  {
    id: 'flooring',
    name: 'New Flooring',
    description: 'Replace flooring material and style',
    icon: <Home className="w-6 h-6" />,
    prompt: 'Replace the flooring with modern hardwood or luxury vinyl that complements the space'
  },
  {
    id: 'furniture',
    name: 'Furniture & Staging',
    description: 'Add or rearrange furniture',
    icon: <Sofa className="w-6 h-6" />,
    prompt: 'Add modern furniture and staging to make the space feel more inviting and functional'
  },
  {
    id: 'lighting',
    name: 'Lighting Design',
    description: 'Update lighting fixtures and ambiance',
    icon: <Zap className="w-6 h-6" />,
    prompt: 'Upgrade the lighting with modern fixtures and improve the overall ambiance'
  },
  {
    id: 'custom',
    name: 'Custom Design',
    description: 'Describe your vision',
    icon: <Edit3 className="w-6 h-6" />,
    prompt: ''
  }
];

function DesignStudioContent() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [resultImages, setResultImages] = useState<string[]>([]);
  const [isTransforming, setIsTransforming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [summary, setSummary] = useState<any | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [transformationStep, setTransformationStep] = useState<'upload' | 'options' | 'results'>('upload');
  const [isDragActive, setIsDragActive] = useState(false);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [designHistory, setDesignHistory] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Helper function to compress images
  const compressImage = (file: File, maxWidth: number, quality: number): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            reject(new Error('Failed to get canvas context'));
            return;
          }

          ctx.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/jpeg', quality));
        };
        img.onerror = reject;
        img.src = e.target?.result as string;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  // Handle image upload
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const compressedDataUrl = await compressImage(file, 1920, 0.85);
      setSelectedImage(compressedDataUrl);
    } catch (error) {
      console.error('Failed to upload image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle transformation with preset or custom prompt
  const handleTransform = async (prompt: string) => {
    if (!selectedImage || !prompt.trim()) {
      alert('Please provide a transformation prompt');
      return;
    }

    setIsTransforming(true);
    setTransformationStep('results');

    try {
      const response = await designAPI.transformPromptedUpload(
        selectedImage,
        prompt,
        { numVariations: 2, enableGrounding: true }
      );

      if (response.image_urls && response.image_urls.length > 0) {
        setResultImages(response.image_urls);
        setSummary(response.summary || null);
        setProducts(response.products || []);

        // Add to history
        const historyItem = {
          id: Date.now(),
          originalImage: selectedImage,
          transformedImages: response.image_urls,
          summary: response.summary || null,
          products: response.products || [],
          prompt: prompt,
          timestamp: new Date().toISOString(),
        };
        setDesignHistory([historyItem, ...designHistory]);
      } else {
        alert('No transformation results received');
      }
    } catch (error) {
      console.error('Failed to transform image:', error);
      alert('Failed to generate design. Please try again.');
      setTransformationStep('options');
    } finally {
      setIsTransforming(false);
    }
  };

  // Handle preset selection
  const handlePresetSelect = (preset: PresetOption) => {
    setSelectedPreset(preset.id);
    if (preset.id !== 'custom') {
      handleTransform(preset.prompt);
    }
  };

  // Drag & Drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        handleImageUpload({ target: { files: [file] } } as any);
      } else {
        alert('Please drop an image file');
      }
    }
  };

  // Add to favorites
  const handleAddToFavorites = () => {
    if (resultImages.length === 0) return;
    const favorite = {
      id: Date.now(),
      originalImage: selectedImage,
      transformedImage: resultImages[0],
      summary: summary,
      prompt: customPrompt || selectedPreset,
      timestamp: new Date().toISOString(),
    };
    setFavorites([...favorites, favorite]);
    alert('Design added to favorites!');
  };



  // Download before/after as image
  const handleDownloadComparison = async () => {
    if (!selectedImage || resultImages.length === 0) return;

    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Create a canvas with both images side by side
      const img1 = new Image();
      const img2 = new Image();

      img1.crossOrigin = 'anonymous';
      img2.crossOrigin = 'anonymous';

      img1.onload = () => {
        img2.onload = () => {
          canvas.width = img1.width + img2.width + 20;
          canvas.height = Math.max(img1.height, img2.height) + 60;

          // Fill background
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          // Draw labels
          ctx.fillStyle = '#000000';
          ctx.font = 'bold 20px Arial';
          ctx.fillText('Before', 20, 30);
          ctx.fillText('After', img1.width + 40, 30);

          // Draw images
          ctx.drawImage(img1, 10, 50);
          ctx.drawImage(img2, img1.width + 20, 50);

          // Download
          const link = document.createElement('a');
          link.href = canvas.toDataURL('image/png');
          link.download = `design-comparison-${Date.now()}.png`;
          link.click();
        };
        img2.src = resultImages[0];
      };
      img1.src = selectedImage;
    } catch (error) {
      console.error('Failed to download comparison:', error);
      alert('Failed to download comparison image');
    }
  };



  // Share design
  const handleShareDesign = async () => {
    if (!resultImages.length) return;

    const shareText = `Check out this amazing room transformation I created with HomeView AI! 🏠✨`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'HomeView AI Design',
          text: shareText,
          url: window.location.href,
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    } else {
      // Fallback: copy to clipboard
      const text = `${shareText}\n${window.location.href}`;
      navigator.clipboard.writeText(text);
      alert('Share link copied to clipboard!');
    }
  };

  // Handle save project
  const handleSaveProject = async () => {
    if (!selectedImage || resultImages.length === 0) return;

    setIsSaving(true);
    try {
      const projectData = {
        name: `Design Project ${new Date().toLocaleDateString()}`,
        original_image: selectedImage,
        result_images: resultImages,
        summary: summary,
      };

      if (currentProjectId) {
        await projectsAPI.updateProject(currentProjectId, projectData);
        alert('Project updated successfully!');
      } else {
        const response = await projectsAPI.saveProject(projectData);
        setCurrentProjectId(response.id);
        alert('Project saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save project:', error);
      alert('Failed to save project. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Reset to start over
  const handleReset = () => {
    if (confirm('Are you sure you want to start over? This will clear your current design.')) {
      setSelectedImage(null);
      setResultImages([]);
      setSummary(null);
      setProducts([]);
      setCurrentProjectId(null);
      setSelectedPreset(null);
      setCustomPrompt('');
      setTransformationStep('upload');
    }
  };

  return (
    <div className="h-full w-full overflow-y-auto bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <div className="max-w-6xl mx-auto p-6 pb-20 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Design Studio
            </h1>
            <p className="text-gray-600 mt-1 text-sm md:text-base">Transform your space with AI-powered design</p>
          </div>
          {selectedImage && (
            <div className="flex gap-2">
              {resultImages.length > 0 && (
                <Button
                  variant="outline"
                  onClick={handleSaveProject}
                  disabled={isSaving}
                  className="gap-2"
                  size="sm"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Saving...' : currentProjectId ? 'Update' : 'Save'}
                </Button>
              )}
              <Button
                variant="outline"
                onClick={handleReset}
                className="gap-2"
                size="sm"
              >
                <RefreshCw className="w-4 h-4" />
                Start Over
              </Button>
            </div>
          )}
        </div>

        {/* Upload Section - Show prominently if no image */}
        {!selectedImage && (
          <div className="space-y-6">
            <Card
              className={`border-2 border-dashed bg-white/80 backdrop-blur shadow-xl transition-all ${
                isDragActive
                  ? 'border-purple-600 bg-purple-50'
                  : 'border-purple-300'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <CardContent className="p-8 md:p-12">
                <div className="flex flex-col items-center justify-center text-center space-y-5">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center shadow-lg">
                    <Upload className="w-10 h-10 text-purple-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                      Upload Your Room Image
                    </h2>
                    <p className="text-base md:text-lg text-gray-600 max-w-lg">
                      {isDragActive
                        ? 'Drop your image here!'
                        : 'Drag and drop your room photo here, or click to browse'}
                    </p>
                  </div>
                  <input
                    id="room-upload-file-input"
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="sr-only"
                  />
                  <label htmlFor="room-upload-file-input" className="cursor-pointer">
                    <Button
                      type="button"
                      size="lg"
                      onClick={() => { try { fileInputRef.current?.focus(); fileInputRef.current?.click(); } catch (err) { console.error('File picker failed, retrying', err); try { fileInputRef.current?.click(); } catch {} } }}
                      disabled={isUploading}
                      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-6 text-base md:text-lg shadow-lg hover:shadow-xl transition-all"
                    >
                      {isUploading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-5 h-5 mr-2" />
                          Choose Image to Get Started
                        </>
                      )}
                    </Button>
                  </label>
                  <p className="text-xs md:text-sm text-gray-500">
                    Supports JPG, PNG, WebP • Max 10MB • Best results with well-lit photos
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Design History Gallery */}
            {designHistory.length > 0 && (
              <Card className="bg-white/80 backdrop-blur shadow-lg">
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Designs</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {designHistory.slice(0, 6).map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          setSelectedImage(item.originalImage);
                          setTransformationStep('options');
                        }}
                        className="relative group rounded-lg overflow-hidden bg-gray-100 h-24 hover:shadow-lg transition-shadow"
                      >
                        <img
                          src={item.originalImage}
                          alt="Recent design"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
                          <span className="text-white text-xs font-semibold opacity-0 group-hover:opacity-100">
                            Reload
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Favorites Gallery */}
            {favorites.length > 0 && (
              <Card className="bg-white/80 backdrop-blur shadow-lg">
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">⭐ Favorite Designs</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {favorites.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          setSelectedImage(item.originalImage);
                          setResultImages([item.transformedImage]);
                          setSummary(item.summary);
                          setTransformationStep('results');
                        }}
                        className="relative group rounded-lg overflow-hidden bg-gray-100 h-24 hover:shadow-lg transition-shadow"
                      >
                        <img
                          src={item.transformedImage}
                          alt="Favorite design"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
                          <span className="text-white text-xs font-semibold opacity-0 group-hover:opacity-100">
                            View
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Main Content - After upload */}
        {selectedImage && transformationStep === 'options' && (
          <div className="space-y-6">
            {/* Uploaded Image Preview */}
            <Card className="bg-white/80 backdrop-blur shadow-lg">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-semibold text-gray-900">Your Room</h3>
                  <label htmlFor="room-upload-file-input" className="cursor-pointer">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => { try { fileInputRef.current?.focus(); fileInputRef.current?.click(); } catch (err) { console.error('File picker failed', err); try { fileInputRef.current?.click(); } catch {} } }}
                      className="text-purple-600 hover:text-purple-700 text-xs h-7"
                    >
                      <Upload className="w-3 h-3 mr-1" />
                      Change
                    </Button>
                  </label>
                </div>
                <div className="relative w-full h-64 md:h-80 overflow-hidden rounded-lg bg-gray-100">
                  <img
                    src={selectedImage}
                    alt="Uploaded room"
                    className="w-full h-full object-contain"
                  />
                </div>
                <input
                  id="room-upload-file-input"
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="sr-only"
                />
              </CardContent>
            </Card>

            {/* Transformation Options */}
            <Card className="bg-white/80 backdrop-blur shadow-lg">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">How would you like to transform your room?</h3>
                <p className="text-sm text-gray-600 mb-6">Choose a preset option or describe your vision</p>

                {/* Preset Options Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
                  {PRESET_OPTIONS.map((preset) => (
                    <button
                      key={preset.id}
                      onClick={() => handlePresetSelect(preset)}
                      disabled={isTransforming}
                      className={`p-4 rounded-lg border-2 transition-all text-center ${
                        selectedPreset === preset.id
                          ? 'border-purple-600 bg-purple-50'
                          : 'border-gray-200 hover:border-purple-300 bg-white'
                      } ${isTransforming ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <div className="flex justify-center mb-2 text-purple-600">
                        {preset.icon}
                      </div>
                      <h4 className="font-semibold text-sm text-gray-900 mb-1">{preset.name}</h4>
                      <p className="text-xs text-gray-600">{preset.description}</p>
                    </button>
                  ))}
                </div>

                {/* Custom Prompt Input */}
                {selectedPreset === 'custom' && (
                  <div className="space-y-3 mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <label className="block text-sm font-semibold text-gray-900">
                      Describe your design vision
                    </label>
                    <textarea
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="E.g., 'Modern minimalist kitchen with white cabinets, marble countertops, and stainless steel appliances'"
                      className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 resize-none"
                      rows={4}
                    />
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-600">{customPrompt.length} characters</span>
                      <Button
                        onClick={() => handleTransform(customPrompt)}
                        disabled={isTransforming || !customPrompt.trim()}
                        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white gap-2"
                      >
                        <Sparkles className="w-4 h-4" />
                        Generate Design
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Transformation Results */}
        {selectedImage && transformationStep === 'results' && (
          <div className="space-y-6">
            {isTransforming ? (
              <Card className="bg-white/80 backdrop-blur shadow-lg">
                <CardContent className="p-12 text-center">
                  <Loader2 className="w-12 h-12 mx-auto text-purple-600 mb-4 animate-spin" />
                  <p className="text-lg font-semibold text-gray-900 mb-2">Generating your design...</p>
                  <p className="text-sm text-gray-600">This usually takes 30-45 seconds</p>
                </CardContent>
              </Card>
            ) : resultImages.length > 0 ? (
              <>
                {/* Before/After Comparison */}
                <Card className="bg-white/80 backdrop-blur shadow-lg">
                  <CardContent className="p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Before & After</h3>
                    <BeforeAfterSlider
                      beforeImage={selectedImage}
                      afterImage={resultImages[0]}
                      beforeLabel="Original"
                      afterLabel="Transformed"
                    />
                  </CardContent>
                </Card>

                {/* Transformation Summary */}
                {summary && (
                  <Card className="bg-white/80 backdrop-blur shadow-lg">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">Transformation Summary</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(summary).map(([key, value]: [string, any]) => (
                          <div key={key} className="p-3 bg-purple-50 rounded-lg">
                            <p className="text-xs font-semibold text-purple-600 uppercase mb-1">{key.replace(/_/g, ' ')}</p>
                            <p className="text-sm text-gray-900">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Product Recommendations (Grounding Results) */}
                {products && products.length > 0 && (
                  <Card className="bg-white/80 backdrop-blur shadow-lg">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Package className="w-5 h-5 text-purple-600" />
                        Recommended Products
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {products.map((product, idx) => (
                          <div key={idx} className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                            <h4 className="font-semibold text-sm text-gray-900 mb-1">{product.name || product.title}</h4>
                            <p className="text-xs text-gray-600 mb-2">{product.description || product.snippet}</p>
                            {product.price && <p className="text-sm font-bold text-purple-600 mb-2">{product.price}</p>}
                            {product.link && (
                              <a
                                href={product.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                              >
                                View Product <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* All Variations */}
                {resultImages.length > 1 && (
                  <Card className="bg-white/80 backdrop-blur shadow-lg">
                    <CardContent className="p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">All Design Variations</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {resultImages.map((url, index) => (
                          <div key={index} className="rounded-lg overflow-hidden bg-gray-100">
                            <img
                              src={url}
                              alt={`Variation ${index + 1}`}
                              className="w-full h-64 object-cover"
                            />
                            <p className="text-center py-2 font-medium text-gray-700">Variation {index + 1}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2 justify-center">
                  <Button
                    onClick={() => setTransformationStep('options')}
                    variant="outline"
                    className="gap-2"
                  >
                    <ArrowRight className="w-4 h-4" />
                    Try Another
                  </Button>
                  <Button
                    onClick={handleAddToFavorites}
                    variant="outline"
                    className="gap-2"
                  >
                    ⭐ Favorite
                  </Button>
                  <Button
                    onClick={handleDownloadComparison}
                    variant="outline"
                    className="gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </Button>
                  <Button
                    onClick={handleShareDesign}
                    variant="outline"
                    className="gap-2"
                  >
                    <Share2 className="w-4 h-4" />
                    Share
                  </Button>
                  <Button
                    onClick={handleSaveProject}
                    disabled={isSaving}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white gap-2"
                  >
                    <Save className="w-4 h-4" />
                    {isSaving ? 'Saving...' : 'Save'}
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DesignStudioPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading Design Studio...</div>}>
      <DesignStudioContent />
    </Suspense>
  );
}

