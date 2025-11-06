import React, { useCallback, useState, useEffect } from 'react'
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant
} from 'reactflow'
import 'reactflow/dist/style.css'

import ImageNode from './nodes/ImageNode'
import RoomNode from './nodes/RoomNode'
import FloorPlanNode from './nodes/FloorPlanNode'
import Toolbar from './Toolbar'
import { useStudioData } from '../../hooks/useStudioData'

const nodeTypes = {
  image: ImageNode,
  room: RoomNode,
  floorPlan: FloorPlanNode
}

function StudioCanvas({ homeId, onSelectionChange }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [tool, setTool] = useState('select') // select, pan, measure, annotate
  
  const { data: studioData, isLoading } = useStudioData(homeId)

  // Load studio data and create nodes
  useEffect(() => {
    if (!studioData) return

    const newNodes = []
    const newEdges = []

    // Add floor plan as background node
    if (studioData.floor_plan) {
      newNodes.push({
        id: 'floor-plan',
        type: 'floorPlan',
        position: { x: 100, y: 100 },
        data: {
          imageUrl: studioData.floor_plan.image_url,
          width: 800,
          height: 600
        },
        draggable: false,
        selectable: false
      })

      // Add room nodes
      studioData.floor_plan.rooms?.forEach((room, index) => {
        const roomNode = {
          id: `room-${room.id}`,
          type: 'room',
          position: {
            x: 100 + (room.bounds?.x || index * 150),
            y: 100 + (room.bounds?.y || index * 100)
          },
          data: {
            roomId: room.id,
            name: room.name,
            roomType: room.room_type,
            floor: room.floor_level,
            materialsCount: room.materials_count || 0,
            fixturesCount: room.fixtures_count || 0
          },
          parentNode: 'floor-plan'
        }
        newNodes.push(roomNode)
      })
    }

    // Add image nodes
    studioData.images?.forEach((image, index) => {
      const imageNode = {
        id: `image-${image.id}`,
        type: 'image',
        position: {
          x: image.position?.x || (1000 + (index % 3) * 220),
          y: image.position?.y || (100 + Math.floor(index / 3) * 220)
        },
        data: {
          imageId: image.id,
          imageUrl: image.url,
          roomId: image.room_id,
          roomName: image.room_name
        }
      }
      newNodes.push(imageNode)

      // Create edge if linked to room
      if (image.room_id) {
        newEdges.push({
          id: `edge-${image.id}-${image.room_id}`,
          source: `image-${image.id}`,
          target: `room-${image.room_id}`,
          type: 'default',
          animated: false,
          style: { stroke: '#667eea', strokeWidth: 2 }
        })
      }
    })

    setNodes(newNodes)
    setEdges(newEdges)
  }, [studioData, setNodes, setEdges])

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onSelectionChangeHandler = useCallback(
    ({ nodes: selectedNodes }) => {
      const selectedIds = selectedNodes.map(node => ({
        id: node.id,
        type: node.type,
        data: node.data
      }))
      onSelectionChange(selectedIds)
    },
    [onSelectionChange]
  )

  if (isLoading) {
    return (
      <div className="studio-canvas" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#6b7280' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🏗️</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 600 }}>Loading Studio...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="studio-canvas">
      <Toolbar tool={tool} onToolChange={setTool} />
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onSelectionChange={onSelectionChangeHandler}
        nodeTypes={nodeTypes}
        fitView
        panOnDrag={tool === 'pan'}
        selectionOnDrag={tool === 'select'}
        multiSelectionKeyCode="Shift"
        deleteKeyCode="Delete"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e5e7eb" />
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            if (node.type === 'floorPlan') return '#f3f4f6'
            if (node.type === 'room') return '#ede9fe'
            if (node.type === 'image') return '#dbeafe'
            return '#e5e7eb'
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>
    </div>
  )
}

export default StudioCanvas

