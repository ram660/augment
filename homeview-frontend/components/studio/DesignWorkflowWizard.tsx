'use client';

import { useState } from 'react';
import { Check, ChevronRight, Home, Palette, Ruler, DollarSign, Calendar, Users } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  icon: any;
  completed: boolean;
}

interface DesignWorkflowWizardProps {
  onStepSelect: (stepId: string) => void;
  currentStep?: string;
}

export default function DesignWorkflowWizard({ onStepSelect, currentStep }: DesignWorkflowWizardProps) {
  const [steps, setSteps] = useState<WorkflowStep[]>([
    {
      id: 'room-selection',
      title: 'Select Your Space',
      description: 'Choose the room you want to transform',
      icon: Home,
      completed: false,
    },
    {
      id: 'style-exploration',
      title: 'Explore Styles',
      description: 'Browse design styles and get inspired',
      icon: Palette,
      completed: false,
    },
    {
      id: 'measurements',
      title: 'Room Analysis',
      description: 'AI analyzes dimensions and materials',
      icon: Ruler,
      completed: false,
    },
    {
      id: 'design-generation',
      title: 'Generate Designs',
      description: 'Create multiple design variations',
      icon: Palette,
      completed: false,
    },
    {
      id: 'budget-planning',
      title: 'Budget & Materials',
      description: 'Estimate costs and materials needed',
      icon: DollarSign,
      completed: false,
    },
    {
      id: 'timeline',
      title: 'Implementation Plan',
      description: 'Get step-by-step DIY or contractor guide',
      icon: Calendar,
      completed: false,
    },
    {
      id: 'share-feedback',
      title: 'Share & Collaborate',
      description: 'Get feedback from family or contractors',
      icon: Users,
      completed: false,
    },
  ]);

  const handleStepClick = (stepId: string) => {
    onStepSelect(stepId);
  };

  const currentStepIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
      <CardContent className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-bold text-gray-800 mb-1">Your Design Journey</h3>
          <p className="text-sm text-gray-600">Follow these steps to create your perfect space</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-600">Progress</span>
            <span className="text-xs font-bold text-purple-600">
              {steps.filter(s => s.completed).length} / {steps.length}
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
              style={{ width: `${(steps.filter(s => s.completed).length / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = step.id === currentStep;
            const isPast = index < currentStepIndex;
            
            return (
              <button
                key={step.id}
                onClick={() => handleStepClick(step.id)}
                className={`w-full text-left p-3 rounded-lg transition-all ${
                  isActive 
                    ? 'bg-white shadow-md ring-2 ring-purple-500' 
                    : isPast
                    ? 'bg-white/50 hover:bg-white/70'
                    : 'bg-white/30 hover:bg-white/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Icon/Status */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    step.completed 
                      ? 'bg-green-500 text-white' 
                      : isActive
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}>
                    {step.completed ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <Icon className="w-5 h-5" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className={`text-sm font-semibold ${
                        isActive ? 'text-purple-700' : 'text-gray-800'
                      }`}>
                        {step.title}
                      </h4>
                      {isActive && (
                        <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">
                          Current
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-0.5">{step.description}</p>
                  </div>

                  {/* Arrow */}
                  <ChevronRight className={`w-5 h-5 flex-shrink-0 ${
                    isActive ? 'text-purple-500' : 'text-gray-400'
                  }`} />
                </div>
              </button>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="mt-6 pt-6 border-t border-purple-200">
          <div className="grid grid-cols-2 gap-2">
            <Button 
              variant="outline" 
              size="sm"
              className="text-xs"
              onClick={() => onStepSelect('skip-to-design')}
            >
              Skip to Design
            </Button>
            <Button 
              size="sm"
              className="text-xs bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              onClick={() => onStepSelect('ai-assistant')}
            >
              Ask AI Assistant
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

