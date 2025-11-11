import React, { useState, useRef } from 'react'
import EnhancedTransformationPanel from '../components/Studio/EnhancedTransformationPanel'
import './TransformationsPage.css'

const TransformationsPage = ({ homeId }) => {
  const [showTransformPanel, setShowTransformPanel] = useState(false)
  const [selectedRoomImage, setSelectedRoomImage] = useState(null)
  const [uploadedImage, setUploadedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const fileInputRef = useRef(null)



  const handleImageUpload = (e) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file)
      const reader = new FileReader()
      reader.onloadend = () => setImagePreview(reader.result)
      reader.readAsDataURL(file)
    }
  }

  const handleOpenPanel = () => {
    if (!imagePreview) {
      fileInputRef.current?.click()
    } else {
      setSelectedRoomImage({
        id: 'uploaded-image',
        image_url: imagePreview,
        file: uploadedImage
      })
      setShowTransformPanel(true)
    }
  }

  return (
    <div className="transformations-page">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        style={{ display: 'none' }}
      />

      {!imagePreview ? (
        <div className="empty-state">
          <div className="empty-content">
            <div className="empty-icon">✨</div>
            <h1>Design Studio</h1>
            <p>Transform any room with AI-powered design tools</p>
            <button className="upload-btn" onClick={handleOpenPanel}>
              <span>📸</span>
              Upload Room Image
            </button>
          </div>
        </div>
      ) : (
        <div className="studio-workspace">
          <div className="workspace-sidebar">
            <div className="image-container">
              <img src={imagePreview} alt="Room" />
              <button
                className="change-btn"
                onClick={() => fileInputRef.current?.click()}
              >
                Change Image
              </button>
            </div>
          </div>

          <div className="workspace-main">
            <div className="main-header">
              <h2>Select Transformation</h2>
              <p>Choose what you'd like to transform in your room</p>
            </div>
            <button className="start-btn" onClick={handleOpenPanel}>
              Open Design Tools
            </button>
          </div>
        </div>
      )}

      {showTransformPanel && (
        <EnhancedTransformationPanel
          roomImage={selectedRoomImage}
          onTransform={(result) => {
            setShowTransformPanel(false)
          }}
          onClose={() => setShowTransformPanel(false)}
        />
      )}
    </div>
  )
}

export default TransformationsPage

