'use client';

import React from 'react';
import { Sparkles, Lightbulb, TrendingUp, CheckCircle, ArrowRight, Palette, Home, Star } from 'lucide-react';

interface AnalysisResultsProps {
  analysis: {
    summary?: {
      colors?: Array<{ name: string; hex?: string }>;
      materials?: string[];
      styles?: string[];
      description?: string;
    };
    ideas?: string[];
    ideas_by_theme?: {
      color?: string[];
      flooring?: string[];
      lighting?: string[];
      decor?: string[];
      other?: string[];
    };
    style_transformations?: Array<{
      style: string;
      description: string;
    }>;
  };
  onProceed: () => void;
}

export default function AnalysisResults({ analysis, onProceed }: AnalysisResultsProps) {
  const summary = analysis.summary || {};
  const ideas = analysis.ideas || [];
  const ideasByTheme = analysis.ideas_by_theme || {};
  const styleTransformations = analysis.style_transformations || [];

  // Extract data from summary
  const colors = summary.colors || [];
  const materials = summary.materials || [];
  const styles = summary.styles || [];
  const description = summary.description || 'Room analysis complete';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
            AI Analysis Complete
          </h1>
          <p className="text-gray-600 text-lg">
            We've analyzed your space and identified opportunities for transformation
          </p>
        </div>

        {/* Description Card */}
        {description && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6 border border-purple-100">
            <h2 className="text-xl font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              Overview
            </h2>
            <p className="text-gray-700 leading-relaxed">{description}</p>
          </div>
        )}

        {/* Detected Elements */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Colors */}
          {colors.length > 0 && (
            <div className="bg-white rounded-xl p-5 border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Palette className="w-4 h-4 text-purple-500" />
                Detected Colors
              </h3>
              <div className="flex flex-wrap gap-2">
                {colors.map((color, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-full border border-gray-200"
                  >
                    {color.hex && (
                      <div
                        className="w-4 h-4 rounded-full border border-gray-300"
                        style={{ backgroundColor: color.hex }}
                      />
                    )}
                    <span className="text-sm text-gray-700">{color.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Materials */}
          {materials.length > 0 && (
            <div className="bg-white rounded-xl p-5 border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Home className="w-4 h-4 text-blue-500" />
                Materials
              </h3>
              <div className="flex flex-wrap gap-2">
                {materials.map((material, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-200"
                  >
                    {material}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Styles */}
          {styles.length > 0 && (
            <div className="bg-white rounded-xl p-5 border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-500" />
                Styles
              </h3>
              <div className="flex flex-wrap gap-2">
                {styles.map((style, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-yellow-50 text-yellow-700 rounded-full text-sm border border-yellow-200"
                  >
                    {style}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Transformation Ideas */}
        {ideas.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-6 border border-purple-100">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Lightbulb className="w-6 h-6 text-yellow-500" />
              Transformation Ideas
            </h2>
            <p className="text-gray-600 mb-4">
              Here are some AI-generated ideas to transform your space:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {ideas.map((idea, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border-2 border-purple-100 bg-gradient-to-br from-purple-50 to-blue-50 hover:border-purple-300 transition-colors"
                >
                  <p className="text-gray-800">{idea}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Style Transformations */}
        {styleTransformations.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-blue-100">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Star className="w-6 h-6 text-blue-500" />
              Style Suggestions
            </h2>
            <p className="text-gray-600 mb-4">
              Try these style transformations to completely reimagine your space:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {styleTransformations.map((style, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-xl border-2 border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 hover:border-blue-300 transition-colors"
                >
                  <h3 className="text-lg font-semibold text-gray-800 mb-2 capitalize">
                    {style.style}
                  </h3>
                  <p className="text-gray-700 text-sm">{style.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Proceed Button */}
        <div className="text-center">
          <button
            onClick={onProceed}
            className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
          >
            <span>Start Transforming</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          <p className="text-gray-500 text-sm mt-3">
            Choose from 30+ transformation tools or write your own prompt
          </p>
        </div>
      </div>
    </div>
  );
}

