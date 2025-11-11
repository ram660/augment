'use client';

import { useState } from 'react';
import { Play, Clock, Package, Wrench, AlertTriangle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface VideoTutorialCardProps {
  videoUrl: string;
  analysis: {
    raw_text?: string;
    structured?: {
      steps?: Array<{ timestamp: string; instruction: string }>;
      materials?: string[];
      tools?: string[];
      safety_warnings?: string[];
      difficulty?: string;
    };
  };
}

export default function VideoTutorialCard({ videoUrl, analysis }: VideoTutorialCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTimestamp, setActiveTimestamp] = useState<string | null>(null);

  const structured = analysis.structured || {};
  const steps = structured.steps || [];
  const materials = structured.materials || [];
  const tools = structured.tools || [];
  const safetyWarnings = structured.safety_warnings || [];

  // Extract YouTube video ID
  const getYouTubeId = (url: string) => {
    const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
    return match ? match[1] : null;
  };

  const videoId = getYouTubeId(videoUrl);
  const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}` : null;

  const parseTimestamp = (timestamp: string): number => {
    // Parse timestamp like "1:23" or "0:45" to seconds
    const parts = timestamp.split(':').map(Number);
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return 0;
  };

  const jumpToTimestamp = (timestamp: string) => {
    setActiveTimestamp(timestamp);
    const seconds = parseTimestamp(timestamp);
    if (embedUrl && videoId) {
      // Open in new tab with timestamp
      window.open(`https://www.youtube.com/watch?v=${videoId}&t=${seconds}s`, '_blank');
    }
  };

  return (
    <Card className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-purple-500/20 overflow-hidden">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
            <Play className="w-5 h-5 text-purple-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-white mb-1">Video Tutorial Analysis</h3>
            <p className="text-sm text-gray-400">
              {steps.length > 0 ? `${steps.length} steps extracted` : 'Tutorial breakdown'}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-white"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>

        {/* Video Embed */}
        {embedUrl && (
          <div className="relative aspect-video rounded-lg overflow-hidden mb-4 bg-black">
            <iframe
              src={embedUrl}
              className="absolute inset-0 w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {structured.difficulty && (
            <div className="p-2 bg-gray-800/50 rounded text-center">
              <div className="text-xs text-gray-400 mb-1">Difficulty</div>
              <div className="text-sm font-medium text-white capitalize">{structured.difficulty}</div>
            </div>
          )}
          {materials.length > 0 && (
            <div className="p-2 bg-gray-800/50 rounded text-center">
              <div className="text-xs text-gray-400 mb-1">Materials</div>
              <div className="text-sm font-medium text-white">{materials.length}</div>
            </div>
          )}
          {tools.length > 0 && (
            <div className="p-2 bg-gray-800/50 rounded text-center">
              <div className="text-xs text-gray-400 mb-1">Tools</div>
              <div className="text-sm font-medium text-white">{tools.length}</div>
            </div>
          )}
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="space-y-4 pt-4 border-t border-gray-700">
            {/* Steps with Timestamps */}
            {steps.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Step-by-Step Instructions
                </h4>
                <div className="space-y-2">
                  {steps.map((step, idx) => (
                    <button
                      key={idx}
                      onClick={() => jumpToTimestamp(step.timestamp)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        activeTimestamp === step.timestamp
                          ? 'bg-purple-500/20 border border-purple-500/30'
                          : 'bg-gray-800/50 hover:bg-gray-800'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-xs font-mono text-purple-400 mt-0.5 flex-shrink-0">
                          {step.timestamp}
                        </span>
                        <span className="text-sm text-gray-300 flex-1">{step.instruction}</span>
                        <ExternalLink className="w-3 h-3 text-gray-500 flex-shrink-0 mt-1" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Materials */}
            {materials.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  Materials Needed
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {materials.map((material, idx) => (
                    <div key={idx} className="p-2 bg-gray-800/50 rounded text-sm text-gray-300">
                      • {material}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tools */}
            {tools.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Wrench className="w-4 h-4" />
                  Tools Required
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {tools.map((tool, idx) => (
                    <div key={idx} className="p-2 bg-gray-800/50 rounded text-sm text-gray-300">
                      • {tool}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Safety Warnings */}
            {safetyWarnings.length > 0 && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <h4 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Safety Warnings
                </h4>
                <ul className="space-y-1">
                  {safetyWarnings.map((warning, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-red-400 mt-0.5">⚠️</span>
                      <span>{warning}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Raw Text Fallback */}
            {!steps.length && analysis.raw_text && (
              <div className="p-3 bg-gray-800/50 rounded-lg">
                <p className="text-sm text-gray-300 whitespace-pre-wrap">{analysis.raw_text}</p>
              </div>
            )}
          </div>
        )}

        {/* Action Button */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => window.open(videoUrl, '_blank')}
          >
            <Play className="w-4 h-4 mr-2" />
            Watch Full Video
          </Button>
        </div>
      </div>
    </Card>
  );
}

