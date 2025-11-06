import React, { useState, useEffect } from 'react'
import './GalleryPage.css'

const GalleryPage = ({ homeId }) => {
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [selectedImage, setSelectedImage] = useState(null)

  useEffect(() => {
    // Fetch room images from API
    const fetchImages = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/digital-twin/homes/${homeId}`)
        const data = await response.json()
        
        // Extract all room images
        const allImages = []
        data.rooms?.forEach(room => {
          room.images?.forEach(img => {
            allImages.push({
              ...img,
              roomName: room.name,
              roomType: room.room_type
            })
          })
        })
        
        setImages(allImages)
      } catch (error) {
        console.error('Error fetching images:', error)
      } finally {
        setLoading(false)
      }
    }

    if (homeId) {
      fetchImages()
    }
  }, [homeId])

  const filteredImages = filter === 'all' 
    ? images 
    : images.filter(img => img.roomType === filter)

  const roomTypes = [...new Set(images.map(img => img.roomType))]

  return (
    <div className="gallery-page">
      <div className="gallery-header">
        <h2>🖼️ Image Gallery</h2>
        <p>View all images from your home</p>
      </div>

      <div className="gallery-content">
        <div className="gallery-filters">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Images ({images.length})
          </button>
          {roomTypes.map(type => (
            <button
              key={type}
              className={`filter-btn ${filter === type ? 'active' : ''}`}
              onClick={() => setFilter(type)}
            >
              {type} ({images.filter(img => img.roomType === type).length})
            </button>
          ))}
        </div>

        {loading ? (
          <div className="gallery-loading">
            <div className="loading-spinner"></div>
            <p>Loading images...</p>
          </div>
        ) : filteredImages.length === 0 ? (
          <div className="gallery-empty">
            <div className="empty-icon">📷</div>
            <h3>No Images Found</h3>
            <p>Upload room images to see them here</p>
          </div>
        ) : (
          <div className="gallery-grid">
            {filteredImages.map((image, index) => (
              <div
                key={index}
                className="gallery-item"
                onClick={() => setSelectedImage(image)}
              >
                <div className="image-wrapper">
                  <img
                    src={`http://localhost:8000${image.image_url}`}
                    alt={image.roomName}
                    loading="lazy"
                  />
                  <div className="image-overlay">
                    <div className="overlay-content">
                      <div className="image-title">{image.roomName}</div>
                      <div className="image-type">{image.roomType}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div className="image-modal" onClick={() => setSelectedImage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedImage(null)}>
              ✕
            </button>
            <img
              src={`http://localhost:8000${selectedImage.image_url}`}
              alt={selectedImage.roomName}
            />
            <div className="modal-info">
              <h3>{selectedImage.roomName}</h3>
              <p>{selectedImage.roomType}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GalleryPage

