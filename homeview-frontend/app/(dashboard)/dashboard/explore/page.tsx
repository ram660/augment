'use client';

import { useState } from 'react';
import { 
  Search, 
  Filter, 
  Heart,
  Compass,
  TrendingUp,
  Grid3x3,
  List
} from 'lucide-react';

const mockDesigns = [
  { id: 1, title: 'Modern Kitchen', style: 'Modern', room: 'Kitchen', budget: 15000, likes: 234, image: '🏠' },
  { id: 2, title: 'Rustic Bathroom', style: 'Rustic', room: 'Bathroom', budget: 8000, likes: 189, image: '🛁' },
  { id: 3, title: 'Coastal Bedroom', style: 'Coastal', room: 'Bedroom', budget: 12000, likes: 456, image: '🛏️' },
  { id: 4, title: 'Industrial Living', style: 'Industrial', room: 'Living Room', budget: 20000, likes: 321, image: '🛋️' },
  { id: 5, title: 'Scandinavian Office', style: 'Scandinavian', room: 'Office', budget: 6000, likes: 278, image: '💼' },
  { id: 6, title: 'Bohemian Patio', style: 'Bohemian', room: 'Outdoor', budget: 10000, likes: 412, image: '🌿' },
];

export default function ExplorePage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center">
                <Compass className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Explore Designs</h1>
                <p className="text-sm text-gray-500">Discover inspiration for your home</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'grid' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Grid3x3 className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'list' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Search & Filters */}
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search designs, styles, rooms..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <button className="flex items-center gap-2 px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium">
              <Filter className="w-5 h-5" />
              Filters
            </button>
          </div>

          {/* Quick Filters */}
          <div className="flex items-center gap-2 mt-4">
            <span className="text-sm font-medium text-gray-600">Popular:</span>
            {['Modern', 'Rustic', 'Coastal', 'Industrial'].map((style) => (
              <button
                key={style}
                className="px-3 py-1.5 bg-gray-100 hover:bg-primary hover:text-white rounded-full text-sm font-medium text-gray-700 transition-colors"
              >
                {style}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* Trending Section */}
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-gray-900">Trending This Week</h2>
            </div>
            <div className={`grid ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'} gap-6`}>
              {mockDesigns.map((design) => (
                <DesignCard key={design.id} design={design} viewMode={viewMode} />
              ))}
            </div>
          </div>

          {/* Load More */}
          <div className="text-center py-8">
            <button className="px-6 py-3 bg-white border-2 border-gray-200 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium">
              Load More Designs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface DesignCardProps {
  design: {
    id: number;
    title: string;
    style: string;
    room: string;
    budget: number;
    likes: number;
    image: string;
  };
  viewMode: 'grid' | 'list';
}

function DesignCard({ design, viewMode }: DesignCardProps) {
  const [isLiked, setIsLiked] = useState(false);

  if (viewMode === 'list') {
    return (
      <div className="bg-white rounded-xl border-2 border-gray-100 hover:border-primary/20 hover:shadow-md transition-all p-4 flex items-center gap-4">
        <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center text-4xl">
          {design.image}
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{design.title}</h3>
          <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
            <span className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">{design.style}</span>
            <span>{design.room}</span>
            <span>•</span>
            <span>${design.budget.toLocaleString()}</span>
          </div>
        </div>
        <button
          onClick={() => setIsLiked(!isLiked)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500 text-red-500' : 'text-gray-400'}`} />
          <span className="text-sm font-medium text-gray-600">{design.likes}</span>
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border-2 border-gray-100 hover:border-primary/20 hover:shadow-md transition-all overflow-hidden group cursor-pointer">
      <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-6xl relative">
        {design.image}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsLiked(!isLiked);
          }}
          className="absolute top-3 right-3 p-2 bg-white/90 backdrop-blur-sm rounded-full hover:bg-white transition-colors"
        >
          <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500 text-red-500' : 'text-gray-600'}`} />
        </button>
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-2">{design.title}</h3>
        <div className="flex items-center gap-2 mb-3">
          <span className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">{design.style}</span>
          <span className="text-xs text-gray-600">{design.room}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-900">${design.budget.toLocaleString()}</span>
          <span className="text-sm text-gray-500">❤️ {design.likes}</span>
        </div>
      </div>
    </div>
  );
}

