import React, { useState, useRef, useEffect } from 'react';
import './BeforeAfterSlider.css';

const BeforeAfterSlider = ({ beforeImage, afterImage, onClose, onDownload, onShare, onSetFavorite }) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [viewMode, setViewMode] = useState('slider'); // 'slider', 'side-by-side', 'before', 'after'
  const containerRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging || !containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = (x / rect.width) * 100;
      setSliderPosition(Math.max(0, Math.min(100, percentage)));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const renderSliderView = () => (
    <div
      ref={containerRef}
      className="slider-container"
      onMouseDown={handleMouseDown}
    >
      {/* After Image (Full) */}
      <div className="image-layer after-image">
        <img src={afterImage} alt="After" draggable="false" />
        <div className="image-label after-label">After</div>
      </div>

      {/* Before Image (Clipped) */}
      <div
        className="image-layer before-image"
        style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
      >
        <img src={beforeImage} alt="Before" draggable="false" />
        <div className="image-label before-label">Before</div>
      </div>

      {/* Slider Handle */}
      <div
        className="slider-handle"
        style={{ left: `${sliderPosition}%` }}
      >
        <div className="slider-line"></div>
        <div className="slider-button">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  );

  const renderSideBySideView = () => (
    <div className="side-by-side-container">
      <div className="side-image">
        <img src={beforeImage} alt="Before" />
        <div className="image-label before-label">Before</div>
      </div>
      <div className="side-image">
        <img src={afterImage} alt="After" />
        <div className="image-label after-label">After</div>
      </div>
    </div>
  );

  const renderSingleView = (image, label) => (
    <div className="single-view-container">
      <img src={image} alt={label} />
      <div className={`image-label ${label.toLowerCase()}-label`}>{label}</div>
    </div>
  );

  return (
    <div className="before-after-slider">
      <div className="slider-header">
        <div className="header-left">
          <h2>🔍 Compare Transformation</h2>
        </div>
        <div className="header-right">
          <button onClick={onClose} className="close-button">✕</button>
        </div>
      </div>

      <div className="slider-content">
        {/* View Mode Selector */}
        <div className="view-mode-selector">
          <button
            className={`mode-button ${viewMode === 'slider' ? 'active' : ''}`}
            onClick={() => setViewMode('slider')}
          >
            ↔️ Slider
          </button>
          <button
            className={`mode-button ${viewMode === 'side-by-side' ? 'active' : ''}`}
            onClick={() => setViewMode('side-by-side')}
          >
            ⬌ Side by Side
          </button>
          <button
            className={`mode-button ${viewMode === 'before' ? 'active' : ''}`}
            onClick={() => setViewMode('before')}
          >
            📷 Before Only
          </button>
          <button
            className={`mode-button ${viewMode === 'after' ? 'active' : ''}`}
            onClick={() => setViewMode('after')}
          >
            ✨ After Only
          </button>
        </div>

        {/* Image Comparison */}
        <div className="comparison-area">
          {viewMode === 'slider' && renderSliderView()}
          {viewMode === 'side-by-side' && renderSideBySideView()}
          {viewMode === 'before' && renderSingleView(beforeImage, 'Before')}
          {viewMode === 'after' && renderSingleView(afterImage, 'After')}
        </div>

        {/* Actions */}
        <div className="slider-actions">
          <button className="action-btn" onClick={onSetFavorite}>
            ⭐ Mark as Favorite
          </button>
          <button className="action-btn" onClick={onDownload}>
            ⬇️ Download
          </button>
          <button className="action-btn" onClick={onShare}>
            🔗 Share
          </button>
          <button className="action-btn secondary" onClick={onClose}>
            ← Back to Gallery
          </button>
        </div>

        {/* Instructions */}
        {viewMode === 'slider' && (
          <div className="slider-instructions">
            <p>💡 <strong>Tip:</strong> Click and drag the slider to compare before and after</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BeforeAfterSlider;

