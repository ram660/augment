import React from 'react'
import { Handle, Position } from 'reactflow'
import './nodes.css'

function ImageNode({ data, selected }) {
  return (
    <div className={`image-node ${selected ? 'selected' : ''}`}>
      <Handle type="source" position={Position.Bottom} />
      
      <div className="image-node-preview">
        <img 
          src={data.imageUrl} 
          alt="Room" 
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      </div>
      
      <div className="image-node-label">
        <div className="image-node-title">📷 Image</div>
        {data.roomName && (
          <div className="image-node-room">→ {data.roomName}</div>
        )}
      </div>
    </div>
  )
}

export default ImageNode

