import React from 'react'
import { Handle, Position } from 'reactflow'
import './nodes.css'

function RoomNode({ data, selected }) {
  return (
    <div className={`room-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      
      <div className="room-node-header">
        <div className="room-node-title">{data.name}</div>
        <div className="room-node-type">{data.roomType}</div>
      </div>
      
      <div className="room-node-stats">
        <div className="room-stat">
          <span className="stat-icon">🎨</span>
          <span className="stat-value">{data.materialsCount}</span>
        </div>
        <div className="room-stat">
          <span className="stat-icon">🔧</span>
          <span className="stat-value">{data.fixturesCount}</span>
        </div>
        <div className="room-stat">
          <span className="stat-icon">📍</span>
          <span className="stat-value">Floor {data.floor}</span>
        </div>
      </div>
    </div>
  )
}

export default RoomNode

