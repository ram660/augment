'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Palette, Upload, Sparkles, Image as ImageIcon, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { designAPI } from '@/lib/api/design';
import { DESIGN_STYLES } from '@/lib/types/design';
import type { DesignStyle } from '@/lib/types/design';

export default function DesignStudioPage() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<DesignStyle | null>(null);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [useCustomPrompt, setUseCustomPrompt] = useState<boolean>(false);
  const [isTransforming, setIsTransforming] = useState(false);

  // Fetch user's transformations
  const { data: transformations = [], isLoading } = useQuery({
    queryKey: ['transformations'],
    queryFn: designAPI.getAllTransformations,
  });

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleTransform = async () => {
    if (!selectedImage) return;
    if (!useCustomPrompt && !selectedStyle) return;
    if (useCustomPrompt && !customPrompt.trim()) return;

    setIsTransforming(true);
    // TODO: Implement transformation
    setTimeout(() => {
      setIsTransforming(false);
    }, 3000);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
            <Palette className="w-6 h-6 text-white" />
          </div>
          AI Design Studio
        </h1>
        <p className="text-gray-600 mt-2">
          Transform your rooms with AI-powered design in 40+ styles
        </p>
      </div>

      {/* Main Design Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Panel - Upload & Original */}
        <Card>
          <CardHeader>
            <CardTitle>Original Image</CardTitle>
            <CardDescription>Upload a photo of your room</CardDescription>
          </CardHeader>
          <CardContent>
            {selectedImage ? (
              <div className="space-y-4">
                <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    src={selectedImage}
                    alt="Original room"
                    className="w-full h-full object-cover"
                  />
                </div>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setSelectedImage(null)}
                >
                  Change Image
                </Button>
              </div>
            ) : (
              <label className="block">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-primary hover:bg-blue-50 transition-colors">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-700 font-medium mb-1">
                    Click to upload room photo
                  </p>
                  <p className="text-sm text-gray-500">
                    PNG, JPG up to 10MB
                  </p>
                </div>
              </label>
            )}
          </CardContent>
        </Card>

        {/* Right Panel - Transformed */}
        <Card>
          <CardHeader>
            <CardTitle>AI Transformation</CardTitle>
            <CardDescription>See your room in a new style</CardDescription>
          </CardHeader>
          <CardContent>
            {isTransforming ? (
              <div className="aspect-video bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Sparkles className="w-12 h-12 text-purple-600 mx-auto mb-4 animate-pulse" />
                  <p className="text-purple-900 font-medium">Transforming your room...</p>
                  <p className="text-sm text-purple-700 mt-1">This may take a few moments</p>
                </div>
              </div>
            ) : selectedImage && (selectedStyle || (useCustomPrompt && customPrompt.trim())) ? (
              <div className="space-y-4">
                <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <ImageIcon className="w-12 h-12 mx-auto mb-2" />
                    <p className="text-sm">Click "Transform" to see the result</p>
                  </div>
                </div>
                <Button
                  className="w-full"
                  onClick={handleTransform}
                  disabled={isTransforming}
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  {useCustomPrompt ? 'Apply Custom Changes' : 'Transform Room'}
                </Button>
              </div>
            ) : (
              <div className="aspect-video bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-400">
                  <ArrowRight className="w-12 h-12 mx-auto mb-2" />
                  <p className="text-sm">
                    {useCustomPrompt
                      ? 'Upload an image and describe your changes'
                      : 'Upload an image and select a style'
                    }
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Transformation Mode Toggle */}
      <div className="flex items-center justify-center gap-4 p-4 bg-gray-50 rounded-lg">
        <button
          onClick={() => setUseCustomPrompt(false)}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            !useCustomPrompt
              ? 'bg-white shadow-md text-primary border-2 border-primary'
              : 'bg-transparent text-gray-600 hover:bg-white'
          }`}
        >
          Choose Style
        </button>
        <button
          onClick={() => setUseCustomPrompt(true)}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            useCustomPrompt
              ? 'bg-white shadow-md text-primary border-2 border-primary'
              : 'bg-transparent text-gray-600 hover:bg-white'
          }`}
        >
          Custom Prompt
        </button>
      </div>

      {/* Style Selection */}
      {!useCustomPrompt && (
        <Card>
          <CardHeader>
            <CardTitle>Choose a Design Style</CardTitle>
            <CardDescription>Select from 10 popular interior design styles</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {DESIGN_STYLES.map((style) => (
                <button
                  key={style.value}
                  onClick={() => setSelectedStyle(style.value)}
                  disabled={!selectedImage}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    selectedStyle === style.value
                      ? 'border-primary bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                  } ${!selectedImage ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <p className="font-semibold text-gray-900 mb-1">{style.label}</p>
                  <p className="text-xs text-gray-600">{style.description}</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Custom Prompt Input */}
      {useCustomPrompt && (
        <Card>
          <CardHeader>
            <CardTitle>Describe Your Transformation</CardTitle>
            <CardDescription>
              Tell us what changes you want to make to your room. Be specific about colors, materials, furniture, or any other details.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Example: Change the wall color to soft sage green, replace the flooring with light oak hardwood, and add a modern pendant light fixture..."
                disabled={!selectedImage}
                className={`w-full min-h-[150px] p-4 border-2 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                  !selectedImage ? 'opacity-50 cursor-not-allowed bg-gray-50' : 'border-gray-300'
                }`}
              />
              <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <Sparkles className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium mb-1">Tips for better results:</p>
                  <ul className="list-disc list-inside space-y-1 text-blue-800">
                    <li>Be specific about what you want to change</li>
                    <li>Mention colors, materials, and styles</li>
                    <li>Describe the desired mood or atmosphere</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Transformations */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Transformations</h2>
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          </div>
        ) : transformations.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center text-gray-500">
                <Palette className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>No transformations yet</p>
                <p className="text-sm mt-1">Upload an image to get started</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {transformations.slice(0, 6).map((transformation) => (
              <Card key={transformation.id} className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                <div className="aspect-video bg-gray-200">
                  <img
                    src={transformation.transformed_image_url}
                    alt={`${transformation.style} transformation`}
                    className="w-full h-full object-cover"
                  />
                </div>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{transformation.style}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      transformation.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : transformation.status === 'processing'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {transformation.status}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

