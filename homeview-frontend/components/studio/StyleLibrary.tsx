'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, Heart, TrendingUp } from 'lucide-react';

interface StyleTemplate {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  tags: string[];
  popularity: number;
  prompt: string;
}

interface StyleLibraryProps {
  onStyleSelect: (style: StyleTemplate) => void;
}

export default function StyleLibrary({ onStyleSelect }: StyleLibraryProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  const categories = [
    { id: 'all', label: 'All Styles', icon: '🎨' },
    { id: 'modern', label: 'Modern', icon: '✨' },
    { id: 'traditional', label: 'Traditional', icon: '🏛️' },
    { id: 'minimalist', label: 'Minimalist', icon: '⚪' },
    { id: 'bohemian', label: 'Bohemian', icon: '🌺' },
    { id: 'industrial', label: 'Industrial', icon: '🏭' },
    { id: 'scandinavian', label: 'Scandinavian', icon: '❄️' },
  ];

  const styles: StyleTemplate[] = [
    {
      id: 'modern-minimalist',
      name: 'Modern Minimalist',
      description: 'Clean lines, neutral colors, and functional furniture',
      thumbnail: '/api/placeholder/400/300',
      tags: ['modern', 'minimalist', 'clean'],
      popularity: 95,
      prompt: 'Transform this room into a modern minimalist space with clean lines, neutral colors (white, gray, beige), minimal furniture, and plenty of natural light. Add sleek modern furniture and remove clutter.',
    },
    {
      id: 'cozy-scandinavian',
      name: 'Cozy Scandinavian',
      description: 'Warm woods, soft textiles, and hygge vibes',
      thumbnail: '/api/placeholder/400/300',
      tags: ['scandinavian', 'cozy', 'natural'],
      popularity: 88,
      prompt: 'Create a cozy Scandinavian design with light wood floors, white walls, warm textiles, plants, and natural materials. Add soft lighting and comfortable seating.',
    },
    {
      id: 'industrial-loft',
      name: 'Industrial Loft',
      description: 'Exposed brick, metal accents, and urban edge',
      thumbnail: '/api/placeholder/400/300',
      tags: ['industrial', 'urban', 'edgy'],
      popularity: 82,
      prompt: 'Transform into an industrial loft style with exposed brick walls, metal fixtures, concrete floors, Edison bulb lighting, and vintage furniture pieces.',
    },
    {
      id: 'bohemian-eclectic',
      name: 'Bohemian Eclectic',
      description: 'Colorful patterns, plants, and global influences',
      thumbnail: '/api/placeholder/400/300',
      tags: ['bohemian', 'colorful', 'eclectic'],
      popularity: 76,
      prompt: 'Create a bohemian eclectic space with colorful textiles, patterned rugs, lots of plants, macramé wall hangings, and mix-and-match furniture with global influences.',
    },
    {
      id: 'coastal-retreat',
      name: 'Coastal Retreat',
      description: 'Light blues, whites, and beachy vibes',
      thumbnail: '/api/placeholder/400/300',
      tags: ['coastal', 'beach', 'relaxed'],
      popularity: 85,
      prompt: 'Design a coastal retreat with light blue and white colors, natural textures like rattan and jute, nautical accents, and airy, relaxed atmosphere.',
    },
    {
      id: 'mid-century-modern',
      name: 'Mid-Century Modern',
      description: 'Retro furniture, bold colors, and iconic pieces',
      thumbnail: '/api/placeholder/400/300',
      tags: ['modern', 'retro', 'vintage'],
      popularity: 90,
      prompt: 'Transform into mid-century modern style with iconic furniture pieces, bold accent colors (mustard, teal, orange), wood paneling, and geometric patterns.',
    },
  ];

  const filteredStyles = selectedCategory === 'all' 
    ? styles 
    : styles.filter(s => s.tags.includes(selectedCategory));

  const toggleFavorite = (styleId: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(styleId)) {
      newFavorites.delete(styleId);
    } else {
      newFavorites.add(styleId);
    }
    setFavorites(newFavorites);
  };

  return (
    <div className="space-y-3">
      {/* Category Filter - Compact */}
      <div className="flex gap-1.5 overflow-x-auto pb-2 scrollbar-thin">
        {categories.slice(0, 5).map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`flex-shrink-0 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${
              selectedCategory === cat.id
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <span className="mr-1 text-xs">{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      {/* Style Grid - Compact 3 columns with reduced height */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-[350px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-purple-200 scrollbar-track-gray-50">
        {filteredStyles.map(style => (
          <Card
            key={style.id}
            className="overflow-hidden hover:shadow-lg transition-all cursor-pointer group border-2 hover:border-purple-300"
            onClick={() => onStyleSelect(style)}
          >
            <div className="relative aspect-video bg-gradient-to-br from-purple-100 to-blue-100">
              {/* Popularity Badge */}
              {style.popularity >= 85 && (
                <div className="absolute top-1 left-1 px-1.5 py-0.5 bg-gradient-to-r from-orange-500 to-red-500 text-white text-[9px] font-bold rounded-full flex items-center gap-0.5">
                  <TrendingUp className="w-2 h-2" />
                  Hot
                </div>
              )}

              {/* Overlay on hover */}
              <div className="absolute inset-0 bg-gradient-to-t from-purple-600/90 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <div className="text-white text-center p-1.5">
                  <Sparkles className="w-5 h-5 mx-auto mb-0.5" />
                  <p className="text-[10px] font-medium">Click to Apply</p>
                </div>
              </div>
            </div>

            <CardContent className="p-2">
              <h4 className="font-semibold text-xs text-gray-800 mb-0.5 line-clamp-1">{style.name}</h4>
              <p className="text-[10px] text-gray-600 line-clamp-2">{style.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Custom Style CTA - Compact */}
      <Card className="bg-gradient-to-r from-purple-500 to-pink-500 text-white mt-3">
        <CardContent className="p-3 text-center">
          <Sparkles className="w-8 h-8 mx-auto mb-1.5" />
          <h4 className="font-bold text-sm mb-1">Can't Find Your Style?</h4>
          <p className="text-[11px] mb-2 text-white/90">
            Describe your dream design and let AI create it
          </p>
          <Button
            variant="outline"
            size="sm"
            className="bg-white text-purple-600 hover:bg-gray-100 border-white h-7 text-xs"
          >
            Create Custom Style
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

