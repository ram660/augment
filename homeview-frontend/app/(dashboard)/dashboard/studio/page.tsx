'use client';

import { useState, useRef, useEffect } from 'react';
import {
  Upload,
  Paintbrush,
  Home,
  Sofa,
  Lightbulb,
  Trees,
  Wand2,
  X,
  ChevronRight,
  Sparkles,
  Loader2,
  ArrowRight,
  CheckCircle
} from 'lucide-react';
import WorkspaceView from '@/components/studio/WorkspaceView';
import { useRouter } from 'next/navigation';


type WorkflowStep = 'features' | 'workspace';

// Transformation categories with all tools
const TRANSFORMATION_CATEGORIES = {
  surfaces: {
    name: 'Surfaces',
    icon: '🎨',
    color: 'from-blue-500 to-purple-500',
    tools: [
      { id: 'paint', name: 'Paint Walls', icon: '🎨', description: 'Change wall colors with any finish' },
      { id: 'flooring', name: 'Flooring', icon: '🪵', description: 'Replace floor materials' },
      { id: 'wallpaper', name: 'Wallpaper', icon: '📜', description: 'Add or change wallpaper patterns' },
      { id: 'accent_wall', name: 'Accent Wall', icon: '🖼️', description: 'Create a feature wall' },
    ]
  },
  kitchen_bath: {
    name: 'Kitchen & Bath',
    icon: '🍳',
    color: 'from-orange-500 to-red-500',
    tools: [
      { id: 'cabinets', name: 'Cabinets', icon: '🗄️', description: 'Transform cabinet style and color' },
      { id: 'countertops', name: 'Countertops', icon: '🪨', description: 'Change countertop materials' },
      { id: 'backsplash', name: 'Backsplash', icon: '🧱', description: 'Update backsplash design' },
      { id: 'fixtures', name: 'Fixtures', icon: '🚰', description: 'Replace faucets and hardware' },
      { id: 'appliances', name: 'Appliances', icon: '🔌', description: 'Update appliance style' },
    ]
  },
  furniture: {
    name: 'Furniture & Decor',
    icon: '🛋️',
    color: 'from-green-500 to-teal-500',
    tools: [
      { id: 'furniture', name: 'Furniture', icon: '🛋️', description: 'Add, remove, or replace furniture' },
      { id: 'decor', name: 'Decor', icon: '🖼️', description: 'Add decorative elements' },
      { id: 'window_treatments', name: 'Window Treatments', icon: '🪟', description: 'Add curtains, blinds, shades' },
      { id: 'rugs', name: 'Rugs & Carpets', icon: '🧶', description: 'Add or change area rugs' },
    ]
  },
  lighting: {
    name: 'Lighting',
    icon: '💡',
    color: 'from-yellow-500 to-orange-500',
    tools: [
      { id: 'lighting', name: 'Light Fixtures', icon: '💡', description: 'Replace light fixtures' },
      { id: 'natural_light', name: 'Natural Light', icon: '☀️', description: 'Adjust brightness and mood' },
      { id: 'ambient', name: 'Ambient Lighting', icon: '🕯️', description: 'Add mood lighting' },
    ]
  },
  outdoor: {
    name: 'Outdoor & Exterior',
    icon: '🌳',
    color: 'from-green-600 to-emerald-600',
    tools: [
      { id: 'exterior_paint', name: 'Exterior Paint', icon: '🏠', description: 'Change exterior colors' },
      { id: 'landscaping', name: 'Landscaping', icon: '🌳', description: 'Add plants and greenery' },
      { id: 'outdoor_furniture', name: 'Outdoor Furniture', icon: '🪑', description: 'Add patio furniture' },
      { id: 'hardscaping', name: 'Hardscaping', icon: '🪨', description: 'Add paths, patios, walls' },
    ]
  },
  advanced: {
    name: 'Advanced Tools',
    icon: '🚀',
    color: 'from-purple-600 to-pink-600',
    tools: [
      { id: 'style_transfer', name: 'Style Transfer', icon: '🎨', description: 'Complete style transformation' },
      { id: 'virtual_staging', name: 'Virtual Staging', icon: '🏡', description: 'Stage empty rooms' },
      { id: 'renovation', name: 'Renovation', icon: '🔨', description: 'Major structural changes' },
      { id: 'custom', name: 'Custom Prompt', icon: '✨', description: 'Describe any transformation' },
    ]
  },
};

