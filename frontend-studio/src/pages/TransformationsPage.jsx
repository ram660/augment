import React, { useState } from 'react'
import TransformationPanel from '../components/Studio/TransformationPanel'
import VariationGallery from '../components/Studio/VariationGallery'
import TransformationHistory from '../components/Studio/TransformationHistory'
import './TransformationsPage.css'

const TransformationsPage = ({ homeId }) => {
  const [showTransformPanel, setShowTransformPanel] = useState(false)
  const [showGallery, setShowGallery] = useState(false)
  const [selectedRoomImage, setSelectedRoomImage] = useState(null)
  const [transformationResult, setTransformationResult] = useState(null)

  const transformationTypes = [
    {
      id: 'paint',
      name: 'Paint Walls',
      icon: '🎨',
      description: 'Change wall colors with photorealistic results',
      color: '#667eea'
    },
    {
      id: 'flooring',
      name: 'Flooring',
      icon: '🪵',
      description: 'Replace floor materials (hardwood, tile, carpet)',
      color: '#764ba2'
    },
    {
      id: 'cabinets',
      name: 'Cabinets',
      icon: '🗄️',
      description: 'Transform cabinet style and color',
      color: '#f59e0b'
    },
    {
      id: 'countertops',
      name: 'Countertops',
      icon: '🪨',
      description: 'Change countertop materials (granite, quartz, marble)',
      color: '#10b981'
    },
    {
      id: 'backsplash',
      name: 'Backsplash',
      icon: '🧱',
      description: 'Update backsplash design and pattern',
      color: '#3b82f6'
    },
    {
      id: 'lighting',
      name: 'Lighting',
      icon: '💡',
      description: 'Replace light fixtures and styles',
      color: '#f59e0b'
    },
    {
      id: 'furniture',
      name: 'Furniture',
      icon: '🛋️',
      description: 'Add, remove, or replace furniture',
      color: '#8b5cf6'
    }
  ]

  const handleStartTransformation = (type) => {
    // Use test image for now
    setSelectedRoomImage({
      id: 'test-room-1',
      image_url: '/uploads/room_images/genMid.R2929648_10_4 (1).jpg',
      transformationType: type
    })
    setShowTransformPanel(true)
  }

  return (
    <div className="transformations-page">
      <div className="transformations-header">
        <h2>✨ AI Transformations</h2>
        <p>Generate photorealistic room transformations powered by Gemini Imagen 4.0</p>
      </div>

      <div className="transformations-content">
        <div className="transformation-types">
          <h3>Select Transformation Type</h3>
          <div className="types-grid">
            {transformationTypes.map((type) => (
              <button
                key={type.id}
                className="type-card"
                onClick={() => handleStartTransformation(type.id)}
                style={{ '--card-color': type.color }}
              >
                <div className="type-icon">{type.icon}</div>
                <div className="type-name">{type.name}</div>
                <div className="type-description">{type.description}</div>
                <div className="type-action">
                  Start Transformation →
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="transformation-history-section">
          <h3>Recent Transformations</h3>
          <TransformationHistory homeId={homeId} />
        </div>
      </div>

      {/* Transformation Panel */}
      {showTransformPanel && (
        <TransformationPanel
          roomImage={selectedRoomImage}
          onTransform={(result) => {
            setTransformationResult(result)
            setShowTransformPanel(false)
            setShowGallery(true)
          }}
          onClose={() => setShowTransformPanel(false)}
        />
      )}

      {/* Variation Gallery */}
      {showGallery && transformationResult && (
        <VariationGallery
          transformationId={transformationResult.transformation_id}
          variations={transformationResult.image_urls}
          originalImage={selectedRoomImage}
          onClose={() => {
            setShowGallery(false)
            setTransformationResult(null)
          }}
        />
      )}
    </div>
  )
}

export default TransformationsPage

