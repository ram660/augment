import React from 'react'
import './nodes.css'

function FloorPlanNode({ data }) {
  return (
    <div className="floor-plan-node" style={{ width: data.width, height: data.height }}>
      <img 
        src={data.imageUrl} 
        alt="Floor Plan" 
        style={{ 
          width: '100%', 
          height: '100%', 
          objectFit: 'contain',
          opacity: 0.7
        }}
      />
    </div>
  )
}

export default FloorPlanNode

