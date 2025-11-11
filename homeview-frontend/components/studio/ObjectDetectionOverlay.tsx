'use client';

import { useState, useRef, useEffect } from 'react';
import { Scan, X, Ruler, Package, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { designAPI } from '@/lib/api/design';

interface BoundingBox {
  y_min: number;
  x_min: number;
  y_max: number;
  x_max: number;
}

interface DetectedObject {
  label: string;
  confidence: number;
  bounding_box: BoundingBox;
}

interface ObjectDetectionOverlayProps {
  imageUrl: string;
  onClose?: () => void;
}

export default function ObjectDetectionOverlay({ imageUrl, onClose }: ObjectDetectionOverlayProps) {
  const [isDetecting, setIsDetecting] = useState(false);
  const [objects, setObjects] = useState<DetectedObject[]>([]);
  const [selectedObject, setSelectedObject] = useState<number | null>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [hoveredObject, setHoveredObject] = useState<number | null>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    detectObjects();
  }, [imageUrl]);

  const detectObjects = async () => {
    setIsDetecting(true);
    try {
      const result = await designAPI.analyzeBoundingBoxes(imageUrl);
      setObjects(result.objects || []);
      setImageDimensions(result.image_dimensions || { width: 0, height: 0 });
    } catch (error) {
      console.error('Object detection failed:', error);
    } finally {
      setIsDetecting(false);
    }
  };

  const getPixelBox = (bbox: BoundingBox) => {
    if (!imageRef.current) return { x: 0, y: 0, width: 0, height: 0 };
    
    const imgWidth = imageRef.current.offsetWidth;
    const imgHeight = imageRef.current.offsetHeight;
    
    return {
      x: (bbox.x_min / 1000) * imgWidth,
      y: (bbox.y_min / 1000) * imgHeight,
      width: ((bbox.x_max - bbox.x_min) / 1000) * imgWidth,
      height: ((bbox.y_max - bbox.y_min) / 1000) * imgHeight,
    };
  };

  const getDimensions = (bbox: BoundingBox) => {
    const widthNorm = (bbox.x_max - bbox.x_min) / 1000;
    const heightNorm = (bbox.y_max - bbox.y_min) / 1000;
    
    // Estimate real-world dimensions (assuming standard room height ~2.4m)
    const estimatedHeight = 2.4 * heightNorm;
    const estimatedWidth = 2.4 * widthNorm;
    
    return {
      width: estimatedWidth.toFixed(2),
      height: estimatedHeight.toFixed(2),
    };
  };

  const getObjectColor = (index: number) => {
    const colors = [
      'rgb(59, 130, 246)',   // blue
      'rgb(16, 185, 129)',   // green
      'rgb(245, 158, 11)',   // amber
      'rgb(239, 68, 68)',    // red
      'rgb(168, 85, 247)',   // purple
      'rgb(236, 72, 153)',   // pink
    ];
    return colors[index % colors.length];
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4">
      <div className="relative w-full h-full max-w-7xl max-h-[90vh] flex gap-4">
        {/* Main Image with Overlays */}
        <div ref={containerRef} className="relative flex-1 flex items-center justify-center">
          <div className="relative inline-block">
            <img
              ref={imageRef}
              src={imageUrl}
              alt="Room analysis"
              className="max-w-full max-h-[85vh] object-contain rounded-lg"
            />
            
            {/* Bounding Boxes */}
            {!isDetecting && objects.map((obj, index) => {
              const pixelBox = getPixelBox(obj.bounding_box);
              const color = getObjectColor(index);
              const isSelected = selectedObject === index;
              const isHovered = hoveredObject === index;
              const isActive = isSelected || isHovered;
              
              return (
                <div
                  key={index}
                  className="absolute cursor-pointer transition-all duration-200"
                  style={{
                    left: `${pixelBox.x}px`,
                    top: `${pixelBox.y}px`,
                    width: `${pixelBox.width}px`,
                    height: `${pixelBox.height}px`,
                    border: `${isActive ? '3' : '2'}px solid ${color}`,
                    backgroundColor: isActive ? `${color}20` : 'transparent',
                    boxShadow: isActive ? `0 0 20px ${color}80` : 'none',
                  }}
                  onClick={() => setSelectedObject(isSelected ? null : index)}
                  onMouseEnter={() => setHoveredObject(index)}
                  onMouseLeave={() => setHoveredObject(null)}
                >
                  {/* Label Badge */}
                  <div
                    className="absolute -top-8 left-0 px-2 py-1 rounded text-xs font-medium text-white whitespace-nowrap shadow-lg"
                    style={{ backgroundColor: color }}
                  >
                    {obj.label} {Math.round(obj.confidence * 100)}%
                  </div>
                  
                  {/* Dimension Lines (when active) */}
                  {isActive && (
                    <>
                      {/* Width indicator */}
                      <div className="absolute -bottom-6 left-0 right-0 flex items-center justify-center">
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-black/80 rounded text-xs text-white">
                          <Ruler className="w-3 h-3" />
                          {getDimensions(obj.bounding_box).width}m
                        </div>
                      </div>
                      
                      {/* Height indicator */}
                      <div className="absolute -right-12 top-0 bottom-0 flex items-center justify-center">
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-black/80 rounded text-xs text-white rotate-90">
                          <Ruler className="w-3 h-3" />
                          {getDimensions(obj.bounding_box).height}m
                        </div>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
            
            {/* Loading Overlay */}
            {isDetecting && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center rounded-lg">
                <div className="text-center text-white">
                  <Scan className="w-12 h-12 animate-pulse mx-auto mb-2" />
                  <p className="text-sm">Detecting objects...</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar with Object List */}
        <Card className="w-80 bg-gray-900 border-gray-800 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Scan className="w-5 h-5" />
                Detected Objects
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                {objects.length} items found
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {objects.map((obj, index) => {
              const color = getObjectColor(index);
              const dims = getDimensions(obj.bounding_box);
              const isSelected = selectedObject === index;
              
              return (
                <div
                  key={index}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    isSelected ? 'bg-gray-800 ring-2' : 'bg-gray-800/50 hover:bg-gray-800'
                  }`}
                  style={{
                    borderColor: isSelected ? color : 'transparent',
                    borderWidth: isSelected ? '2px' : '0px'
                  }}
                  onClick={() => setSelectedObject(isSelected ? null : index)}
                  onMouseEnter={() => setHoveredObject(index)}
                  onMouseLeave={() => setHoveredObject(null)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: color }}
                      />
                      <span className="font-medium text-white">{obj.label}</span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {Math.round(obj.confidence * 100)}%
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1 text-gray-400">
                      <Ruler className="w-3 h-3" />
                      <span>W: {dims.width}m</span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-400">
                      <Maximize2 className="w-3 h-3" />
                      <span>H: {dims.height}m</span>
                    </div>
                  </div>
                  
                  <div className="mt-2 pt-2 border-t border-gray-700">
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                      <Package className="w-3 h-3" />
                      <span>Area: {(parseFloat(dims.width) * parseFloat(dims.height)).toFixed(2)}m²</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div className="p-4 border-t border-gray-800 space-y-2">
            <Button
              onClick={detectObjects}
              disabled={isDetecting}
              className="w-full"
              variant="outline"
            >
              <Scan className="w-4 h-4 mr-2" />
              Re-scan Objects
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

