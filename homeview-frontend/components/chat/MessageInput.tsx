'use client';

import { useState, useRef, KeyboardEvent, useEffect } from 'react';
import { Send, Paperclip, Mic, Image as ImageIcon, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface MessageInputProps {
  onSend: (message: string, files?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({ onSend, disabled, placeholder = 'Ask me anything about your home...' }: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Generate image previews when files change
  useEffect(() => {
    const imageFiles = files.filter(f => f.type.startsWith('image/'));
    const previews: string[] = [];

    imageFiles.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        previews.push(reader.result as string);
        if (previews.length === imageFiles.length) {
          setImagePreviews(previews);
        }
      };
      reader.readAsDataURL(file);
    });

    // Cleanup
    return () => {
      imagePreviews.forEach(url => URL.revokeObjectURL(url));
    };
  }, [files]);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim(), files.length ? files : undefined);
      setMessage('');
      setFiles([]);
      // Clear input value so selecting the same file again triggers change
      if (fileInputRef.current) fileInputRef.current.value = '';

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    if (selected.length) {
      setFiles((prev) => [...prev, ...selected]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
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
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              className={cn(
                "p-2 rounded-lg transition-colors",
                files.length > 0
                  ? "text-primary bg-primary/10 hover:bg-primary/20"
                  : "text-gray-500 hover:bg-gray-100"
              )}
              title="Upload room photo for AI transformation"
              disabled={disabled}
              onClick={() => fileInputRef.current?.click()}
            >
              <ImageIcon className="w-5 h-5" />
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

        {/* Selected attachments preview */}
        {files.length > 0 && (
          <div className="mt-3 space-y-2">
            <div className="text-xs font-medium text-gray-600">
              📎 Attachments ({files.length})
            </div>
            <div className="flex flex-wrap gap-3">
              {files.map((f, idx) => {
                const isImage = f.type.startsWith('image/');
                return (
                  <div
                    key={idx}
                    className="relative group"
                  >
                    {isImage ? (
                      // Image preview with thumbnail
                      <div className="relative w-24 h-24 rounded-lg overflow-hidden border-2 border-gray-200 bg-gray-100">
                        {imagePreviews[idx] && (
                          <img
                            src={imagePreviews[idx]}
                            alt={f.name}
                            className="w-full h-full object-cover"
                          />
                        )}
                        {/* Remove button overlay */}
                        <button
                          type="button"
                          onClick={() => removeFile(idx)}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                          title="Remove image"
                        >
                          <X className="w-3 h-3" />
                        </button>
                        {/* File name tooltip */}
                        <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] px-1 py-0.5 truncate">
                          {f.name}
                        </div>
                      </div>
                    ) : (
                      // Non-image file preview
                      <div className="flex items-center gap-2 bg-gray-100 border border-gray-200 rounded-md px-3 py-2 pr-8 relative">
                        <span className="text-xs text-gray-700 max-w-[160px] truncate" title={f.name}>
                          {f.type.includes('pdf') ? '📄' : '📎'} {f.name}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeFile(idx)}
                          className="absolute right-1 top-1/2 -translate-y-1/2 p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Remove file"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}


        {/* Helper Text */}
        <p className="text-xs text-gray-500 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

