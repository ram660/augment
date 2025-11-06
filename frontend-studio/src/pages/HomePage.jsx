import React from 'react'
import './HomePage.css'

const HomePage = ({ homeId, homes = [] }) => {
  const selectedHome = homes.find(h => h.id === homeId)

  // Format address from object to string
  const formatAddress = (address) => {
    if (!address) return 'Not specified'
    if (typeof address === 'string') return address
    const parts = []
    if (address.street) parts.push(address.street)
    if (address.city) parts.push(address.city)
    if (address.province || address.state) parts.push(address.province || address.state)
    if (address.postal_code || address.zip_code) parts.push(address.postal_code || address.zip_code)
    return parts.join(', ') || 'Not specified'
  }

  return (
    <div className="home-page">
      <div className="home-hero">
        <div className="hero-content">
          <h1 className="hero-title">
            Welcome to HomeVision AI 🏠
          </h1>
          <p className="hero-subtitle">
            Your intelligent home design and transformation platform
          </p>
        </div>
      </div>

      {selectedHome && (
        <div className="home-overview">
          <div className="overview-card">
            <div className="card-header">
              <h2>🏡 {selectedHome.name}</h2>
              <span className="home-type-badge">{selectedHome.home_type || 'Home'}</span>
            </div>
            <div className="card-content">
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Address</span>
                  <span className="info-value">{formatAddress(selectedHome.address)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Year Built</span>
                  <span className="info-value">{selectedHome.year_built || 'Unknown'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Square Footage</span>
                  <span className="info-value">{selectedHome.square_footage ? `${selectedHome.square_footage.toLocaleString()} sq ft` : 'Not specified'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Stories</span>
                  <span className="info-value">{selectedHome.num_floors || 1}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="quick-actions">
            <h3>Quick Actions</h3>
            <div className="action-grid">
              <button className="action-card" onClick={() => window.location.hash = '#studio'}>
                <div className="action-icon">🎨</div>
                <div className="action-title">Design Studio</div>
                <div className="action-desc">Edit your home layout and design</div>
              </button>

              <button className="action-card" onClick={() => window.location.hash = '#transformations'}>
                <div className="action-icon">✨</div>
                <div className="action-title">Transform Rooms</div>
                <div className="action-desc">AI-powered room transformations</div>
              </button>

              <button className="action-card" onClick={() => window.location.hash = '#chat'}>
                <div className="action-icon">💬</div>
                <div className="action-title">AI Assistant</div>
                <div className="action-desc">Chat with your home AI assistant</div>
              </button>

              <button className="action-card" onClick={() => window.location.hash = '#gallery'}>
                <div className="action-icon">🖼️</div>
                <div className="action-title">Gallery</div>
                <div className="action-desc">View all your home images</div>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="features-section">
        <h3>Platform Features</h3>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🏗️</div>
            <h4>Digital Twin</h4>
            <p>Complete digital representation of your home with floor plans and room data</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h4>AI-Powered</h4>
            <p>Gemini AI analyzes your home and provides intelligent recommendations</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎨</div>
            <h4>Design Tools</h4>
            <p>Professional design studio with infinite canvas and real-time collaboration</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">✨</div>
            <h4>Transformations</h4>
            <p>Generate photorealistic room transformations with Gemini Imagen 4.0</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">💰</div>
            <h4>Cost Estimation</h4>
            <p>Get accurate cost estimates for materials and renovations</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h4>Product Matching</h4>
            <p>Find products that fit your rooms perfectly based on dimensions</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage

