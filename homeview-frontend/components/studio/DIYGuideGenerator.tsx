'use client';

import { useState } from 'react';
import { Wrench, X, Clock, DollarSign, AlertTriangle, Lightbulb, Package, CheckCircle2, Circle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { designAPI } from '@/lib/api/design';

interface DIYGuideGeneratorProps {
  imageUrl?: string;
  initialPrompt?: string;
  onClose?: () => void;
}

export default function DIYGuideGenerator({ imageUrl, initialPrompt, onClose }: DIYGuideGeneratorProps) {
  const [projectDescription, setProjectDescription] = useState(initialPrompt || '');
  const [isGenerating, setIsGenerating] = useState(false);
  const [guide, setGuide] = useState<any>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const generateGuide = async () => {
    if (!projectDescription.trim()) return;
    
    setIsGenerating(true);
    try {
      const result = await designAPI.generateDIYInstructions(projectDescription, imageUrl);
      setGuide(result.instructions || {});
      setCompletedSteps(new Set());
    } catch (error) {
      console.error('DIY guide generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleStep = (index: number) => {
    const newCompleted = new Set(completedSteps);
    if (newCompleted.has(index)) {
      newCompleted.delete(index);
    } else {
      newCompleted.add(index);
    }
    setCompletedSteps(newCompleted);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner': return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'intermediate': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'advanced': return 'text-red-400 bg-red-500/10 border-red-500/20';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
    }
  };

  const progress = guide?.steps ? (completedSteps.size / guide.steps.length) * 100 : 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4">
      <div className="w-full h-full max-w-6xl max-h-[95vh] flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Wrench className="w-6 h-6" />
              DIY Project Guide
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              Step-by-step instructions with materials and tools
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Input Section */}
        {!guide && (
          <Card className="bg-gray-900 border-gray-800 p-6">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-white mb-2 block">
                  Describe your project
                </label>
                <Textarea
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="E.g., Paint bedroom with accent wall, install floating shelves, refinish hardwood floors..."
                  className="min-h-[100px] bg-gray-800 border-gray-700 text-white"
                />
              </div>
              
              {imageUrl && (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Package className="w-4 h-4" />
                  <span>Reference image attached</span>
                </div>
              )}
              
              <Button
                onClick={generateGuide}
                disabled={isGenerating || !projectDescription.trim()}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Generating Guide...
                  </>
                ) : (
                  <>
                    <Wrench className="w-4 h-4 mr-2" />
                    Generate DIY Guide
                  </>
                )}
              </Button>
            </div>
          </Card>
        )}

        {/* Guide Display */}
        {guide && (
          <div className="flex-1 flex gap-4 overflow-hidden">
            {/* Main Content */}
            <div className="flex-1 overflow-y-auto space-y-4">
              {/* Project Header */}
              <Card className="bg-gray-900 border-gray-800 p-6">
                <h3 className="text-2xl font-bold text-white mb-4">{guide.title}</h3>
                
                <div className="grid grid-cols-3 gap-4">
                  <div className={`p-3 rounded-lg border ${getDifficultyColor(guide.difficulty)}`}>
                    <div className="text-xs font-medium mb-1">Difficulty</div>
                    <div className="text-lg font-bold capitalize">{guide.difficulty}</div>
                  </div>
                  
                  <div className="p-3 rounded-lg border bg-blue-500/10 border-blue-500/20 text-blue-400">
                    <div className="text-xs font-medium mb-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Time
                    </div>
                    <div className="text-lg font-bold">{guide.estimated_time}</div>
                  </div>
                  
                  <div className="p-3 rounded-lg border bg-green-500/10 border-green-500/20 text-green-400">
                    <div className="text-xs font-medium mb-1 flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      Cost
                    </div>
                    <div className="text-lg font-bold">{guide.estimated_cost}</div>
                  </div>
                </div>
                
                {/* Progress Bar */}
                {guide.steps && guide.steps.length > 0 && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-gray-400">Progress</span>
                      <span className="text-white font-medium">{Math.round(progress)}%</span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </Card>

              {/* Steps Timeline */}
              <Card className="bg-gray-900 border-gray-800 p-6">
                <h4 className="text-lg font-semibold text-white mb-4">Step-by-Step Instructions</h4>
                
                <div className="space-y-4">
                  {guide.steps?.map((step: string, index: number) => {
                    const isCompleted = completedSteps.has(index);
                    
                    return (
                      <div key={index} className="flex gap-4">
                        {/* Timeline */}
                        <div className="flex flex-col items-center">
                          <button
                            onClick={() => toggleStep(index)}
                            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                              isCompleted
                                ? 'bg-green-500 text-white'
                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                            }`}
                          >
                            {isCompleted ? (
                              <CheckCircle2 className="w-5 h-5" />
                            ) : (
                              <Circle className="w-5 h-5" />
                            )}
                          </button>
                          {index < guide.steps.length - 1 && (
                            <div className={`w-0.5 flex-1 mt-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-800'}`} style={{ minHeight: '40px' }} />
                          )}
                        </div>
                        
                        {/* Step Content */}
                        <div className={`flex-1 pb-4 ${isCompleted ? 'opacity-60' : ''}`}>
                          <div className="flex items-start justify-between mb-2">
                            <span className="text-sm font-medium text-blue-400">Step {index + 1}</span>
                          </div>
                          <p className={`text-sm ${isCompleted ? 'line-through text-gray-500' : 'text-gray-300'}`}>
                            {step}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Safety Tips */}
              {guide.safety_tips && guide.safety_tips.length > 0 && (
                <Card className="bg-red-500/10 border-red-500/20 p-6">
                  <h4 className="text-lg font-semibold text-red-400 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Safety Tips
                  </h4>
                  <ul className="space-y-2">
                    {guide.safety_tips.map((tip: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                        <span className="text-red-400 mt-1">⚠️</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Pro Tips */}
              {guide.pro_tips && guide.pro_tips.length > 0 && (
                <Card className="bg-yellow-500/10 border-yellow-500/20 p-6">
                  <h4 className="text-lg font-semibold text-yellow-400 mb-3 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5" />
                    Pro Tips
                  </h4>
                  <ul className="space-y-2">
                    {guide.pro_tips.map((tip: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                        <span className="text-yellow-400 mt-1">💡</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>

            {/* Sidebar - Materials & Tools */}
            <div className="w-80 space-y-4 overflow-y-auto">
              {/* Materials */}
              {guide.materials && guide.materials.length > 0 && (
                <Card className="bg-gray-900 border-gray-800 p-4">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Package className="w-4 h-4" />
                    Materials ({guide.materials.length})
                  </h4>
                  <ul className="space-y-2">
                    {guide.materials.map((material: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-300 flex items-start gap-2 p-2 bg-gray-800/50 rounded">
                        <span className="text-blue-400 mt-0.5">•</span>
                        <span className="flex-1">{material}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Tools */}
              {guide.tools && guide.tools.length > 0 && (
                <Card className="bg-gray-900 border-gray-800 p-4">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Wrench className="w-4 h-4" />
                    Tools ({guide.tools.length})
                  </h4>
                  <ul className="space-y-2">
                    {guide.tools.map((tool: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-300 flex items-start gap-2 p-2 bg-gray-800/50 rounded">
                        <span className="text-green-400 mt-0.5">•</span>
                        <span className="flex-1">{tool}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

