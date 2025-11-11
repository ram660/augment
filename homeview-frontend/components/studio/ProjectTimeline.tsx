'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Clock, CheckCircle2, Circle, PlayCircle, Download } from 'lucide-react';

interface TimelinePhase {
  id: string;
  title: string;
  duration: string;
  tasks: TimelineTask[];
  status: 'completed' | 'in-progress' | 'upcoming';
}

interface TimelineTask {
  id: string;
  name: string;
  duration: string;
  difficulty: 'easy' | 'medium' | 'hard';
  diy: boolean;
  estimatedCost: number;
}

interface ProjectTimelineProps {
  projectType?: string;
  onTaskSelect?: (taskId: string) => void;
}

export default function ProjectTimeline({ projectType = 'Room Renovation', onTaskSelect }: ProjectTimelineProps) {
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'checklist'>('timeline');

  const phases: TimelinePhase[] = [
    {
      id: 'planning',
      title: 'Planning & Preparation',
      duration: '3-5 days',
      status: 'completed',
      tasks: [
        { id: 'measure', name: 'Measure room dimensions', duration: '1 hour', difficulty: 'easy', diy: true, estimatedCost: 0 },
        { id: 'budget', name: 'Finalize budget and materials', duration: '2 hours', difficulty: 'easy', diy: true, estimatedCost: 0 },
        { id: 'order', name: 'Order materials and furniture', duration: '1 day', difficulty: 'easy', diy: true, estimatedCost: 2450 },
      ],
    },
    {
      id: 'prep',
      title: 'Room Preparation',
      duration: '1-2 days',
      status: 'in-progress',
      tasks: [
        { id: 'clear', name: 'Clear and protect furniture', duration: '2 hours', difficulty: 'easy', diy: true, estimatedCost: 50 },
        { id: 'repair', name: 'Repair walls and surfaces', duration: '4 hours', difficulty: 'medium', diy: true, estimatedCost: 100 },
        { id: 'prime', name: 'Prime walls if needed', duration: '3 hours', difficulty: 'medium', diy: true, estimatedCost: 80 },
      ],
    },
    {
      id: 'painting',
      title: 'Painting',
      duration: '2-3 days',
      status: 'upcoming',
      tasks: [
        { id: 'tape', name: 'Tape edges and trim', duration: '1 hour', difficulty: 'easy', diy: true, estimatedCost: 20 },
        { id: 'paint-walls', name: 'Paint walls (2 coats)', duration: '8 hours', difficulty: 'medium', diy: true, estimatedCost: 200 },
        { id: 'paint-trim', name: 'Paint trim and details', duration: '4 hours', difficulty: 'medium', diy: true, estimatedCost: 80 },
      ],
    },
    {
      id: 'flooring',
      title: 'Flooring Installation',
      duration: '2-4 days',
      status: 'upcoming',
      tasks: [
        { id: 'remove-old', name: 'Remove old flooring', duration: '4 hours', difficulty: 'hard', diy: false, estimatedCost: 300 },
        { id: 'level', name: 'Level subfloor', duration: '3 hours', difficulty: 'hard', diy: false, estimatedCost: 200 },
        { id: 'install-floor', name: 'Install new flooring', duration: '8 hours', difficulty: 'hard', diy: false, estimatedCost: 800 },
      ],
    },
    {
      id: 'finishing',
      title: 'Finishing Touches',
      duration: '1-2 days',
      status: 'upcoming',
      tasks: [
        { id: 'lighting', name: 'Install light fixtures', duration: '2 hours', difficulty: 'medium', diy: false, estimatedCost: 150 },
        { id: 'furniture', name: 'Arrange furniture', duration: '3 hours', difficulty: 'easy', diy: true, estimatedCost: 0 },
        { id: 'decor', name: 'Add decorative elements', duration: '2 hours', difficulty: 'easy', diy: true, estimatedCost: 300 },
      ],
    },
  ];

  const totalDuration = phases.reduce((sum, phase) => {
    const days = parseInt(phase.duration.split('-')[1] || phase.duration.split('-')[0]);
    return sum + days;
  }, 0);

  const totalCost = phases.reduce((sum, phase) => 
    sum + phase.tasks.reduce((taskSum, task) => taskSum + task.estimatedCost, 0), 0
  );

  const completedTasks = phases.reduce((sum, phase) => 
    sum + (phase.status === 'completed' ? phase.tasks.length : 0), 0
  );

  const totalTasks = phases.reduce((sum, phase) => sum + phase.tasks.length, 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-gray-800">Project Timeline</h3>
          <p className="text-sm text-gray-600">Step-by-step implementation guide</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant={viewMode === 'timeline' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('timeline')}
          >
            <Calendar className="w-4 h-4 mr-2" />
            Timeline
          </Button>
          <Button 
            variant={viewMode === 'checklist' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('checklist')}
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Checklist
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-gray-600">Duration</span>
            </div>
            <div className="text-xl font-bold text-blue-700">{totalDuration} days</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <span className="text-xs text-gray-600">Progress</span>
            </div>
            <div className="text-xl font-bold text-green-700">{completedTasks}/{totalTasks}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-gray-600">Total Cost</span>
            </div>
            <div className="text-xl font-bold text-purple-700">${totalCost.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="space-y-4">
          {phases.map((phase, phaseIndex) => {
            const isExpanded = selectedPhase === phase.id;
            
            return (
              <Card 
                key={phase.id}
                className={`overflow-hidden transition-all ${
                  phase.status === 'in-progress' ? 'ring-2 ring-purple-500' : ''
                }`}
              >
                <button
                  onClick={() => setSelectedPhase(isExpanded ? null : phase.id)}
                  className="w-full text-left"
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      {/* Status Icon */}
                      <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                        phase.status === 'completed' ? 'bg-green-500' :
                        phase.status === 'in-progress' ? 'bg-purple-500' :
                        'bg-gray-300'
                      }`}>
                        {phase.status === 'completed' ? (
                          <CheckCircle2 className="w-6 h-6 text-white" />
                        ) : phase.status === 'in-progress' ? (
                          <PlayCircle className="w-6 h-6 text-white" />
                        ) : (
                          <Circle className="w-6 h-6 text-white" />
                        )}
                      </div>

                      {/* Phase Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-gray-800">{phase.title}</h4>
                          {phase.status === 'in-progress' && (
                            <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">
                              In Progress
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {phase.duration}
                          </span>
                          <span>{phase.tasks.length} tasks</span>
                        </div>
                      </div>

                      {/* Phase Number */}
                      <div className="text-2xl font-bold text-gray-300">
                        {phaseIndex + 1}
                      </div>
                    </div>

                    {/* Tasks (Expanded) */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-gray-200 space-y-2">
                        {phase.tasks.map(task => (
                          <div 
                            key={task.id}
                            className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                          >
                            <CheckCircle2 className={`w-5 h-5 flex-shrink-0 ${
                              phase.status === 'completed' ? 'text-green-500' : 'text-gray-300'
                            }`} />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-800">{task.name}</div>
                              <div className="flex items-center gap-3 text-xs text-gray-600 mt-0.5">
                                <span>{task.duration}</span>
                                <span className={`px-2 py-0.5 rounded-full ${
                                  task.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                                  task.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-red-100 text-red-700'
                                }`}>
                                  {task.difficulty}
                                </span>
                                {!task.diy && (
                                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                                    Pro recommended
                                  </span>
                                )}
                              </div>
                            </div>
                            {task.estimatedCost > 0 && (
                              <div className="text-sm font-bold text-gray-700">
                                ${task.estimatedCost}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </button>
              </Card>
            );
          })}
        </div>
      )}

      {/* Checklist View */}
      {viewMode === 'checklist' && (
        <Card>
          <CardContent className="p-4">
            <div className="space-y-3">
              {phases.flatMap(phase => 
                phase.tasks.map(task => (
                  <label 
                    key={task.id}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                  >
                    <input 
                      type="checkbox" 
                      className="w-5 h-5 text-purple-600 rounded"
                      defaultChecked={phase.status === 'completed'}
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-800">{task.name}</div>
                      <div className="text-xs text-gray-600">{phase.title} • {task.duration}</div>
                    </div>
                    {task.estimatedCost > 0 && (
                      <div className="text-sm font-bold text-gray-700">
                        ${task.estimatedCost}
                      </div>
                    )}
                  </label>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Timeline
        </Button>
        <Button className="bg-gradient-to-r from-purple-500 to-pink-500">
          Start Project
        </Button>
      </div>
    </div>
  );
}

