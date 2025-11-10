'use client';

import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Star, Copy, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MessageFeedbackProps {
  messageId: string;
  onFeedbackSubmit?: (feedback: FeedbackData) => void;
}

export interface FeedbackData {
  message_id: string;
  feedback_type: 'thumbs_up' | 'thumbs_down' | 'rating_1' | 'rating_2' | 'rating_3' | 'rating_4' | 'rating_5' | 'copy' | 'regenerate';
  rating?: number;
  comment?: string;
  helpful?: boolean;
  accurate?: boolean;
  complete?: boolean;
}

export function MessageFeedback({ messageId, onFeedbackSubmit }: MessageFeedbackProps) {
  const [feedbackGiven, setFeedbackGiven] = useState<'thumbs_up' | 'thumbs_down' | 'rating' | null>(null);
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [copied, setCopied] = useState(false);

  const handleThumbsUp = () => {
    if (feedbackGiven === 'thumbs_up') return; // Already submitted
    
    setFeedbackGiven('thumbs_up');
    submitFeedback({
      message_id: messageId,
      feedback_type: 'thumbs_up',
      helpful: true,
    });
  };

  const handleThumbsDown = () => {
    if (feedbackGiven === 'thumbs_down') return;
    
    setFeedbackGiven('thumbs_down');
    setShowComment(true); // Ask for feedback on what went wrong
    submitFeedback({
      message_id: messageId,
      feedback_type: 'thumbs_down',
      helpful: false,
    });
  };

  const handleRatingClick = () => {
    if (feedbackGiven === 'rating') return;
    setShowRating(!showRating);
  };

  const handleStarClick = (starValue: number) => {
    setRating(starValue);
    setFeedbackGiven('rating');
    setShowRating(false);
    
    const feedbackType = `rating_${starValue}` as FeedbackData['feedback_type'];
    submitFeedback({
      message_id: messageId,
      feedback_type: feedbackType,
      rating: starValue,
      helpful: starValue >= 4,
      accurate: starValue >= 3,
      complete: starValue >= 3,
    });
  };

  const handleCopy = async () => {
    // This would copy the message content - parent component should handle this
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    
    submitFeedback({
      message_id: messageId,
      feedback_type: 'copy',
      helpful: true,
    });
  };

  const submitFeedback = (feedback: FeedbackData) => {
    // Add comment if provided
    if (comment.trim()) {
      feedback.comment = comment.trim();
    }
    
    onFeedbackSubmit?.(feedback);
  };

  const handleCommentSubmit = () => {
    if (!comment.trim()) return;
    
    // Update the existing feedback with comment
    const feedbackType = feedbackGiven === 'thumbs_up' ? 'thumbs_up' : 
                        feedbackGiven === 'thumbs_down' ? 'thumbs_down' :
                        `rating_${rating}` as FeedbackData['feedback_type'];
    
    submitFeedback({
      message_id: messageId,
      feedback_type: feedbackType,
      rating: rating || undefined,
      comment: comment.trim(),
    });
    
    setShowComment(false);
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Main Feedback Buttons */}
      <div className="flex items-center gap-2">
        {/* Thumbs Up */}
        <button
          onClick={handleThumbsUp}
          disabled={feedbackGiven !== null && feedbackGiven !== 'thumbs_up'}
          className={cn(
            'p-1.5 rounded-md transition-all',
            feedbackGiven === 'thumbs_up'
              ? 'bg-green-100 text-green-700'
              : 'text-gray-400 hover:text-green-600 hover:bg-green-50',
            feedbackGiven !== null && feedbackGiven !== 'thumbs_up' && 'opacity-50 cursor-not-allowed'
          )}
          title="Helpful"
        >
          <ThumbsUp className="w-4 h-4" />
        </button>

        {/* Thumbs Down */}
        <button
          onClick={handleThumbsDown}
          disabled={feedbackGiven !== null && feedbackGiven !== 'thumbs_down'}
          className={cn(
            'p-1.5 rounded-md transition-all',
            feedbackGiven === 'thumbs_down'
              ? 'bg-red-100 text-red-700'
              : 'text-gray-400 hover:text-red-600 hover:bg-red-50',
            feedbackGiven !== null && feedbackGiven !== 'thumbs_down' && 'opacity-50 cursor-not-allowed'
          )}
          title="Not helpful"
        >
          <ThumbsDown className="w-4 h-4" />
        </button>

        {/* Star Rating Toggle */}
        <button
          onClick={handleRatingClick}
          disabled={feedbackGiven !== null && feedbackGiven !== 'rating'}
          className={cn(
            'p-1.5 rounded-md transition-all',
            feedbackGiven === 'rating'
              ? 'bg-yellow-100 text-yellow-700'
              : 'text-gray-400 hover:text-yellow-600 hover:bg-yellow-50',
            feedbackGiven !== null && feedbackGiven !== 'rating' && 'opacity-50 cursor-not-allowed'
          )}
          title="Rate this response"
        >
          <Star className={cn('w-4 h-4', rating > 0 && 'fill-current')} />
        </button>

        {/* Copy Button */}
        <button
          onClick={handleCopy}
          className={cn(
            'p-1.5 rounded-md transition-all',
            copied
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'
          )}
          title={copied ? 'Copied!' : 'Copy response'}
        >
          <Copy className="w-4 h-4" />
        </button>

        {/* Feedback Status */}
        {feedbackGiven && (
          <span className="text-xs text-gray-500 ml-2">
            {feedbackGiven === 'thumbs_up' && 'Thanks for your feedback!'}
            {feedbackGiven === 'thumbs_down' && 'Thanks for letting us know'}
            {feedbackGiven === 'rating' && `Rated ${rating} star${rating !== 1 ? 's' : ''}`}
          </span>
        )}
      </div>

      {/* Star Rating Dropdown */}
      {showRating && (
        <div className="flex items-center gap-1 p-2 bg-white border border-gray-200 rounded-md shadow-sm">
          <span className="text-xs text-gray-600 mr-2">Rate:</span>
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => handleStarClick(star)}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              className="p-1 hover:scale-110 transition-transform"
            >
              <Star
                className={cn(
                  'w-5 h-5',
                  (hoverRating >= star || rating >= star)
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-300'
                )}
              />
            </button>
          ))}
        </div>
      )}

      {/* Comment Input */}
      {showComment && (
        <div className="flex flex-col gap-2 p-2 bg-white border border-gray-200 rounded-md">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="What could be improved? (optional)"
            className="text-xs p-2 border border-gray-200 rounded resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
            rows={2}
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowComment(false)}
              className="text-xs px-3 py-1 text-gray-600 hover:text-gray-800"
            >
              Skip
            </button>
            <button
              onClick={handleCommentSubmit}
              disabled={!comment.trim()}
              className="text-xs px-3 py-1 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Submit
            </button>
          </div>
        </div>
      )}

      {/* Add Comment Link (if feedback given but no comment yet) */}
      {feedbackGiven && !showComment && !comment && (
        <button
          onClick={() => setShowComment(true)}
          className="text-xs text-gray-500 hover:text-gray-700 text-left"
        >
          Add a comment...
        </button>
      )}
    </div>
  );
}

