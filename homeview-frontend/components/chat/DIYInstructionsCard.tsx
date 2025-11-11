'use client';

import { useState } from 'react';
import { Wrench, Clock, DollarSign, CheckCircle2, Circle, Package, AlertTriangle, Lightbulb, ShoppingCart, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface DIYInstructionsCardProps {
  instructions: {
    title: string;
    difficulty: string;
    estimated_time: string;
    estimated_cost: string;
    materials: string[];
    tools: string[];
    steps: string[];
    safety_tips?: string[];
    pro_tips?: string[];
  };
}

export default function DIYInstructionsCard({ instructions }: DIYInstructionsCardProps) {
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [isExpanded, setIsExpanded] = useState(true);
  const [showMaterials, setShowMaterials] = useState(false);
  const [showTools, setShowTools] = useState(false);

  const toggleStep = (index: number) => {
    const newCompleted = new Set(completedSteps);
    if (newCompleted.has(index)) {
      newCompleted.delete(index);
    } else {
      newCompleted.add(index);
    }
    setCompletedSteps(newCompleted);
  };

  const progress = instructions.steps.length > 0 
    ? (completedSteps.size / instructions.steps.length) * 100 
    : 0;

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'intermediate': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'advanced': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <Card className="bg-gradient-to-br from-blue-500/10 to-green-500/10 border-blue-500/20 overflow-hidden">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
            <Wrench className="w-5 h-5 text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-white mb-1">{instructions.title}</h3>
            <p className="text-sm text-gray-400">
              {instructions.steps.length} steps • {instructions.materials.length} materials
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

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className={`p-2 rounded border ${getDifficultyColor(instructions.difficulty)}`}>
            <div className="text-xs mb-1">Difficulty</div>
            <div className="text-sm font-medium capitalize">{instructions.difficulty}</div>
          </div>
          
          <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded text-blue-400">
            <div className="text-xs mb-1 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Time
            </div>
            <div className="text-sm font-medium">{instructions.estimated_time}</div>
          </div>
          
          <div className="p-2 bg-green-500/10 border border-green-500/20 rounded text-green-400">
            <div className="text-xs mb-1 flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              Cost
            </div>
            <div className="text-sm font-medium">{instructions.estimated_cost}</div>
          </div>
        </div>

        {/* Progress Bar */}
        {instructions.steps.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-400">Your Progress</span>
              <span className="text-white font-medium">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Expanded Content */}
        {isExpanded && (
          <div className="space-y-4">
            {/* Steps */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">Steps</h4>
              <div className="space-y-2">
                {instructions.steps.map((step, index) => {
                  const isCompleted = completedSteps.has(index);
                  
                  return (
                    <button
                      key={index}
                      onClick={() => toggleStep(index)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        isCompleted
                          ? 'bg-green-500/10 border border-green-500/20'
                          : 'bg-gray-800/50 hover:bg-gray-800'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isCompleted ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-400'
                        }`}>
                          {isCompleted ? (
                            <CheckCircle2 className="w-4 h-4" />
                          ) : (
                            <span className="text-xs font-medium">{index + 1}</span>
                          )}
                        </div>
                        <span className={`text-sm flex-1 ${
                          isCompleted ? 'line-through text-gray-500' : 'text-gray-300'
                        }`}>
                          {step}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Materials */}
            <div>
              <button
                onClick={() => setShowMaterials(!showMaterials)}
                className="w-full flex items-center justify-between text-sm font-semibold text-white mb-2 hover:text-blue-400 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  Materials ({instructions.materials.length})
                </span>
                {showMaterials ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
              
              {showMaterials && (
                <div className="space-y-1 mb-2">
                  {instructions.materials.map((material, idx) => (
                    <div key={idx} className="p-2 bg-gray-800/50 rounded text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span className="flex-1">{material}</span>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2"
                  >
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    Add to Shopping List
                  </Button>
                </div>
              )}
            </div>

            {/* Tools */}
            <div>
              <button
                onClick={() => setShowTools(!showTools)}
                className="w-full flex items-center justify-between text-sm font-semibold text-white mb-2 hover:text-blue-400 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Wrench className="w-4 h-4" />
                  Tools ({instructions.tools.length})
                </span>
                {showTools ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
              
              {showTools && (
                <div className="space-y-1">
                  {instructions.tools.map((tool, idx) => (
                    <div key={idx} className="p-2 bg-gray-800/50 rounded text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-green-400 mt-0.5">•</span>
                      <span className="flex-1">{tool}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Safety Tips */}
            {instructions.safety_tips && instructions.safety_tips.length > 0 && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <h4 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Safety Tips
                </h4>
                <ul className="space-y-1">
                  {instructions.safety_tips.map((tip, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-red-400 mt-0.5">⚠️</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Pro Tips */}
            {instructions.pro_tips && instructions.pro_tips.length > 0 && (
              <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <h4 className="text-sm font-semibold text-yellow-400 mb-2 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4" />
                  Pro Tips
                </h4>
                <ul className="space-y-1">
                  {instructions.pro_tips.map((tip, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-yellow-400 mt-0.5">💡</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

