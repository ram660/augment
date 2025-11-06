import React from 'react'
import ChatPanel from '../components/Studio/ChatPanel'
import './ChatPage.css'

const ChatPage = ({ homeId }) => {
  return (
    <div className="chat-page">
      <div className="chat-header">
        <h2>💬 AI Assistant</h2>
        <p>Ask questions about your home, get design advice, and cost estimates</p>
      </div>

      <div className="chat-content">
        <div className="chat-container">
          <ChatPanel
            homeId={homeId}
            selectedNodes={[]}
            fullPage={true}
          />
        </div>

        <div className="chat-sidebar">
          <div className="sidebar-section">
            <h3>💡 Suggested Questions</h3>
            <div className="suggestions">
              <button className="suggestion-btn">
                What materials are in my kitchen?
              </button>
              <button className="suggestion-btn">
                How much would it cost to renovate the master bathroom?
              </button>
              <button className="suggestion-btn">
                What's the total square footage of my home?
              </button>
              <button className="suggestion-btn">
                Show me all the fixtures in the living room
              </button>
              <button className="suggestion-btn">
                What products would fit in my bedroom?
              </button>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>🎯 AI Capabilities</h3>
            <div className="capabilities">
              <div className="capability-item">
                <span className="capability-icon">🏠</span>
                <div>
                  <strong>Home Analysis</strong>
                  <p>Analyze floor plans and room layouts</p>
                </div>
              </div>
              <div className="capability-item">
                <span className="capability-icon">💰</span>
                <div>
                  <strong>Cost Estimation</strong>
                  <p>Calculate renovation and material costs</p>
                </div>
              </div>
              <div className="capability-item">
                <span className="capability-icon">🔍</span>
                <div>
                  <strong>Product Matching</strong>
                  <p>Find products that fit your rooms</p>
                </div>
              </div>
              <div className="capability-item">
                <span className="capability-icon">🎨</span>
                <div>
                  <strong>Design Advice</strong>
                  <p>Get professional design recommendations</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage

