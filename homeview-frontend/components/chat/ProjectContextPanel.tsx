'use client';

import { useState } from 'react';
import { 
  BarChart3,
  CheckSquare,
  Image as ImageIcon,
  DollarSign,
  Calendar,
  TrendingUp,
  FileText,
  Users,
  Wrench,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Task {
  id: string;
  title: string;
  completed: boolean;
}

interface ProjectImage {
  id: string;
  url: string;
  type: 'generated' | 'uploaded' | 'before' | 'after';
  timestamp: string;
}

export function ProjectContextPanel() {
  const [expandedSections, setExpandedSections] = useState<string[]>([
    'overview',
    'tasks',
    'images'
  ]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  // Mock data
  const projectData = {
    name: 'Kitchen Remodel',
    status: 'In Progress',
    budget: 15000,
    spent: 8500,
    timeline: '3 weeks',
    startDate: '2025-01-01',
    tasks: [
      { id: '1', title: 'Choose cabinet style', completed: true },
      { id: '2', title: 'Select countertop material', completed: true },
      { id: '3', title: 'Pick backsplash tile', completed: false },
      { id: '4', title: 'Choose lighting fixtures', completed: false },
      { id: '5', title: 'Get contractor quotes', completed: false },
    ],
    images: [
      { id: '1', url: '/placeholder1.jpg', type: 'generated' as const, timestamp: '2h ago' },
      { id: '2', url: '/placeholder2.jpg', type: 'generated' as const, timestamp: '3h ago' },
      { id: '3', url: '/placeholder3.jpg', type: 'before' as const, timestamp: '1d ago' },
      { id: '4', url: '/placeholder4.jpg', type: 'after' as const, timestamp: '1d ago' },
    ],
  };

  const completedTasks = projectData.tasks.filter(t => t.completed).length;
  const budgetPercentage = (projectData.spent / projectData.budget) * 100;

  return (
    <div className="w-72 bg-white border-l border-gray-200 flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="p-3 border-b border-gray-200 bg-gradient-to-br from-primary/5 to-secondary/5">
        <h2 className="text-base font-semibold text-gray-900 mb-1">
          {projectData.name}
        </h2>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-medium rounded-full">
            <TrendingUp className="w-2.5 h-2.5" />
            {projectData.status}
          </span>
        </div>
      </div>

      {/* Overview Section */}
      <Section
        title="Overview"
        icon={BarChart3}
        isExpanded={expandedSections.includes('overview')}
        onToggle={() => toggleSection('overview')}
      >
        <div className="space-y-3">
          {/* Budget */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-600">Budget</span>
              <span className="text-xs font-semibold text-gray-900">
                ${projectData.spent.toLocaleString()} / ${projectData.budget.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={cn(
                  "h-2 rounded-full transition-all",
                  budgetPercentage > 90 ? "bg-red-500" : 
                  budgetPercentage > 70 ? "bg-yellow-500" : "bg-green-500"
                )}
                style={{ width: `${budgetPercentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {budgetPercentage.toFixed(0)}% used
            </p>
          </div>

          {/* Timeline */}
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-medium text-gray-600">Timeline</span>
            </div>
            <span className="text-xs font-semibold text-gray-900">
              {projectData.timeline}
            </span>
          </div>

          {/* Start Date */}
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-medium text-gray-600">Started</span>
            </div>
            <span className="text-xs font-semibold text-gray-900">
              {projectData.startDate}
            </span>
          </div>
        </div>
      </Section>

      {/* Tasks Section */}
      <Section
        title="Tasks"
        icon={CheckSquare}
        badge={`${completedTasks}/${projectData.tasks.length}`}
        isExpanded={expandedSections.includes('tasks')}
        onToggle={() => toggleSection('tasks')}
      >
        <div className="space-y-2">
          {projectData.tasks.map((task) => (
            <label
              key={task.id}
              className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer group"
            >
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => {}}
                className="mt-0.5 w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
              />
              <span className={cn(
                "text-sm flex-1",
                task.completed 
                  ? "text-gray-400 line-through" 
                  : "text-gray-700"
              )}>
                {task.title}
              </span>
            </label>
          ))}
          <button className="w-full mt-2 text-xs text-primary hover:underline text-left">
            + Add task
          </button>
        </div>
      </Section>

      {/* Images Section */}
      <Section
        title="Images"
        icon={ImageIcon}
        badge={projectData.images.length.toString()}
        isExpanded={expandedSections.includes('images')}
        onToggle={() => toggleSection('images')}
      >
        <div className="grid grid-cols-2 gap-2">
          {projectData.images.map((image) => (
            <div
              key={image.id}
              className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 group cursor-pointer"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="absolute bottom-0 left-0 right-0 p-2 text-white opacity-0 group-hover:opacity-100 transition-opacity">
                <p className="text-xs font-medium capitalize">{image.type}</p>
                <p className="text-xs text-gray-300">{image.timestamp}</p>
              </div>
              {/* Placeholder for actual image */}
              <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                <ImageIcon className="w-8 h-8 text-gray-400" />
              </div>
            </div>
          ))}
        </div>
        <button className="w-full mt-3 flex items-center justify-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg text-xs font-medium text-gray-700 transition-colors">
          <ExternalLink className="w-3 h-3" />
          View All Images
        </button>
      </Section>

      {/* Quick Actions */}
      <Section
        title="Quick Actions"
        icon={Wrench}
        isExpanded={expandedSections.includes('actions')}
        onToggle={() => toggleSection('actions')}
      >
        <div className="space-y-2">
          <ActionButton icon={FileText} label="Generate DIY Plan" />
          <ActionButton icon={DollarSign} label="Get Cost Estimate" />
          <ActionButton icon={Users} label="Find Contractors" />
          <ActionButton icon={ImageIcon} label="Create Before/After" />
        </div>
      </Section>
    </div>
  );
}

// Helper Components
interface SectionProps {
  title: string;
  icon: React.ElementType;
  badge?: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function Section({ title, icon: Icon, badge, isExpanded, onToggle, children }: SectionProps) {
  return (
    <div className="border-b border-gray-200">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-semibold text-gray-900">{title}</span>
          {badge && (
            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs font-medium rounded-full">
              {badge}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>
      {isExpanded && (
        <div className="px-4 pb-4">
          {children}
        </div>
      )}
    </div>
  );
}

interface ActionButtonProps {
  icon: React.ElementType;
  label: string;
}

function ActionButton({ icon: Icon, label }: ActionButtonProps) {
  return (
    <button className="w-full flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all group">
      <div className="p-2 bg-gray-100 rounded-lg group-hover:bg-primary/10 transition-colors">
        <Icon className="w-4 h-4 text-gray-600 group-hover:text-primary" />
      </div>
      <span className="text-sm font-medium text-gray-700 group-hover:text-primary">
        {label}
      </span>
    </button>
  );
}

