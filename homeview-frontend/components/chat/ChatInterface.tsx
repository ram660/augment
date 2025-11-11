'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Sparkles } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ChatModeToggle, type ChatMode } from './ChatModeToggle';
import { chatAPI } from '@/lib/api/chat';
import type { Message, ChatRequest } from '@/lib/types/chat';

interface ChatInterfaceProps {
  conversationId?: string;
  homeId?: string;
  persona?: 'homeowner' | 'diy_worker' | 'contractor';
}

export function ChatInterface({ conversationId, homeId, persona = 'homeowner' }: ChatInterfaceProps) {
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState(conversationId);
  const [chatMode, setChatMode] = useState<ChatMode>('agent'); // Default to agent mode

  // Fetch messages
  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['messages', currentConversationId],
    queryFn: () => currentConversationId ? chatAPI.getMessages(currentConversationId) : Promise.resolve([]),
    enabled: !!currentConversationId,
  });

  // Send message mutation (supports multipart for file uploads)
  const sendMessageMutation = useMutation({
    mutationFn: async (request: ChatRequest & { files?: File[] }) => {
      setIsStreaming(true);
      setStreamingMessage('');

      return new Promise<Message>((resolve, reject) => {
        chatAPI.streamMessageMultipart(
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

  const send = (content: string, scenario?: 'contractor_quotes' | 'diy_project_plan') => {
    const request: ChatRequest = {
      message: content,
      conversation_id: currentConversationId,
      persona,
      scenario,
      mode: chatMode, // Pass current chat mode
    };

    sendMessageMutation.mutate(request);
  };

  const handleSendMessage = (content: string, files?: File[]) => {
    const request: ChatRequest & { files?: File[] } = {
      message: content,
      conversation_id: currentConversationId,
      persona,
      mode: chatMode, // Pass current chat mode
      files,
    };

    sendMessageMutation.mutate(request);
  };

  // Derive persisted persona/scenario from latest message metadata
  const lastMeta = [...messages]
    .slice()
    .reverse()
    .find((m) => {
      const md: any = m.metadata || {};
      return md.persona || md.scenario;
    })?.metadata as any | undefined;

  const persistedPersona = lastMeta?.persona as 'homeowner' | 'diy_worker' | 'contractor' | undefined;
  const persistedScenario = lastMeta?.scenario as 'contractor_quotes' | 'diy_project_plan' | undefined;
  const headerPersona = persistedPersona ?? persona;
  const scenarioLabel =
    persistedScenario === 'contractor_quotes'
      ? 'Get Contractor Quotes'
      : persistedScenario === 'diy_project_plan'
      ? 'DIY Project Plan'
      : undefined;

  // Suggested prompts for empty state
  const suggestedPrompts =
    headerPersona === 'homeowner'
      ? [
          "What's the estimated cost to renovate my kitchen?",
          'Help me compare countertop materials for durability and cost',
          'What can I do to improve energy efficiency in my home?',
          'Suggest a modern design concept for my living room',
        ]

      : headerPersona === 'diy_worker'
      ? [
          'Create a step-by-step plan to paint my bedroom (walls + trim)',
          'What tools and materials do I need to install laminate flooring?',
          'How do I prepare a wall for tiling in a bathroom?',
          'Give me safety tips for using a circular saw as a beginner',
        ]
      : [
          'Draft a scope of work for a small bathroom remodel',
          'Provide a high-level material takeoff for a 12x15 kitchen demo + install',
          'Outline a client-ready proposal structure with key assumptions',
          'What site constraints should I verify before quoting an egress window?',
        ];

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {/* Conversation Header: persona + scenario + mode toggle */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 rounded-full bg-white border border-gray-200 text-xs text-gray-700">
                Persona: {headerPersona === 'homeowner' ? 'Homeowner' : headerPersona === 'diy_worker' ? 'DIY Worker' : 'Contractor'}
              </span>
              {scenarioLabel && (
                <span className="px-2 py-1 rounded-full bg-white border border-gray-200 text-xs text-gray-700">
                  Scenario: {scenarioLabel}
                </span>
              )}
            </div>

            {/* Chat/Agent Mode Toggle */}
            <ChatModeToggle mode={chatMode} onModeChange={setChatMode} />
          </div>

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

              {/* Scenario Templates */}
              <div className="flex flex-wrap gap-3 justify-center mb-6">
                <button
                  onClick={() => send('Help me prepare to get contractor quotes for my project.', 'contractor_quotes')}
                  className="px-4 py-2 rounded-full border-2 border-primary text-primary hover:bg-primary hover:text-white transition-colors"
                  disabled={isStreaming}
                >
                  Get Contractor Quotes
                </button>
                <button
                  onClick={() => send('Create a DIY project plan tailored to my home.', 'diy_project_plan')}
                  className="px-4 py-2 rounded-full border-2 border-secondary text-secondary hover:bg-secondary hover:text-white transition-colors"
                  disabled={isStreaming}
                >
                  Create My DIY Project Plan
                </button>
              </div>

              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {suggestedPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => send(prompt)}
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
                <MessageBubble
                  key={message.id}
                  message={message}
                  onQuestionClick={(question) => send(question)}
                />
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
        placeholder="Ask me anything..."
      />

    </div>
  );
}

