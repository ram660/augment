import React, { useState, useEffect } from 'react'
import Header from './components/Common/Header'
import TabNavigation from './components/Common/TabNavigation'
import TestPage from './pages/TestPage'
import HomePage from './pages/HomePage'
import StudioPage from './pages/StudioPage'
import TransformationsPage from './pages/TransformationsPage'
import ChatPage from './pages/ChatPage'
import GalleryPage from './pages/GalleryPage'
import { useHomes } from './hooks/useHomes'
import './styles/app.css'

function App() {
  const { homes, isLoading: homesLoading } = useHomes()
  const [selectedHomeId, setSelectedHomeId] = useState(null)
  const [activeTab, setActiveTab] = useState('home')

  // Auto-select first home when homes are loaded
  useEffect(() => {
    if (!homesLoading && homes.length > 0 && !selectedHomeId) {
      setSelectedHomeId(homes[0].id)
    }
  }, [homes, homesLoading, selectedHomeId])

  // Handle hash-based navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1)
      if (hash && ['home', 'studio', 'transformations', 'chat', 'gallery'].includes(hash)) {
        setActiveTab(hash)
      }
    }

    handleHashChange()
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    window.location.hash = tab
  }

  // Show loading state while homes are loading
  if (homesLoading) {
    return (
      <div className="app">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          flexDirection: 'column',
          gap: '20px'
        }}>
          <div style={{ fontSize: '4rem' }}>🏠</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#667eea' }}>
            Loading HomeVision AI Studio...
          </div>
        </div>
      </div>
    )
  }

  // Show message if no homes found
  if (!homesLoading && homes.length === 0) {
    return (
      <div className="app">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          flexDirection: 'column',
          gap: '20px',
          padding: '40px'
        }}>
          <div style={{ fontSize: '4rem' }}>🏗️</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#667eea' }}>
            No Homes Found
          </div>
          <div style={{ fontSize: '1rem', color: '#6b7280', textAlign: 'center', maxWidth: '500px' }}>
            Please create a home first using the data import script or the API.
          </div>
          <button
            className="header-btn"
            style={{ marginTop: '20px', padding: '12px 24px' }}
            onClick={() => window.location.href = '/'}
          >
            Go to Main Interface
          </button>
        </div>
      </div>
    )
  }

  // Render active page
  const renderPage = () => {
    try {
      switch (activeTab) {
        case 'home':
          return <TestPage homeId={selectedHomeId} homes={homes} />
        case 'studio':
          return <StudioPage homeId={selectedHomeId} />
        case 'transformations':
          return <TransformationsPage homeId={selectedHomeId} />
        case 'chat':
          return <ChatPage homeId={selectedHomeId} />
        case 'gallery':
          return <GalleryPage homeId={selectedHomeId} />
        default:
          return <TestPage homeId={selectedHomeId} homes={homes} />
      }
    } catch (error) {
      console.error('Error rendering page:', error)
      return (
        <div style={{ padding: '40px', textAlign: 'center' }}>
          <h2>Error loading page</h2>
          <p>{error.message}</p>
        </div>
      )
    }
  }

  return (
    <div className="app">
      <Header
        selectedHomeId={selectedHomeId}
        onHomeChange={setSelectedHomeId}
      />

      <TabNavigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      <div className="app-content">
        {renderPage()}
      </div>
    </div>
  )
}

export default App

