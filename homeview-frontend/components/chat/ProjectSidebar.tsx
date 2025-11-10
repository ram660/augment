'use client';

import { useState } from 'react';
import { 
  Plus, 
  FolderOpen, 
  Archive, 
  Search,
  MoreVertical,
  Trash2,
  Edit2,
  CheckCircle2,
  Clock,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Project {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'archived';
  lastMessage: string;
  lastMessageTime: string;
  messageCount: number;
  imageCount: number;
  budget?: number;
}

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Kitchen Remodel',
    status: 'active',
    lastMessage: 'Show me modern kitchen designs',
    lastMessageTime: '2 hours ago',
    messageCount: 24,
    imageCount: 12,
    budget: 15000
  },
  {
    id: '2',
    name: 'Bathroom Refresh',
    status: 'active',
    lastMessage: 'What about coastal style?',
    lastMessageTime: '1 day ago',
    messageCount: 18,
    imageCount: 8,
    budget: 8000
  },
  {
    id: '3',
    name: 'Living Room Update',
    status: 'completed',
    lastMessage: 'Perfect! Thanks for the help',
    lastMessageTime: '1 week ago',
    messageCount: 32,
    imageCount: 15,
    budget: 5000
  },
];

export function ProjectSidebar() {
  const [activeProjectId, setActiveProjectId] = useState('1');
  const [searchQuery, setSearchQuery] = useState('');
  const [showArchived, setShowArchived] = useState(false);

  const filteredProjects = mockProjects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesArchived = showArchived ? project.status === 'archived' : project.status !== 'archived';
    return matchesSearch && matchesArchived;
  });

  const getStatusIcon = (status: Project['status']) => {
    switch (status) {
      case 'active':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'archived':
        return <Archive className="w-4 h-4 text-gray-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-base font-semibold text-gray-900">Projects</h2>
          <button
            className="p-1.5 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
            title="New Project"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-7 pr-2 py-1.5 border border-gray-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-gray-200 bg-gray-50">
        <button
          onClick={() => setShowArchived(false)}
          className={cn(
            'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-colors',
            !showArchived
              ? 'bg-white text-primary shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <FolderOpen className="w-3 h-3" />
          Active
        </button>
        <button
          onClick={() => setShowArchived(true)}
          className={cn(
            'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-colors',
            showArchived
              ? 'bg-white text-primary shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <Archive className="w-3 h-3" />
          Archived
        </button>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto">
        {filteredProjects.length === 0 ? (
          <div className="p-8 text-center">
            <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No projects found</p>
            <button className="mt-3 text-sm text-primary hover:underline">
              Create your first project
            </button>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredProjects.map((project) => (
              <div
                key={project.id}
                onClick={() => setActiveProjectId(project.id)}
                className={cn(
                  'w-full p-2 rounded-lg text-left transition-all duration-200 cursor-pointer',
                  'hover:bg-gray-50 group',
                  activeProjectId === project.id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'border border-transparent'
                )}
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    {getStatusIcon(project.status)}
                    <h3 className={cn(
                      'font-medium text-xs truncate',
                      activeProjectId === project.id ? 'text-primary' : 'text-gray-900'
                    )}>
                      {project.name}
                    </h3>
                  </div>
                  <button
                    className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-gray-200 rounded transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle menu
                    }}
                  >
                    <MoreVertical className="w-3 h-3 text-gray-500" />
                  </button>
                </div>

                <p className="text-[10px] text-gray-500 truncate mb-1">
                  {project.lastMessage}
                </p>

                <div className="flex items-center justify-between text-[10px] text-gray-400">
                  <span>{project.lastMessageTime}</span>
                  <div className="flex items-center gap-2">
                    <span>💬 {project.messageCount}</span>
                    <span>🖼️ {project.imageCount}</span>
                  </div>
                </div>

                {project.budget && (
                  <div className="mt-1 pt-1 border-t border-gray-100">
                    <span className="text-[10px] font-medium text-gray-600">
                      Budget: ${project.budget.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-2 border-t border-gray-200 bg-gray-50">
        <button className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors">
          <Archive className="w-3 h-3" />
          View All Projects
        </button>
      </div>
    </div>
  );
}

