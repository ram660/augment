'use client';

import { 
  Palette, 
  Layers, 
  Wand2, 
  Image as ImageIcon,
  Upload,
  Sparkles
} from 'lucide-react';

export default function StudioPage() {
  return (
    <div className="h-full flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-pink-50">
      <div className="text-center max-w-2xl px-6">
        {/* Icon */}
        <div className="w-24 h-24 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
          <Palette className="w-12 h-12 text-white" />
        </div>

        {/* Title */}
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Design Studio
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Advanced visual editor for your home designs
        </p>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <FeatureCard
            icon={Layers}
            title="Layer-Based Editing"
            description="Professional editing with layers"
          />
          <FeatureCard
            icon={Wand2}
            title="AI-Powered Tools"
            description="Smart editing with AI assistance"
          />
          <FeatureCard
            icon={Sparkles}
            title="Style Transfer"
            description="Transform designs instantly"
          />
        </div>

        {/* CTA */}
        <div className="flex items-center justify-center gap-4">
          <button className="flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium shadow-md hover:shadow-lg">
            <Upload className="w-5 h-5" />
            Upload Image
          </button>
          <button className="flex items-center gap-2 px-6 py-3 bg-white text-gray-700 border-2 border-gray-200 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium">
            <ImageIcon className="w-5 h-5" />
            Browse Gallery
          </button>
        </div>

        {/* Coming Soon Badge */}
        <div className="mt-8 inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
          🚧 Coming Soon - Advanced editing features in development
        </div>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
}

function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <div className="p-6 bg-white rounded-xl border-2 border-gray-100 hover:border-primary/20 hover:shadow-md transition-all">
      <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
        <Icon className="w-6 h-6 text-primary" />
      </div>
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}

