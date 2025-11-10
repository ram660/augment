import React, { useState } from 'react';
import './VariationGallery.css';
import BeforeAfterSlider from './BeforeAfterSlider';

const VariationGallery = ({ transformation, originalImage, onClose, onSelectFavorite, enableFavorite = false }) => {
  const [selectedVariation, setSelectedVariation] = useState(null);
  const [showComparison, setShowComparison] = useState(false);

  const handleSelectVariation = (variation, index) => {
    setSelectedVariation({ ...variation, index });
    setShowComparison(true);
  };

  const handleDownload = async (imageUrl, filename) => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'transformation.jpg';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download image');
    }
  };

  const handleShare = async (imageUrl) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'HomerView AI Transformation',
          text: 'Check out this room transformation!',
          url: imageUrl,
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(imageUrl);
      alert('Link copied to clipboard!');
    }
  };

  const handleSetFavorite = async (variationId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/design/transformations/${transformation.transformation_id}/favorite/${variationId}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to set favorite');
      }

      onSelectFavorite && onSelectFavorite(variationId);
      alert('✅ Marked as favorite!');
    } catch (error) {
      console.error('Failed to set favorite:', error);
      alert('Failed to mark as favorite');
    }
  };

  if (showComparison && selectedVariation) {
    return (
      <BeforeAfterSlider
        beforeImage={originalImage}
        afterImage={selectedVariation.image_url}
        onClose={() => setShowComparison(false)}
        onDownload={() => handleDownload(selectedVariation.image_url, `transformation_${selectedVariation.index + 1}.jpg`)}
        onShare={() => handleShare(selectedVariation.image_url)}
        onSetFavorite={() => handleSetFavorite(selectedVariation.id)}
      />
    );
  }

  return (
    <div className="variation-gallery">
      <div className="gallery-header">
        <div>
          <h2>🎨 Transformation Results</h2>
          <p className="transformation-type">
            {transformation.transformation_type.toUpperCase()} • {transformation.num_variations} variations
          </p>
        </div>
        <button onClick={onClose} className="close-button">✕</button>
      </div>

      <div className="gallery-content">
        {/* Original Image */}
        <div className="original-section">
          <h3>Original</h3>
          <div className="image-card original">
            <img src={originalImage} alt="Original" />
          </div>
        </div>

        {/* Variations Grid */}
        <div className="variations-section">
          <h3>Variations ({transformation.image_urls?.length || 0})</h3>
          <div className="variations-grid">
            {transformation.image_urls?.map((imageUrl, index) => (
              <div key={index} className="variation-card">
                <div className="variation-image-wrapper">
                  <img
                    src={imageUrl}
                    alt={`Variation ${index + 1}`}
                    onClick={() => handleSelectVariation({ id: index, image_url: imageUrl }, index)}
                  />
                  <div className="variation-overlay">
                    <button
                      className="overlay-button"
                      onClick={() => handleSelectVariation({ id: index, image_url: imageUrl }, index)}
                    >
                      👁️ Compare
                    </button>
                  </div>
                </div>

                <div className="variation-actions">
                  {enableFavorite && (
                    <button
                      className="action-button"
                      onClick={() => handleSetFavorite(index)}
                      title="Mark as favorite"
                    >
                      ⭐
                    </button>
                  )}
                  <button
                    className="action-button"
                    onClick={() => handleDownload(imageUrl, `transformation_${index + 1}.jpg`)}
                    title="Download"
                  >
                    ⬇️
                  </button>
                  <button
                    className="action-button"
                    onClick={() => handleShare(imageUrl)}
                    title="Share"
                  >
                    🔗
                  </button>
                </div>

                <p className="variation-label">Variation {index + 1}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Transformation Info */}
        <div className="transformation-details">
          <h3>Transformation Details</h3>
          <div className="details-grid">
            <div className="detail-item">
              <span className="detail-label">Type:</span>
              <span className="detail-value">{transformation.transformation_type}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Status:</span>
              <span className={`detail-value status-${transformation.status}`}>
                {transformation.status}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Variations:</span>
              <span className="detail-value">{transformation.num_variations}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">ID:</span>
              <span className="detail-value">{transformation.transformation_id}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="gallery-actions">
          <button className="action-button-large secondary" onClick={onClose}>
            ← Back to Studio
          </button>
          <button
            className="action-button-large primary"
            onClick={() => {
              // TODO: Implement "Apply to Room" functionality
              alert('This will apply the selected transformation to your room!');
            }}
          >
            ✨ Apply to Room
          </button>
        </div>
      </div>
    </div>
  );
};

export default VariationGallery;

