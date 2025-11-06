'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Sparkles } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { chatAPI } from '@/lib/api/chat';
import type { Message, ChatRequest } from '@/lib/types/chat';

interface ChatInterfaceProps {
  conversationId?: string;
  homeId?: string;
}

export function ChatInterface({ conversationId, homeId }: ChatInterfaceProps) {
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState(conversationId);

  // Fetch messages
  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['messages', currentConversationId],
    queryFn: () => currentConversationId ? chatAPI.getMessages(currentConversationId) : Promise.resolve([]),
    enabled: !!currentConversationId,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (request: ChatRequest) => {
      setIsStreaming(true);
      setStreamingMessage('');

      return new Promise<Message>((resolve, reject) => {
        chatAPI.streamMessage(
          request,
          // onChunk
          (chunk) => {
            setStreamingMessage((prev) => prev + chunk);
          },
          // onComplete
          (message) => {
            setIsStreaming(false);
            setStreamingMessage('');
            resolve(message);
          },
          // onError
          (error) => {
            setIsStreaming(false);
            setStreamingMessage('');
            reject(error);
          }
        );
      });
    },
    onSuccess: (message) => {
      // Update conversation ID if it's a new conversation
      if (!currentConversationId && message.conversation_id) {
        setCurrentConversationId(message.conversation_id);
      }

      // Invalidate messages query to refetch
      queryClient.invalidateQueries({ queryKey: ['messages', message.conversation_id] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const handleSendMessage = (content: string) => {
    const request: ChatRequest = {
      message: content,
      conversation_id: currentConversationId,
      home_id: homeId,
    };

    sendMessageMutation.mutate(request);
  };

  // Suggested prompts for empty state
  const suggestedPrompts = [
    "What's the estimated cost to renovate my kitchen?",
    "Show me modern design ideas for my living room",
    "Find products that fit my bathroom dimensions",
    "Create a DIY project plan for painting my bedroom",
  ];

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : messages.length === 0 && !streamingMessage ? (
            /* Empty State */
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                AI Assistant Ready
              </h3>
              <p className="text-gray-600 mb-8">
                Ask me anything about your home, designs, costs, or projects
              </p>

              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {suggestedPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-4 bg-white border-2 border-gray-200 rounded-xl text-left hover:border-primary hover:shadow-md transition-all"
                    disabled={isStreaming}
                  >
                    <p className="text-sm text-gray-700">{prompt}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages List */
            <div className="space-y-6">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}

              {/* Streaming Message */}
              {streamingMessage && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex flex-col gap-2 max-w-[70%]">
                    <div className="px-4 py-3 rounded-2xl bg-white border border-gray-200 rounded-tl-sm">
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {streamingMessage}
                        <span className="inline-block w-1 h-4 bg-primary ml-1 animate-pulse"></span>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Loading Indicator */}
              {isStreaming && !streamingMessage && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl bg-white border border-gray-200">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <MessageInput
        onSend={handleSendMessage}
        disabled={isStreaming}
        placeholder={homeId ? "Ask about this home..." : "Ask me anything..."}
      />
    </div>
  );
}

