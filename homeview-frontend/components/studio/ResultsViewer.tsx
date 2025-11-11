'use client';

import { useState } from 'react';
import { X, Download, Share2, ChevronLeft, ChevronRight, ZoomIn } from 'lucide-react';
import Image from 'next/image';

interface ResultsViewerProps {
  results: string[];
  originalImage: string;
  onClose: () => void;
  onUseAsBase?: (imageUrl: string) => void;
}

export default function ResultsViewer({
  results,
  originalImage,
  onClose,
  onUseAsBase,
}: ResultsViewerProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [showComparison, setShowComparison] = useState(false);
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);

  const handleDownload = async (imageUrl: string) => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transformation-${Date.now()}.jpg`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download image');
    }
  };

  const handleShare = async (imageUrl: string) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'My Room Transformation',
          text: 'Check out my room transformation!',
          url: imageUrl,
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(imageUrl);
      alert('Image URL copied to clipboard!');
    }
  };

  const currentImage = results[selectedIndex];

  return (
    <>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-primary/10 to-secondary/10">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Transformation Results</h2>
              <p className="text-sm text-gray-600 mt-1">
                {results.length} variation{results.length > 1 ? 's' : ''} generated
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="w-6 h-6 text-gray-600" />
            </button>
          </div>

          {/* Main Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Comparison Toggle */}
            <div className="flex items-center justify-center gap-4 mb-6">
              <button
                onClick={() => setShowComparison(false)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  !showComparison
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Result Only
              </button>
              <button
                onClick={() => setShowComparison(true)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  showComparison
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Before & After
              </button>
            </div>

            {/* Image Display */}
            <div className="mb-6">
              {showComparison ? (
                <div className="grid grid-cols-2 gap-4">
                  {/* Before */}
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2 text-center">Before</p>
                    <div className="relative aspect-video rounded-lg overflow-hidden border-2 border-gray-200">
                      <Image
                        src={originalImage}
                        alt="Original"
                        fill
                        className="object-contain cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => setLightboxImage(originalImage)}
                      />
                    </div>
                  </div>
                  {/* After */}
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2 text-center">After</p>
                    <div className="relative aspect-video rounded-lg overflow-hidden border-2 border-primary">
                      <Image
                        src={currentImage}
                        alt="Transformed"
                        fill
                        className="object-contain cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => setLightboxImage(currentImage)}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="relative aspect-video rounded-lg overflow-hidden border-2 border-primary">
                  <Image
                    src={currentImage}
                    alt="Transformed"
                    fill
                    className="object-contain cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setLightboxImage(currentImage)}
                  />
                  <button
                    onClick={() => setLightboxImage(currentImage)}
                    className="absolute top-4 right-4 p-2 bg-white/90 hover:bg-white rounded-full shadow-lg transition-colors"
                  >
                    <ZoomIn className="w-5 h-5 text-gray-700" />
                  </button>
                </div>
              )}
            </div>

            {/* Variation Selector */}
            {results.length > 1 && (
              <div className="flex items-center justify-center gap-4 mb-6">
                <button
                  onClick={() => setSelectedIndex(Math.max(0, selectedIndex - 1))}
                  disabled={selectedIndex === 0}
                  className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-sm font-medium text-gray-700">
                  Variation {selectedIndex + 1} of {results.length}
                </span>
                <button
                  onClick={() => setSelectedIndex(Math.min(results.length - 1, selectedIndex + 1))}
                  disabled={selectedIndex === results.length - 1}
                  className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            )}

            {/* Thumbnail Grid */}
            {results.length > 1 && (
              <div className="grid grid-cols-4 gap-3 mb-6">
                {results.map((result, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedIndex(index)}
                    className={`relative aspect-video rounded-lg overflow-hidden border-2 transition-all ${
                      index === selectedIndex
                        ? 'border-primary ring-2 ring-primary/30'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Image
                      src={result}
                      alt={`Variation ${index + 1}`}
                      fill
                      className="object-cover"
                    />
                  </button>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => handleDownload(currentImage)}
                className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium"
              >
                <Download className="w-5 h-5" />
                Download
              </button>
              <button
                onClick={() => handleShare(currentImage)}
                className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:border-primary hover:text-primary transition-colors font-medium"
              >
                <Share2 className="w-5 h-5" />
                Share
              </button>
              {onUseAsBase && (
                <button
                  onClick={() => onUseAsBase(currentImage)}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white rounded-lg hover:shadow-lg transition-all font-medium"
                >
                  Use as Base for Next Edit
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Lightbox */}
      {lightboxImage && (
        <div
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-[60] p-4"
          onClick={() => setLightboxImage(null)}
        >
          <button
            onClick={() => setLightboxImage(null)}
            className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-white" />
          </button>
          <div className="relative w-full h-full">
            <Image
              src={lightboxImage}
              alt="Full size"
              fill
              className="object-contain"
            />
          </div>
        </div>
      )}
    </>
  );
}

