'use client';

import { useState, useRef } from 'react';
import { ArrowLeftRight, TrendingUp, DollarSign, Wrench, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface BeforeAfterComparisonProps {
  beforeImage: string;
  afterImage: string;
  analysis?: {
    changes_made?: string[];
    improvements?: string[];
    estimated_cost_range?: string;
    diy_feasibility?: 'low' | 'medium' | 'high';
  };
}

export default function BeforeAfterComparison({ beforeImage, afterImage, analysis }: BeforeAfterComparisonProps) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isExpanded, setIsExpanded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const getFeasibilityColor = (feasibility?: string) => {
    switch (feasibility) {
      case 'low': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'high': return 'text-green-400 bg-green-500/10 border-green-500/20';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
  };

  return (
    <Card className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/20 overflow-hidden">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
            <ArrowLeftRight className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-white mb-1">Before & After Comparison</h3>
            <p className="text-sm text-gray-400">
              {analysis?.changes_made?.length || 0} changes detected
            </p>
          </div>
          {analysis && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-400 hover:text-white"
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          )}
        </div>

        {/* Slider Comparison */}
        <div ref={containerRef} className="relative w-full h-[400px] rounded-lg overflow-hidden mb-4">
          {/* After Image (Right) */}
          <img
            src={afterImage}
            alt="After"
            className="absolute inset-0 w-full h-full object-cover"
          />
          
          {/* Before Image (Left) with clip */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
          >
            <img
              src={beforeImage}
              alt="Before"
              className="absolute inset-0 w-full h-full object-cover"
            />
          </div>
          
          {/* Slider Handle */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-white shadow-2xl cursor-ew-resize z-10"
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
            onTouchStart={(e) => {
              const container = containerRef.current;
              if (!container) return;
              
              const handleMove = (moveEvent: TouchEvent) => {
                const rect = container.getBoundingClientRect();
                const x = moveEvent.touches[0].clientX - rect.left;
                const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
                setSliderPosition(percentage);
              };
              
              const handleEnd = () => {
                document.removeEventListener('touchmove', handleMove);
                document.removeEventListener('touchend', handleEnd);
              };
              
              document.addEventListener('touchmove', handleMove);
              document.addEventListener('touchend', handleEnd);
            }}
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full shadow-2xl flex items-center justify-center">
              <ArrowLeftRight className="w-6 h-6 text-gray-900" />
            </div>
          </div>
          
          {/* Labels */}
          <div className="absolute top-4 left-4 px-3 py-1.5 bg-black/80 text-white text-sm font-medium rounded-full backdrop-blur-sm">
            Before
          </div>
          <div className="absolute top-4 right-4 px-3 py-1.5 bg-black/80 text-white text-sm font-medium rounded-full backdrop-blur-sm">
            After
          </div>
        </div>

        {/* Quick Stats */}
        {analysis && (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {analysis.estimated_cost_range && (
              <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="text-xs text-green-400 mb-1 flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  Estimated Cost
                </div>
                <div className="text-sm font-semibold text-white">{analysis.estimated_cost_range}</div>
              </div>
            )}
            
            {analysis.diy_feasibility && (
              <div className={`p-3 rounded-lg border ${getFeasibilityColor(analysis.diy_feasibility)}`}>
                <div className="text-xs mb-1 flex items-center gap-1">
                  <Wrench className="w-3 h-3" />
                  DIY Feasibility
                </div>
                <div className="text-sm font-semibold capitalize">{analysis.diy_feasibility}</div>
              </div>
            )}
          </div>
        )}

        {/* Expanded Analysis */}
        {isExpanded && analysis && (
          <div className="space-y-4 pt-4 border-t border-gray-700">
            {/* Changes Made */}
            {analysis.changes_made && analysis.changes_made.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Changes Made
                </h4>
                <ul className="space-y-2">
                  {analysis.changes_made.map((change, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2 p-2 bg-gray-800/50 rounded">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span>{change}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Improvements */}
            {analysis.improvements && analysis.improvements.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Improvements
                </h4>
                <ul className="space-y-2">
                  {analysis.improvements.map((improvement, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2 p-2 bg-green-500/10 rounded">
                      <span className="text-green-400 mt-0.5">✓</span>
                      <span>{improvement}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* ROI Estimate */}
            {analysis.estimated_cost_range && (
              <div className="p-4 bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-lg">
                <h4 className="text-sm font-semibold text-white mb-2">Investment Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Estimated Cost:</span>
                    <span className="text-white font-medium">{analysis.estimated_cost_range}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">DIY Feasibility:</span>
                    <span className="text-white font-medium capitalize">{analysis.diy_feasibility}</span>
                  </div>
                  <div className="pt-2 border-t border-gray-700">
                    <p className="text-xs text-gray-400">
                      {analysis.diy_feasibility === 'high' 
                        ? '💡 Great DIY project! You can save on labor costs.'
                        : analysis.diy_feasibility === 'medium'
                        ? '⚠️ Consider hiring help for complex tasks.'
                        : '🔧 Professional installation recommended.'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-4 pt-4 border-t border-gray-700 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => setSliderPosition(0)}
          >
            Show Before
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => setSliderPosition(100)}
          >
            Show After
          </Button>
        </div>
      </div>
    </Card>
  );
}

