import React from 'react'
import { useStudioData } from '../../hooks/useStudioData'

function Sidebar({ homeId, selectedNodes, onToggle }) {
  const { data: studioData } = useStudioData(homeId)

  if (!studioData) return null

  const allLayers = [
    { id: 'floor-plan', type: 'floorPlan', name: 'Floor Plan', icon: '📐' },
    ...(studioData.floor_plan?.rooms || []).map(room => ({
      id: `room-${room.id}`,
      type: 'room',
      name: room.name,
      icon: '🏠',
      meta: `Floor ${room.floor_level} • ${room.materials_count} materials`
    })),
    ...(studioData.images || []).map(image => ({
      id: `image-${image.id}`,
      type: 'image',
      name: `Image ${image.id.slice(0, 8)}`,
      icon: '📷',
      meta: image.room_name || 'Unlinked'
    }))
  ]

  const selectedIds = selectedNodes.map(n => n.id)

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span>Layers ({allLayers.length})</span>
        <button
          onClick={onToggle}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontSize: '1.2rem',
            padding: '4px 8px'
          }}
          title="Hide Layers"
        >
          ◀
        </button>
      </div>

      <div className="sidebar-content">
        {allLayers.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-title">No Layers</div>
            <div className="empty-state-description">
              Upload floor plans and images to see them here.
            </div>
          </div>
        ) : (
          allLayers.map(layer => (
            <div
              key={layer.id}
              className={`layer-item ${selectedIds.includes(layer.id) ? 'selected' : ''}`}
            >
              <div className="layer-icon">{layer.icon}</div>
              <div className="layer-info">
                <div className="layer-name">{layer.name}</div>
                {layer.meta && <div className="layer-meta">{layer.meta}</div>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Sidebar

