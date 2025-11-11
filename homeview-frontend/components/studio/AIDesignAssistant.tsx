'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, MessageCircle, Lightbulb, TrendingUp, AlertCircle } from 'lucide-react';

interface Suggestion {
  id: string;
  type: 'tip' | 'warning' | 'idea' | 'trend';
  title: string;
  description: string;
  action?: string;
}

interface AIDesignAssistantProps {
  context?: {
    roomType?: string;
    currentStyle?: string;
    budget?: number;
    spatialData?: any;
  };
  onSuggestionApply?: (suggestionId: string) => void;
  onAsk?: (query: string) => void;
}

export default function AIDesignAssistant({ context, onSuggestionApply, onAsk }: AIDesignAssistantProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState<'suggestions' | 'chat'>('suggestions');

  const [chatQuery, setChatQuery] = useState('');

  // helper to safely map types to Tailwind class strings (avoid dynamic class generation)
  const COLOR_MAP: Record<string, { bg: string; iconBg: string; text: string; badgeBg: string; badgeText: string }> = {
    tip: { bg: 'bg-blue-50', iconBg: 'bg-blue-100', text: 'text-blue-600', badgeBg: 'bg-blue-100', badgeText: 'text-blue-700' },
    warning: { bg: 'bg-amber-50', iconBg: 'bg-amber-100', text: 'text-amber-600', badgeBg: 'bg-amber-100', badgeText: 'text-amber-700' },
    trend: { bg: 'bg-purple-50', iconBg: 'bg-purple-100', text: 'text-purple-600', badgeBg: 'bg-purple-100', badgeText: 'text-purple-700' },
    idea: { bg: 'bg-pink-50', iconBg: 'bg-pink-100', text: 'text-pink-600', badgeBg: 'bg-pink-100', badgeText: 'text-pink-700' },
    default: { bg: 'bg-gray-50', iconBg: 'bg-gray-100', text: 'text-gray-600', badgeBg: 'bg-gray-100', badgeText: 'text-gray-700' },
  };

  // Generate contextual suggestions based on the design
  const suggestions: Suggestion[] = [
    {
      id: 'lighting-tip',
      type: 'tip',
      title: 'Enhance Natural Light',
      description: context?.roomType && context.roomType.toLowerCase().includes('kitchen')
        ? 'This kitchen layout gets great daylight — consider under-cabinet lighting and sheer window treatments to keep it bright during evenings.'
        : 'Your room has good natural light potential. Consider adding sheer curtains to maximize brightness while maintaining privacy.',
      action: 'Add to design',
    },
    {
      id: 'budget-warning',
      type: 'warning',
      title: 'Budget Alert',
      description: 'Your current selections exceed budget by 15%. Consider these cost-saving alternatives without compromising style.',
      action: 'View alternatives',
    },
    {
      id: 'trend-idea',
      type: 'trend',
      title: '2024 Trend: Warm Minimalism',
      description: 'Warm minimalism is trending. Add natural wood tones and soft textiles to create a cozy yet clean aesthetic.',
      action: 'Apply trend',
    },
    {
      id: 'space-optimization',
      type: 'idea',
      title: 'Maximize Space',
      description: 'Based on your room dimensions, a corner reading nook would fit perfectly and add functionality.',
      action: 'Show placement',
    },
    {
      id: 'color-harmony',
      type: 'tip',
      title: 'Color Harmony Tip',
      description: 'Your selected wall color pairs beautifully with sage green accents. Consider adding plants or green throw pillows.',
      action: 'See examples',
    },
  ];

  const getIcon = (type: string) => {
    switch (type) {
      case 'tip': return <Lightbulb className="w-5 h-5" />;
      case 'warning': return <AlertCircle className="w-5 h-5" />;
      case 'trend': return <TrendingUp className="w-5 h-5" />;
      case 'idea': return <Sparkles className="w-5 h-5" />;
      default: return <MessageCircle className="w-5 h-5" />;
    }
  };

  const getColor = (type: string) => COLOR_MAP[type] || COLOR_MAP.default;

  return (
    <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-800">AI Design Assistant</h3>
              <p className="text-xs text-gray-600">Smart suggestions for your project</p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Minimize' : 'Expand'}
          </Button>
        </div>

        {isExpanded && (
          <>
            {/* Tabs */}
            <div className="flex gap-2 mb-4">
              <button
                  onClick={() => setActiveTab('suggestions')}
                  type="button"
                  aria-label="Show suggestions"
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'suggestions'
                    ? 'bg-white text-purple-700 shadow-sm'
                    : 'text-gray-600 hover:bg-white/50'
                }`}
              >
                <Lightbulb className="w-4 h-4 inline mr-1" />
                Suggestions ({suggestions.length})
              </button>
              <button
                  onClick={() => setActiveTab('chat')}
                  type="button"
                  aria-label="Ask AI chat"
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'chat'
                    ? 'bg-white text-purple-700 shadow-sm'
                    : 'text-gray-600 hover:bg-white/50'
                }`}
              >
                <MessageCircle className="w-4 h-4 inline mr-1" />
                Ask AI
              </button>
            </div>

            {/* Suggestions Tab */}
            {activeTab === 'suggestions' && (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {suggestions.map(suggestion => {
                  const color = getColor(suggestion.type);

                  return (
                    <div
                      key={suggestion.id}
                      className="bg-white rounded-lg p-3 border border-gray-200 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start gap-3">
                        <div className={`${color.iconBg} flex-shrink-0 w-8 h-8 rounded-full ${color.text} flex items-center justify-center`} aria-hidden>
                          {getIcon(suggestion.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm font-semibold text-gray-800">{suggestion.title}</h4>
                            <span className={`text-[10px] px-2 py-0.5 ${color.badgeBg} ${color.badgeText} rounded-full font-medium capitalize`}>
                              {suggestion.type}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-2">{suggestion.description}</p>
                          {suggestion.action && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-xs h-7"
                              type="button"
                              onClick={() => onSuggestionApply?.(suggestion.id)}
                              aria-label={`Apply suggestion ${suggestion.title}`}
                            >
                              {suggestion.action}
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Chat Tab */}
            {activeTab === 'chat' && (
              <div className="space-y-3">
                {/* Quick Questions */}
                <div>
                  <div className="text-xs font-semibold text-gray-700 mb-2">Quick Questions</div>
                  <div className="space-y-2">
                    {[
                      'What colors work best with my current palette?',
                      'How can I make this room feel larger?',
                      'What furniture size should I choose?',
                      'How do I improve lighting in this space?',
                    ].map((question, idx) => (
                      <button
                        key={idx}
                        className="w-full text-left px-3 py-2 bg-white rounded-lg text-xs text-gray-700 hover:bg-purple-50 hover:text-purple-700 transition-colors border border-gray-200"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chat Input */}
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <textarea
                    placeholder="Ask me anything about your design..."
                    className="w-full text-sm text-gray-700 placeholder-gray-400 resize-none focus:outline-none"
                    rows={3}
                    value={chatQuery}
                    onChange={(e) => setChatQuery(e.target.value)}
                    aria-label="Chat query"
                    onKeyDown={(e) => {
                      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                        e.preventDefault();
                        if (chatQuery.trim()) {
                          onAsk?.(chatQuery.trim());
                        }
                      }
                    }}
                  />
                  <div className="flex justify-end mt-2">
                    <Button
                      size="sm"
                      className="bg-gradient-to-r from-purple-500 to-pink-500"
                      type="button"
                      onClick={() => {
                        if (chatQuery.trim()) {
                          onAsk?.(chatQuery.trim());
                        }
                      }}
                      aria-label="Send chat query"
                      disabled={!chatQuery.trim()}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Ask AI
                    </Button>
                  </div>
                </div>

                {/* Context Info */}
                <div className="bg-white/50 rounded-lg p-3 border border-purple-200">
                  <div className="text-[10px] font-semibold text-purple-700 mb-2">AI Context</div>
                  <div className="space-y-1 text-[10px] text-gray-600">
                    <div>• Room Type: {context?.roomType || 'Living Room'}</div>
                    <div>• Current Style: {context?.currentStyle || 'Modern'}</div>
                    <div>• Budget: ${context?.budget?.toLocaleString() || '2,500'}</div>
                    <div>• Dimensions: Available ✓</div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Collapsed State */}
        {!isExpanded && (
          <div className="text-center">
            <Button 
              size="sm"
              className="bg-gradient-to-r from-purple-500 to-pink-500"
              onClick={() => setIsExpanded(true)}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              View {suggestions.length} AI Suggestions
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

