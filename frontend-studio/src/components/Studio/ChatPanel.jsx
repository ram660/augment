import React, { useState, useRef, useEffect } from 'react'
import { useChat } from '../../hooks/useChat'

function ChatPanel({ homeId, selectedNodes, onToggle, fullPage = false }) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])
  const messagesEndRef = useRef(null)
  const { sendMessage, isLoading } = useChat(homeId)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!message.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setMessage('')

    try {
      const response = await sendMessage(message, selectedNodes, messages)
      
      const aiMessage = {
        role: 'ai',
        content: response,
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      const errorMessage = {
        role: 'ai',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={`chat-panel ${fullPage ? 'full-page' : ''}`}>
      {!fullPage && (
        <div className="chat-header">
          <span>💬 AI Assistant</span>
          <button
            onClick={onToggle}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1.2rem',
              padding: '4px 8px',
              marginLeft: 'auto'
            }}
            title="Hide Chat"
          >
            ▶
          </button>
        </div>
      )}
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#6b7280', padding: '40px 20px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🤖</div>
            <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
              Ask me anything about your home!
            </div>
            <div style={{ fontSize: '0.85rem' }}>
              Select items on the canvas and ask questions about them.
            </div>
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.role}`}>
            <div className={`message-bubble ${msg.role}`}>
              {msg.content}
            </div>
            {msg.role === 'user' && selectedNodes.length > 0 && (
              <div className="message-context">
                Context: {selectedNodes.length} item{selectedNodes.length > 1 ? 's' : ''} selected
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="chat-message ai">
            <div className="message-bubble ai">
              <span style={{ opacity: 0.6 }}>Thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        {selectedNodes.length > 0 && (
          <div style={{ 
            fontSize: '0.75rem', 
            color: '#667eea', 
            marginBottom: '8px',
            fontWeight: 500
          }}>
            📍 {selectedNodes.length} item{selectedNodes.length > 1 ? 's' : ''} selected
          </div>
        )}
        
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            placeholder="Ask about your home..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            rows={1}
          />
          <button 
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatPanel

