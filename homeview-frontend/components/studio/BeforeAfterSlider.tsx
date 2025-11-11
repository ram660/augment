'use client';

import { useState, useRef, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Share2, Maximize2 } from 'lucide-react';

interface BeforeAfterSliderProps {
  beforeImage: string;
  afterImage: string;
  beforeLabel?: string;
  afterLabel?: string;
}

export default function BeforeAfterSlider({ 
  beforeImage, 
  afterImage,
  beforeLabel = 'Before',
  afterLabel = 'After'
}: BeforeAfterSliderProps) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = (x / rect.width) * 100;
    
    setSliderPosition(Math.max(0, Math.min(100, percentage)));
  };

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!isDragging) return;
    handleMove(e.touches[0].clientX);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove);
      document.addEventListener('touchend', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDragging]);

  const handleDownload = async () => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const beforeImg = new Image();
      const afterImg = new Image();

      beforeImg.crossOrigin = 'anonymous';
      afterImg.crossOrigin = 'anonymous';

      await Promise.all([
        new Promise((resolve) => {
          beforeImg.onload = resolve;
          beforeImg.src = beforeImage;
        }),
        new Promise((resolve) => {
          afterImg.onload = resolve;
          afterImg.src = afterImage;
        }),
      ]);

      canvas.width = beforeImg.width * 2;
      canvas.height = beforeImg.height;

      ctx.drawImage(beforeImg, 0, 0);
      ctx.drawImage(afterImg, beforeImg.width, 0);

      ctx.font = 'bold 24px Arial';
      ctx.fillStyle = 'white';
      ctx.strokeStyle = 'black';
      ctx.lineWidth = 3;

      ctx.strokeText(beforeLabel, 20, 40);
      ctx.fillText(beforeLabel, 20, 40);

      ctx.strokeText(afterLabel, beforeImg.width + 20, 40);
      ctx.fillText(afterLabel, beforeImg.width + 20, 40);

      canvas.toBlob((blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'homeview-comparison.png';
        a.click();
        URL.revokeObjectURL(url);
      });
    } catch (error) {
      console.error('Failed to download:', error);
      alert('Failed to download. Please try again.');
    }
  };

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'HomeView AI Design',
          text: 'Check out my room transformation!',
          url: window.location.href,
        });
      } else {
        await navigator.clipboard.writeText(window.location.href);
        alert('Link copied to clipboard!');
      }
    } catch (error) {
      console.error('Failed to share:', error);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-gray-800">Before & After</h3>
          <p className="text-sm text-gray-600">Drag the slider to compare</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Comparison Slider */}
      <Card className="overflow-hidden">
        <div 
          ref={containerRef}
          className="relative aspect-video bg-gray-900 cursor-ew-resize select-none"
          onMouseDown={handleMouseDown}
          onTouchStart={handleMouseDown}
        >
          {/* After Image (Full) */}
          <div className="absolute inset-0">
            <img 
              src={afterImage} 
              alt={afterLabel}
              className="w-full h-full object-cover"
              draggable={false}
            />
            {/* After Label */}
            <div className="absolute top-4 right-4 px-3 py-1.5 bg-green-500 text-white text-sm font-bold rounded-full shadow-lg">
              {afterLabel}
            </div>
          </div>

          {/* Before Image (Clipped) */}
          <div 
            className="absolute inset-0 overflow-hidden"
            style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
          >
            <img 
              src={beforeImage} 
              alt={beforeLabel}
              className="w-full h-full object-cover"
              draggable={false}
            />
            {/* Before Label */}
            <div className="absolute top-4 left-4 px-3 py-1.5 bg-gray-700 text-white text-sm font-bold rounded-full shadow-lg">
              {beforeLabel}
            </div>
          </div>

          {/* Slider Handle */}
          <div 
            className="absolute top-0 bottom-0 w-1 bg-white shadow-lg"
            style={{ left: `${sliderPosition}%` }}
          >
            {/* Handle Circle */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full shadow-xl flex items-center justify-center cursor-ew-resize">
              <div className="flex gap-1">
                <div className="w-0.5 h-6 bg-gray-400 rounded-full"></div>
                <div className="w-0.5 h-6 bg-gray-400 rounded-full"></div>
              </div>
            </div>
          </div>

          {/* Hover Instruction */}
          {!isDragging && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-black/70 text-white text-xs rounded-full pointer-events-none">
              ← Drag to compare →
            </div>
          )}
        </div>
      </Card>

      {/* Quick Comparison Stats */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="p-3 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="text-xs text-gray-600 mb-1">Style Change</div>
          <div className="text-sm font-bold text-blue-700">Modern → Minimalist</div>
        </Card>
        <Card className="p-3 bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
          <div className="text-xs text-gray-600 mb-1">Color Palette</div>
          <div className="text-sm font-bold text-purple-700">5 Colors Updated</div>
        </Card>
        <Card className="p-3 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="text-xs text-gray-600 mb-1">Est. Cost</div>
          <div className="text-sm font-bold text-green-700">$2,450</div>
        </Card>
      </div>

      {/* Key Changes List */}
      <Card className="p-4">
        <div className="text-sm font-semibold text-gray-700 mb-3">Key Changes Made</div>
        <div className="space-y-2">
          {[
            { icon: '🎨', text: 'Walls painted in soft gray (#E5E5E5)' },
            { icon: '🪵', text: 'Light oak flooring installed' },
            { icon: '💡', text: 'Modern pendant lighting added' },
            { icon: '🛋️', text: 'Minimalist furniture arrangement' },
            { icon: '🌿', text: 'Indoor plants for natural touch' },
          ].map((change, idx) => (
            <div key={idx} className="flex items-center gap-3 text-sm">
              <span className="text-xl">{change.icon}</span>
              <span className="text-gray-700">{change.text}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2 mb-2">
        <Button variant="outline" onClick={handleDownload}>
          <Download className="w-4 h-4 mr-2" />
          Download
        </Button>
        <Button variant="outline" onClick={handleShare}>
          <Share2 className="w-4 h-4 mr-2" />
          Share
        </Button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline">
          Try Another Style
        </Button>
        <Button className="bg-gradient-to-r from-purple-500 to-pink-500">
          Get Implementation Guide
        </Button>
      </div>
    </div>
  );
}

