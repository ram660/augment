'use client';

import { useState } from 'react';
import { 
  Users, 
  Heart, 
  MessageCircle, 
  Share2,
  TrendingUp,
  Clock,
  Plus
} from 'lucide-react';

const mockPosts = [
  {
    id: 1,
    author: 'John Doe',
    avatar: '👨',
    time: '2 hours ago',
    content: 'Just finished my kitchen remodel! 🎉 Took 3 weeks and stayed under budget.',
    beforeImage: '🏚️',
    afterImage: '✨',
    budget: 15000,
    timeline: '3 weeks',
    diyPercentage: 60,
    likes: 234,
    comments: 45,
  },
  {
    id: 2,
    author: 'Jane Smith',
    avatar: '👩',
    time: '5 hours ago',
    content: 'Need advice on bathroom tile selection. Which one looks better?',
    beforeImage: '🛁',
    afterImage: null,
    budget: 8000,
    timeline: null,
    diyPercentage: null,
    likes: 89,
    comments: 23,
  },
  {
    id: 3,
    author: 'Mike Johnson',
    avatar: '👨‍🦰',
    time: '1 day ago',
    content: 'Transformed my backyard into an outdoor oasis! DIY project that took 2 months.',
    beforeImage: '🌱',
    afterImage: '🌿',
    budget: 12000,
    timeline: '2 months',
    diyPercentage: 90,
    likes: 567,
    comments: 78,
  },
];

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState<'feed' | 'trending' | 'following'>('feed');

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Community</h1>
                <p className="text-sm text-gray-500">Connect with other homeowners</p>
              </div>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium shadow-md">
              <Plus className="w-5 h-5" />
              Share Project
            </button>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('feed')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'feed'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Clock className="w-4 h-4" />
              Latest
            </button>
            <button
              onClick={() => setActiveTab('trending')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'trending'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Trending
            </button>
            <button
              onClick={() => setActiveTab('following')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'following'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Users className="w-4 h-4" />
              Following
            </button>
          </div>
        </div>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
          {mockPosts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}

          {/* Load More */}
          <div className="text-center py-8">
            <button className="px-6 py-3 bg-white border-2 border-gray-200 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium">
              Load More Posts
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface PostCardProps {
  post: {
    id: number;
    author: string;
    avatar: string;
    time: string;
    content: string;
    beforeImage: string | null;
    afterImage: string | null;
    budget: number | null;
    timeline: string | null;
    diyPercentage: number | null;
    likes: number;
    comments: number;
  };
}

function PostCard({ post }: PostCardProps) {
  const [isLiked, setIsLiked] = useState(false);

  return (
    <div className="bg-white rounded-xl border-2 border-gray-100 hover:border-gray-200 transition-all overflow-hidden">
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-xl">
            {post.avatar}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{post.author}</h3>
            <p className="text-xs text-gray-500">{post.time}</p>
          </div>
        </div>
        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Share2 className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {/* Content */}
      <div className="px-4 pb-4">
        <p className="text-gray-700 mb-4">{post.content}</p>

        {/* Before/After Images */}
        {(post.beforeImage || post.afterImage) && (
          <div className="grid grid-cols-2 gap-4 mb-4">
            {post.beforeImage && (
              <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex flex-col items-center justify-center text-6xl">
                {post.beforeImage}
                <span className="text-xs font-medium text-gray-600 mt-2">Before</span>
              </div>
            )}
            {post.afterImage && (
              <div className="aspect-video bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg flex flex-col items-center justify-center text-6xl">
                {post.afterImage}
                <span className="text-xs font-medium text-primary mt-2">After</span>
              </div>
            )}
          </div>
        )}

        {/* Project Stats */}
        {(post.budget || post.timeline || post.diyPercentage) && (
          <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg mb-4">
            {post.budget && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600">Budget:</span>
                <span className="text-xs font-semibold text-gray-900">${post.budget.toLocaleString()}</span>
              </div>
            )}
            {post.timeline && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600">Timeline:</span>
                <span className="text-xs font-semibold text-gray-900">{post.timeline}</span>
              </div>
            )}
            {post.diyPercentage && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600">DIY:</span>
                <span className="text-xs font-semibold text-gray-900">{post.diyPercentage}%</span>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-4 pt-3 border-t border-gray-100">
          <button
            onClick={() => setIsLiked(!isLiked)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500 text-red-500' : 'text-gray-600'}`} />
            <span className="text-sm font-medium text-gray-700">{post.likes}</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors">
            <MessageCircle className="w-5 h-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">{post.comments}</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors ml-auto">
            <Share2 className="w-5 h-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Share</span>
          </button>
        </div>
      </div>
    </div>
  );
}