export default function StudioPage() {
  const [workflowStep, setWorkflowStep] = useState<WorkflowStep>('features');
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const router = useRouter();
  useEffect(() => {
    router.replace('/dashboard/design');
  }, [router]);

  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const imageDataUrl = reader.result as string;
        setUploadedImage(imageDataUrl);

        // Skip AI analysis - go directly to workspace with pre-defined suggestions
        const predefinedSuggestions = {
          summary: {
            description: "Your room is ready for transformation! Choose from our suggestions below or write your own custom prompt.",
            colors: [],
            materials: [],
            styles: []
          },
          ideas: [
            "Change wall colors to create a fresh new look",
            "Update flooring to modern hardwood or tile",
            "Add or rearrange furniture for better flow",
            "Improve lighting with new fixtures",
            "Transform cabinets with new colors and styles",
            "Add decorative elements and accessories"
          ],
          ideas_by_theme: {
            color: [
              "Paint walls in soft neutrals (beige, gray, white)",
              "Add bold accent walls in navy, emerald, or terracotta",
              "Try warm earth tones for a cozy feel"
            ],
            flooring: [
              "Install hardwood flooring in oak or walnut",
              "Add luxury vinyl plank for durability",
              "Update with modern tile patterns"
            ],
            lighting: [
              "Add pendant lights for ambient lighting",
              "Install recessed lighting for modern look",
              "Update fixtures to match your style"
            ],
            furniture: [
              "Stage with modern furniture pieces",
              "Rearrange existing furniture for better flow",
              "Add accent chairs or side tables"
            ],
            decor: [
              "Add throw pillows and blankets",
              "Hang artwork or mirrors",
              "Include plants for natural elements"
            ]
          },
          style_transformations: [
            {
              style: "Modern",
              description: "Clean lines, neutral colors, minimal decor, and contemporary furniture"
            },
            {
              style: "Scandinavian",
              description: "Light woods, whites and pastels, cozy textiles, and functional design"
            },
            {
              style: "Industrial",
              description: "Exposed brick, metal accents, dark colors, and raw materials"
            },
            {
              style: "Farmhouse",
              description: "Rustic wood, vintage pieces, neutral palette, and cozy atmosphere"
            }
          ]
        };

        setAnalysisResult(predefinedSuggestions);
        setWorkflowStep('workspace');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleBackToFeatures = () => {
    setWorkflowStep('features');
    setUploadedImage(null);
    setAnalysisResult(null);
  };

  const handleReset = () => {
    setWorkflowStep('features');
    setUploadedImage(null);
    setAnalysisResult(null);
  };

  // Render based on workflow step
  if (workflowStep === 'workspace' && uploadedImage && analysisResult) {
    return (
      <WorkspaceView
        originalImage={uploadedImage}
        analysis={analysisResult}
        onBack={handleBackToFeatures}
      />
    );
  }

  // Features showcase - default view
  return (
    <div className="h-full flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-pink-50 p-6 overflow-auto">
      <div className="text-center max-w-6xl py-12">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="hidden"
        />

        {/* Hero Section */}
        <div className="mb-12">
          <div className="w-24 h-24 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
            <Wand2 className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Design Studio
          </h1>
            <p className="text-xl text-gray-600 mb-8">
              Transform any room with AI-powered design tools. No login required.
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-primary to-secondary text-white rounded-xl hover:shadow-xl transition-all font-semibold text-lg"
            >
              <Upload className="w-6 h-6" />
              Upload Room Image to Start
            </button>
          </div>

          {/* Capabilities Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {Object.entries(TRANSFORMATION_CATEGORIES).slice(0, 6).map(([id, category]) => (
              <div
                key={id}
                className="p-6 bg-white rounded-xl border-2 border-gray-100 hover:border-primary/30 hover:shadow-lg transition-all"
              >
                <div className={`w-14 h-14 bg-gradient-to-br ${category.color} rounded-xl flex items-center justify-center mx-auto mb-4 text-2xl`}>
                  {category.icon}
                </div>
                <h3 className="font-bold text-gray-900 mb-2 text-lg">{category.name}</h3>
                <p className="text-sm text-gray-600 mb-3">
                  {category.tools.length} tools available
                </p>
                <div className="text-xs text-gray-500 space-y-1">
                  {category.tools.slice(0, 2).map(tool => (
                    <div key={tool.id}>• {tool.name}</div>
                  ))}
                  {category.tools.length > 2 && (
                    <div>• +{category.tools.length - 2} more</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Stats */}
          <div className="flex items-center justify-center gap-8 text-sm text-gray-600">
            <div>
              <span className="font-bold text-2xl text-primary block">30+</span>
              Transformation Tools
            </div>
            <div>
              <span className="font-bold text-2xl text-primary block">6</span>
              Categories
            </div>
            <div>
              <span className="font-bold text-2xl text-primary block">∞</span>
              Possibilities
            </div>
          </div>
        </div>
      </div>
    );
  }

