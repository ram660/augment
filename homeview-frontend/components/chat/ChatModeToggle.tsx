'use client';

import { MessageSquare, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ChatMode = 'chat' | 'agent';

interface ChatModeToggleProps {
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  className?: string;
}

export function ChatModeToggle({ mode, onModeChange, className }: ChatModeToggleProps) {
  return (
    <div className={cn('inline-flex items-center gap-1 p-1 bg-gray-100 rounded-lg', className)}>
      <button
        onClick={() => onModeChange('chat')}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
          mode === 'chat'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        )}
      >
        <MessageSquare className="w-4 h-4" />
        Chat
      </button>
      <button
        onClick={() => onModeChange('agent')}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
          mode === 'agent'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        )}
      >
        <Sparkles className="w-4 h-4" />
        Agent
      </button>
    </div>
  );
}

/**
 * Mode Descriptions:
 * 
 * CHAT MODE:
 * - Simple conversational responses
 * - No automatic tool execution
 * - No web search, image generation, or YouTube recommendations
 * - Faster, more direct answers
 * - User controls all actions
 * 
 * AGENT MODE:
 * - Agentic workflow with automatic tool execution
 * - Web search integration (Google Grounding)
 * - Image generation (Gemini Imagen)
 * - Visual aids and diagrams
 * - YouTube video recommendations
 * - Multi-step task execution
 * - Proactive suggestions and actions
 */

