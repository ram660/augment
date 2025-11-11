'use client';

import { useState, useRef, useEffect } from 'react';
import { ArrowLeftRight, X, TrendingUp, DollarSign, Wrench, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { designAPI } from '@/lib/api/design';

interface CompareVariationsProps {
  images: string[];
  onClose?: () => void;
}

export default function CompareVariations({ images, onClose }: CompareVariationsProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [compareMode, setCompareMode] = useState<'slider' | 'side-by-side' | 'grid'>('slider');
  const [sliderPosition, setSliderPosition] = useState(50);
  const [selectedImages, setSelectedImages] = useState<[number, number]>([0, Math.min(1, images.length - 1)]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (images.length >= 2) {
      analyzeSequence();
    }
  }, [images]);

  const analyzeSequence = async () => {
    setIsAnalyzing(true);
    try {
      const sequenceType = images.length === 2 ? 'before_after' : 'variations';
      const result = await designAPI.analyzeSequence(images, sequenceType);
      setAnalysis(result.analysis || {});
    } catch (error) {
      console.error('Sequence analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const [leftIdx, rightIdx] = selectedImages;
  const leftImage = images[leftIdx];
  const rightImage = images[rightIdx];

  const renderSliderView = () => (
    <div ref={containerRef} className="relative w-full h-[600px] overflow-hidden rounded-lg">
      {/* Right Image (After) */}
      <img
        src={rightImage}
        alt="After"
        className="absolute inset-0 w-full h-full object-contain"
      />
      
      {/* Left Image (Before) with clip */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
      >
        <img
          src={leftImage}
          alt="Before"
          className="absolute inset-0 w-full h-full object-contain"
        />
      </div>
      
      {/* Slider Handle */}
      <div
        className="absolute top-0 bottom-0 w-1 bg-white shadow-lg cursor-ew-resize z-10"
        style={{ left: `${sliderPosition}%` }}
        onMouseDown={(e) => {
          const container = containerRef.current;
          if (!container) return;
          
          const handleMove = (moveEvent: MouseEvent) => {
            const rect = container.getBoundingClientRect();
            const x = moveEvent.clientX - rect.left;
            const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
            setSliderPosition(percentage);
          };
          
          const handleUp = () => {
            document.removeEventListener('mousemove', handleMove);
            document.removeEventListener('mouseup', handleUp);
          };
          
          document.addEventListener('mousemove', handleMove);
          document.addEventListener('mouseup', handleUp);
        }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full shadow-xl flex items-center justify-center">
          <ArrowLeftRight className="w-6 h-6 text-gray-900" />
        </div>
      </div>
      
      {/* Labels */}
      <div className="absolute top-4 left-4 px-3 py-1.5 bg-black/70 text-white text-sm font-medium rounded-full">
        Before
      </div>
      <div className="absolute top-4 right-4 px-3 py-1.5 bg-black/70 text-white text-sm font-medium rounded-full">
        After
      </div>
    </div>
  );

  const renderSideBySide = () => (
    <div className="grid grid-cols-2 gap-4 h-[600px]">
      <div className="relative rounded-lg overflow-hidden">
        <img src={leftImage} alt="Before" className="w-full h-full object-contain bg-gray-900" />
        <div className="absolute top-4 left-4 px-3 py-1.5 bg-black/70 text-white text-sm font-medium rounded-full">
          Before
        </div>
      </div>
      <div className="relative rounded-lg overflow-hidden">
        <img src={rightImage} alt="After" className="w-full h-full object-contain bg-gray-900" />
        <div className="absolute top-4 right-4 px-3 py-1.5 bg-black/70 text-white text-sm font-medium rounded-full">
          After
        </div>
      </div>
    </div>
  );

  const renderGrid = () => (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {images.map((img, idx) => (
        <div
          key={idx}
          className={`relative rounded-lg overflow-hidden cursor-pointer transition-all ${
            selectedImages.includes(idx) ? 'ring-4 ring-blue-500' : 'hover:ring-2 ring-gray-600'
          }`}
          onClick={() => {
            if (selectedImages.includes(idx)) {
              // Deselect
              const newSelection = selectedImages.filter(i => i !== idx);
              if (newSelection.length === 0) {
                setSelectedImages([idx, (idx + 1) % images.length]);
              } else {
                setSelectedImages([newSelection[0], idx === selectedImages[0] ? selectedImages[1] : selectedImages[0]] as [number, number]);
              }
            } else {
              // Select
              setSelectedImages([selectedImages[1], idx]);
            }
          }}
        >
          <img src={img} alt={`Variation ${idx + 1}`} className="w-full h-48 object-cover" />
          <div className="absolute top-2 left-2 px-2 py-1 bg-black/70 text-white text-xs font-medium rounded">
            #{idx + 1}
          </div>
          {selectedImages.includes(idx) && (
            <div className="absolute inset-0 bg-blue-500/20 flex items-center justify-center">
              <div className="px-3 py-1.5 bg-blue-500 text-white text-sm font-medium rounded-full">
                Selected
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4">
      <div className="w-full h-full max-w-7xl max-h-[95vh] flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <ArrowLeftRight className="w-6 h-6" />
              Compare Variations
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              {images.length} variations • Analyzing changes and improvements
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* View Mode Toggles */}
            <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
              <Button
                size="sm"
                variant={compareMode === 'slider' ? 'default' : 'ghost'}
                onClick={() => setCompareMode('slider')}
                className="text-xs"
              >
                Slider
              </Button>
              <Button
                size="sm"
                variant={compareMode === 'side-by-side' ? 'default' : 'ghost'}
                onClick={() => setCompareMode('side-by-side')}
                className="text-xs"
              >
                Side-by-Side
              </Button>
              <Button
                size="sm"
                variant={compareMode === 'grid' ? 'default' : 'ghost'}
                onClick={() => setCompareMode('grid')}
                className="text-xs"
              >
                Grid
              </Button>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="text-gray-400 hover:text-white">
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        <div className="flex-1 flex gap-4 overflow-hidden">
          {/* Main Comparison View */}
          <div className="flex-1 flex flex-col gap-4">
            {compareMode === 'slider' && renderSliderView()}
            {compareMode === 'side-by-side' && renderSideBySide()}
            {compareMode === 'grid' && renderGrid()}
            
            {/* Image Selector (for slider/side-by-side modes) */}
            {compareMode !== 'grid' && images.length > 2 && (
              <div className="flex items-center gap-2 justify-center">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedImages([Math.max(0, leftIdx - 1), rightIdx])}
                  disabled={leftIdx === 0}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-400">
                  Comparing #{leftIdx + 1} vs #{rightIdx + 1}
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedImages([leftIdx, Math.min(images.length - 1, rightIdx + 1)])}
                  disabled={rightIdx === images.length - 1}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Analysis Sidebar */}
          <Card className="w-80 bg-gray-900 border-gray-800 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-800">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Analysis
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {isAnalyzing ? (
                <div className="text-center text-gray-400 py-8">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
                  <p className="text-sm">Analyzing changes...</p>
                </div>
              ) : analysis ? (
                <>
                  {/* Changes Made */}
                  {analysis.changes_made && (
                    <div>
                      <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        Changes Made
                      </h4>
                      <ul className="space-y-1">
                        {analysis.changes_made.map((change: string, idx: number) => (
                          <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-blue-400 mt-1">•</span>
                            <span>{change}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Cost Estimate */}
                  {analysis.estimated_cost_range && (
                    <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                      <h4 className="text-sm font-semibold text-green-400 mb-1 flex items-center gap-2">
                        <DollarSign className="w-4 h-4" />
                        Estimated Cost
                      </h4>
                      <p className="text-lg font-bold text-white">{analysis.estimated_cost_range}</p>
                    </div>
                  )}

                  {/* DIY Feasibility */}
                  {analysis.diy_feasibility && (
                    <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <h4 className="text-sm font-semibold text-blue-400 mb-1 flex items-center gap-2">
                        <Wrench className="w-4 h-4" />
                        DIY Feasibility
                      </h4>
                      <p className="text-lg font-bold text-white capitalize">{analysis.diy_feasibility}</p>
                    </div>
                  )}

                  {/* Improvements */}
                  {analysis.improvements && (
                    <div>
                      <h4 className="text-sm font-semibold text-white mb-2">Improvements</h4>
                      <ul className="space-y-1">
                        {analysis.improvements.map((improvement: string, idx: number) => (
                          <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="text-green-400 mt-1">✓</span>
                            <span>{improvement}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-gray-400 text-center py-8">
                  No analysis available
                </p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

