'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ProjectSidebar } from '@/components/chat/ProjectSidebar';
import { ProjectContextPanel } from '@/components/chat/ProjectContextPanel';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { chatAPI } from '@/lib/api/chat';
import { LayoutGrid, PanelLeftClose, PanelRightClose } from 'lucide-react';

export default function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();
  const [showSidebar, setShowSidebar] = useState(true);
  const [showContextPanel, setShowContextPanel] = useState(true);

  // Fetch conversations
  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => chatAPI.getConversations(),
  });

  return (
    <div className="flex h-full bg-gray-50">
      {/* Project Sidebar - Left */}
      {showSidebar && <ProjectSidebar />}

      {/* Main Chat Area - Center */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center">
                <LayoutGrid className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Kitchen Remodel</h1>
                <p className="text-sm text-gray-500">
                  Plan your project with AI assistance
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title={showSidebar ? 'Hide projects sidebar' : 'Show projects sidebar'}
              >
                <PanelLeftClose className="w-4 h-4" />
                {showSidebar ? 'Hide' : 'Show'} Projects
              </button>
              <button
                onClick={() => setShowContextPanel(!showContextPanel)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title={showContextPanel ? 'Hide context panel' : 'Show context panel'}
              >
                <PanelRightClose className="w-4 h-4" />
                {showContextPanel ? 'Hide' : 'Show'} Context
              </button>
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface conversationId={selectedConversationId} />
        </div>
      </div>

      {/* Project Context Panel - Right */}
      {showContextPanel && <ProjectContextPanel />}
    </div>
  );
}

