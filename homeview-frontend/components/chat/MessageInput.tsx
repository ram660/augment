'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Paperclip, Mic, Image as ImageIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({ onSend, disabled, placeholder = 'Ask me anything about your home...' }: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-2">
          {/* Attachment Buttons */}
          <div className="flex gap-1 mb-2">
            <button
              className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              title="Attach image"
              disabled={disabled}
            >
              <ImageIcon className="w-5 h-5" />
            </button>
            <button
              className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              title="Attach file"
              disabled={disabled}
            >
              <Paperclip className="w-5 h-5" />
            </button>
          </div>

          {/* Message Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              className={cn(
                'w-full px-4 py-3 pr-12 rounded-xl border-2 border-gray-300',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'resize-none overflow-y-auto',
                'disabled:bg-gray-100 disabled:cursor-not-allowed',
                'placeholder:text-gray-400'
              )}
              style={{ maxHeight: '200px' }}
            />
          </div>

          {/* Send Button */}
          <Button
            onClick={handleSend}
            disabled={!message.trim() || disabled}
            size="icon"
            className="mb-2 h-10 w-10"
          >
            <Send className="w-5 h-5" />
          </Button>

          {/* Voice Input Button */}
          <button
            className="p-2 mb-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
            title="Voice input"
            disabled={disabled}
          >
            <Mic className="w-5 h-5" />
          </button>
        </div>

        {/* Helper Text */}
        <p className="text-xs text-gray-500 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

