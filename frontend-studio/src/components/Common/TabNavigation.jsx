import React from 'react'
import './TabNavigation.css'

const TabNavigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'studio', label: 'Design Studio', icon: '🎨' },
    { id: 'transformations', label: 'Transformations', icon: '✨' },
    { id: 'chat', label: 'AI Assistant', icon: '💬' },
    { id: 'gallery', label: 'Gallery', icon: '🖼️' },
  ]

  return (
    <nav className="tab-navigation">
      <div className="tab-list">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  )
}

export default TabNavigation

