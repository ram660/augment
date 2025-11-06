'use client';

import { User, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Message } from '@/lib/types/chat';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
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

