'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, MessageSquare, Trash2, Edit2 } from 'lucide-react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Button } from '@/components/ui/button';
import { chatAPI } from '@/lib/api/chat';
import { formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();
  const [showSidebar, setShowSidebar] = useState(true);

  // Fetch conversations
  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: chatAPI.getConversations,
  });

  const handleNewChat = () => {
    setSelectedConversationId(undefined);
  };

  return (
    <div className="fixed inset-0 top-16 left-64 flex bg-gray-50">
      {/* Conversations Sidebar */}
      {showSidebar && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <Button onClick={handleNewChat} className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {isLoading ? (
              <div className="text-center py-8 text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-1">Start a new chat to begin</p>
              </div>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => setSelectedConversationId(conversation.id)}
                  className={cn(
                    'w-full p-3 rounded-lg text-left transition-colors group cursor-pointer',
                    selectedConversationId === conversation.id
                      ? 'bg-primary text-white'
                      : 'hover:bg-gray-100'
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        'font-medium text-sm truncate',
                        selectedConversationId === conversation.id
                          ? 'text-white'
                          : 'text-gray-900'
                      )}>
                        {conversation.title || 'New Conversation'}
                      </p>
                      <p className={cn(
                        'text-xs mt-1',
                        selectedConversationId === conversation.id
                          ? 'text-blue-100'
                          : 'text-gray-500'
                      )}>
                        {formatDate(conversation.updated_at)}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {conversation.persona && (
                          <span
                            className={cn(
                              'px-1.5 py-0.5 rounded text-[10px] border',
                              selectedConversationId === conversation.id
                                ? 'border-blue-200 text-blue-100'
                                : 'border-gray-200 text-gray-600'
                            )}
                          >
                            {conversation.persona === 'homeowner'
                              ? 'Homeowner'
                              : conversation.persona === 'diy_worker'
                              ? 'DIY Worker'
                              : 'Contractor'}
                          </span>
                        )}
                        {conversation.scenario && (
                          <span
                            className={cn(
                              'px-1.5 py-0.5 rounded text-[10px] border',
                              selectedConversationId === conversation.id
                                ? 'border-blue-200 text-blue-100'
                                : 'border-gray-200 text-gray-600'
                            )}
                          >
                            {conversation.scenario === 'contractor_quotes'
                              ? 'Contractor Quotes'
                              : 'DIY Project Plan'}
                          </span>
                        )}
                      </div>

                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        className={cn(
                          'p-1 rounded hover:bg-gray-200',
                          selectedConversationId === conversation.id && 'hover:bg-blue-600'
                        )}
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Implement edit
                        }}
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        className={cn(
                          'p-1 rounded hover:bg-red-100 text-red-600',
                          selectedConversationId === conversation.id && 'hover:bg-red-600 hover:text-white'
                        )}
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Implement delete
                        }}
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <ChatInterface conversationId={selectedConversationId} />
      </div>
    </div>
  );
}

