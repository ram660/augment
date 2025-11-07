'use client';

import { User, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Message } from '@/lib/types/chat';

interface MessageBubbleProps {
  message: Message;
  onQuestionClick?: (question: string) => void;
}

export function MessageBubble({ message, onQuestionClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-primary' : 'bg-green-500'
        )}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('flex flex-col gap-2 max-w-[70%]', isUser && 'items-end')}>
        {/* Message Bubble */}
        <div
          className={cn(
            'px-4 py-3 rounded-2xl',
            isUser
              ? 'bg-primary text-white rounded-tr-sm'
              : 'bg-white border border-gray-200 rounded-tl-sm'
          )}
        >
          <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Metadata - Images */}
        {message.metadata?.images && message.metadata.images.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.metadata.images.map((imageUrl, index) => (
              <div key={index} className="w-32 h-32 rounded-lg overflow-hidden border border-gray-200">
                <img
                  src={imageUrl}
                  alt={`Attachment ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        )}

        {/* Metadata - Attachments (PDFs / files) */}
        {message.metadata?.attachments && message.metadata.attachments.length > 0 && (
          <div className="flex flex-col gap-2 w-full">
            {message.metadata.attachments
              .filter((att) => att.type === 'pdf' || (att.content_type && att.content_type.includes('pdf')) || att.type === 'file')
              .map((att, idx) => (
                <a
                  key={idx}
                  href={att.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-blue-600 hover:underline bg-blue-50 border border-blue-200 rounded-md px-3 py-2 w-fit"
                >
                  <span>📄 {att.filename || 'Attachment'}</span>
                </a>
              ))}
          </div>
        )}


        {/* Metadata - Designs */}
        {message.metadata?.designs && message.metadata.designs.length > 0 && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm">
            <p className="font-medium text-purple-900">🎨 Design Suggestions</p>
            <p className="text-purple-700 mt-1">{message.metadata.designs.length} designs available</p>
          </div>
        )}

        {/* Metadata - Products */}
        {message.metadata?.products && message.metadata.products.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
            <p className="font-medium text-blue-900">🛒 Product Recommendations</p>
            <p className="text-blue-700 mt-1">{message.metadata.products.length} products found</p>
          </div>
        )}

        {/* Metadata - Cost Estimates */}
        {message.metadata?.cost_estimates && message.metadata.cost_estimates.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
            <p className="font-medium text-green-900">💰 Cost Estimate</p>
            <p className="text-green-700 mt-1">Estimate available</p>
          </div>
        )}
        {/* Suggested Follow-up Questions */}
        {isAssistant && message.metadata?.suggested_questions && message.metadata.suggested_questions.length > 0 && (
          <div className="flex flex-col gap-2 w-full mt-1">
            <p className="text-xs text-gray-500 px-2">Continue your journey:</p>
            <div className="flex flex-wrap gap-2">
              {message.metadata.suggested_questions.map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => onQuestionClick?.(question)}
                  className="px-3 py-1.5 rounded-full text-xs border border-gray-300 text-gray-700 hover:border-primary hover:text-primary hover:bg-primary/5 transition-colors text-left"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}


        {/* Timestamp */}
        <p className="text-xs text-gray-500 px-2">
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}

