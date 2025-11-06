import React, { useState } from 'react'
import StudioCanvas from '../components/Studio/StudioCanvas'
import Sidebar from '../components/Studio/Sidebar'
import './StudioPage.css'

const StudioPage = ({ homeId }) => {
  const [selectedNodes, setSelectedNodes] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="studio-page">
      <div className="studio-header">
        <h2>🎨 Design Studio</h2>
        <p>Create and edit your home layout with our infinite canvas</p>
      </div>

      <div className="studio-content">
        {sidebarOpen && (
          <Sidebar
            homeId={homeId}
            selectedNodes={selectedNodes}
            onToggle={() => setSidebarOpen(false)}
          />
        )}

        {!sidebarOpen && (
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(true)}
            title="Show Layers"
          >
            ▶
          </button>
        )}

        <StudioCanvas
          homeId={homeId}
          onSelectionChange={setSelectedNodes}
        />
      </div>
    </div>
  )
}

export default StudioPage

