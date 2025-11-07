import React, { useState, useEffect } from 'react';
import './TransformationHistory.css';

const TransformationHistory = ({ roomImageId, onSelectTransformation, onClose }) => {
  const [transformations, setTransformations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'paint', 'flooring', etc.

  useEffect(() => {
    fetchTransformations();
  }, [roomImageId]);

  const fetchTransformations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/design/transformations/${roomImageId}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch transformations');
      }

      const data = await response.json();
      setTransformations(data.transformations || []);
    } catch (error) {
      console.error('Failed to fetch transformations:', error);
      setTransformations([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (transformationId) => {
    if (!confirm('Are you sure you want to delete this transformation?')) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/design/transformations/${transformationId}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete transformation');
      }

      // Refresh the list
      fetchTransformations();
      alert('✅ Transformation deleted successfully');
    } catch (error) {
      console.error('Failed to delete transformation:', error);
      alert('Failed to delete transformation');
    }
  };

  const filteredTransformations = transformations.filter(t => {
    if (filter === 'all') return true;
    return t.transformation_type === filter;
  });

  const getTypeIcon = (type) => {
    const icons = {
      paint: '🎨',
      flooring: '🪵',
      cabinets: '🗄️',
      countertops: '🪨',
      backsplash: '🧱',
      lighting: '💡',
      furniture: '🛋️',
    };
    return icons[type] || '✨';
  };

  const getStatusColor = (status) => {
    const colors = {
      completed: '#10b981',
      processing: '#f59e0b',
      failed: '#ef4444',
      pending: '#6b7280',
    };
    return colors[status] || '#6b7280';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="transformation-history">
        <div className="history-header">
          <h2>📜 Transformation History</h2>
          <button onClick={onClose} className="close-button">✕</button>
        </div>
        <div className="loading-state">
          <div className="spinner-large"></div>
          <p>Loading transformations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="transformation-history">
      <div className="history-header">
        <h2>📜 Transformation History</h2>
        <button onClick={onClose} className="close-button">✕</button>
      </div>

      <div className="history-content">
        {/* Filter Buttons */}
        <div className="filter-section">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({transformations.length})
          </button>
          {['paint', 'flooring', 'cabinets', 'countertops', 'backsplash', 'lighting', 'furniture'].map(type => {
            const count = transformations.filter(t => t.transformation_type === type).length;
            if (count === 0) return null;
            return (
              <button
                key={type}
                className={`filter-btn ${filter === type ? 'active' : ''}`}
                onClick={() => setFilter(type)}
              >
                {getTypeIcon(type)} {type} ({count})
              </button>
            );
          })}
        </div>

        {/* Transformations List */}
        {filteredTransformations.length === 0 ? (
          <div className="empty-state">
            <p className="empty-icon">🎨</p>
            <h3>No transformations yet</h3>
            <p>Start by creating your first transformation!</p>
          </div>
        ) : (
          <div className="transformations-list">
            {filteredTransformations.map((transformation) => (
              <div key={transformation.id} className="transformation-item">
                <div className="item-header">
                  <div className="item-type">
                    <span className="type-icon">{getTypeIcon(transformation.transformation_type)}</span>
                    <span className="type-name">{transformation.transformation_type}</span>
                  </div>
                  <div
                    className="item-status"
                    style={{ color: getStatusColor(transformation.status) }}
                  >
                    ● {transformation.status}
                  </div>
                </div>

                <div className="item-details">
                  <div className="detail-row">
                    <span className="detail-label">Created:</span>
                    <span className="detail-value">{formatDate(transformation.created_at)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Variations:</span>
                    <span className="detail-value">{transformation.num_variations}</span>
                  </div>
                  {transformation.processing_time && (
                    <div className="detail-row">
                      <span className="detail-label">Processing Time:</span>
                      <span className="detail-value">{transformation.processing_time.toFixed(2)}s</span>
                    </div>
                  )}
                </div>

                {/* Thumbnail Preview */}
                {transformation.images && transformation.images.length > 0 && (
                  <div className="item-thumbnails">
                    {transformation.images.slice(0, 4).map((img, idx) => (
                      <img
                        key={idx}
                        src={img.image_url}
                        alt={`Variation ${idx + 1}`}
                        className="thumbnail"
                      />
                    ))}
                  </div>
                )}

                <div className="item-actions">
                  <button
                    className="action-btn primary"
                    onClick={() => onSelectTransformation(transformation)}
                  >
                    👁️ View
                  </button>
                  <button
                    className="action-btn danger"
                    onClick={() => handleDelete(transformation.id)}
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TransformationHistory;

