import React, { useCallback, useState, useEffect } from 'react'
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  useReactFlow
} from 'reactflow'
import 'reactflow/dist/style.css'
import axios from 'axios'


import ImageNode from './nodes/ImageNode'
import RoomNode from './nodes/RoomNode'
import FloorPlanNode from './nodes/FloorPlanNode'
import Toolbar from './Toolbar'
import VariationGallery from './VariationGallery'

import { useStudioData } from '../../hooks/useStudioData'

const nodeTypes = {
  image: ImageNode,
  room: RoomNode,
  floorPlan: FloorPlanNode
}

function StudioCanvas({ homeId, onSelectionChange }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  // Precise Edit (polygon) state
  const [selectedImageId, setSelectedImageId] = useState(null)
  const [polyPts, setPolyPts] = useState([]) // normalized [[x,y], ...]
  const [showGallery, setShowGallery] = useState(false)
  const [lastTransformation, setLastTransformation] = useState(null)
  const [origImageForGallery, setOrigImageForGallery] = useState(null)
  const [segmentClass, setSegmentClass] = useState('floor')
  const [hoverPt, setHoverPt] = useState(null)

  const [overlayRect, setOverlayRect] = useState(null)

  const [tool, setTool] = useState('select') // select, pan, measure, annotate

  const [isSaving, setIsSaving] = useState(false)

  const { data: studioData, isLoading } = useStudioData(homeId)

  // Load studio data and create nodes (apply saved canvas state if available)
  useEffect(() => {
    if (!studioData) return

    let newNodes = []
    let newEdges = []

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

    // Try apply saved canvas state (positions/edges)
    const applySaved = async () => {
      try {
        const { data: saved } = await axios.get(`/api/digital-twin/homes/${homeId}/studio/canvas`)
        if (saved?.nodes?.length) {
          const posById = new Map(saved.nodes.map((n) => [n.id, n.position]))
          newNodes = newNodes.map((n) => (posById.has(n.id) ? { ...n, position: posById.get(n.id) } : n))
        }
        if (saved?.edges?.length) {
          const nodeIds = new Set(newNodes.map((n) => n.id))
          newEdges = saved.edges
            .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
            .map((e) => ({
              id: e.id || `${e.source}-${e.target}`,
              source: e.source,
              target: e.target,
              type: e.type || 'default',
              animated: false,
              style: { stroke: '#667eea', strokeWidth: 2 },
            }))
        }
      } catch (e) {
        // ignore - no saved state yet
      }
      setNodes(newNodes)
      setEdges(newEdges)
    }
    applySaved()
  }, [studioData, homeId, setNodes, setEdges])

  const onConnect = useCallback(
    async (params) => {
      // Only allow linking images -> rooms
      const { source, target } = params
      const isImageToRoom = source?.startsWith('image-') && target?.startsWith('room-')
      const isRoomToImage = source?.startsWith('room-') && target?.startsWith('image-')
      if (!isImageToRoom && !isRoomToImage) return

      const imageNodeId = isImageToRoom ? source : target
      const roomNodeId = isImageToRoom ? target : source
      const imageId = imageNodeId.replace('image-', '')
      const roomId = roomNodeId.replace('room-', '')

      try {
        await axios.patch(`/api/digital-twin/images/${imageId}/link`, { room_id: roomId })
        // Add edge
        setEdges((eds) =>
          addEdge(
            {
              ...params,
              source: imageNodeId,
              target: roomNodeId,
              type: 'default',
              animated: false,
              style: { stroke: '#667eea', strokeWidth: 2 },
            },
            eds,
          ),
        )
        // Update image node label with room name
        setNodes((nds) => {
          const roomNode = nds.find((n) => n.id === roomNodeId)
          const roomName = roomNode?.data?.name
          return nds.map((n) =>
            n.id === imageNodeId ? { ...n, data: { ...n.data, roomId, roomName } } : n,
          )
        })
      } catch (e) {
        console.error('Link image to room failed', e)
      }
    },
    [setEdges, setNodes],
  )

  const onSave = useCallback(async () => {
    setIsSaving(true)
    try {
      const payload = {
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data,
          parentNode: n.parentNode,
        })),
        edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target, type: e.type })),
        viewport: null,
      }
      await axios.put(`/api/digital-twin/homes/${homeId}/studio/canvas`, payload)
    } catch (e) {
      console.error('Save canvas failed', e)
    } finally {
      setIsSaving(false)
    }
  }, [nodes, edges, homeId])

  const onAutoArrange = useCallback(() => {
    setNodes((nds) => {
      const next = nds.map((n) => ({ ...n }))
      const roomPositions = new Map(next.filter((n) => n.id.startsWith('room-')).map((n) => [n.id, n.position]))
      const imageToRoom = new Map()
      edges.forEach((e) => {
        const imgId = e.source.startsWith('image-') ? e.source : e.target.startsWith('image-') ? e.target : null
        const rmId = e.source.startsWith('room-') ? e.source : e.target.startsWith('room-') ? e.target : null
        if (imgId && rmId) imageToRoom.set(imgId, rmId)
      })
      const groups = new Map()
      next.forEach((n) => {
        if (n.id.startsWith('image-')) {
          const rmId = imageToRoom.get(n.id) || (n.data?.roomId ? `room-${n.data.roomId}` : null)
          if (!rmId) return
          if (!groups.has(rmId)) groups.set(rmId, [])
          groups.get(rmId).push(n.id)
        }
      })
      groups.forEach((imageIds, rmId) => {
        const center = roomPositions.get(rmId) || { x: 0, y: 0 }
        const radius = 160
        const count = imageIds.length || 1
        imageIds.forEach((imgId, i) => {
          const angle = (i / count) * Math.PI * 2
          const x = center.x + radius * Math.cos(angle)
          const y = center.y + radius * Math.sin(angle)
          const idx = next.findIndex((n) => n.id === imgId)
          if (idx >= 0) next[idx] = { ...next[idx], position: { x, y } }
        })
      })
      return next
    })
  }, [edges, setNodes])

  const onSelectionChangeHandler = useCallback(
    ({ nodes: selectedNodes }) => {
      const selectedIds = selectedNodes.map(node => ({
        id: node.id,
        type: node.type,
        data: node.data
      }))
      onSelectionChange(selectedIds)
      // Track a single selected image for Polygon edits
      const img = selectedNodes.find(n => n.type === 'image')
      setSelectedImageId(img ? img.id : null)
      // Reset polygon points when selection changes
      setPolyPts([])
    },
    [onSelectionChange]
  )

  // Keep an up-to-date overlay rect of the selected image when in polygon mode
  useEffect(() => {
    if (!(tool === 'polygon' || tool === 'segment') || !selectedImageId) {
      setOverlayRect(null)
      return
    }
    const nodeEl = document.querySelector(`.react-flow__node[data-id="${selectedImageId}"] .image-node-preview`)
    if (nodeEl) {
      setOverlayRect(nodeEl.getBoundingClientRect())
    } else {
      setOverlayRect(null)
    }
    const onResize = () => {
      const el = document.querySelector(`.react-flow__node[data-id="${selectedImageId}"] .image-node-preview`)
      if (el) setOverlayRect(el.getBoundingClientRect())
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [tool, selectedImageId, nodes])

  // Collect polygon points with pane clicks mapped into the selected image rect
  const onPaneClick = useCallback((evt) => {
    if (tool !== 'polygon' || !selectedImageId || !overlayRect) return
    const { clientX, clientY } = evt
    const { left, top, width, height } = overlayRect
    if (clientX < left || clientX > left + width || clientY < top || clientY > top + height) return
    const x = (clientX - left) / width
    const y = (clientY - top) / height
    setPolyPts((prev) => [...prev, [x, y]])
  }, [tool, selectedImageId, overlayRect])

  // Submit precise edit request
  const applyPreciseEdit = useCallback(async () => {
    if (!selectedImageId || polyPts.length < 3) return
    const isReplace = window.confirm('Replace selected area? OK = Replace, Cancel = Remove')
    let replacement_prompt = null
    const operation = isReplace ? 'replace' : 'remove'
    if (isReplace) {
      const input = window.prompt('Describe the replacement (e.g., "matte white cabinets"):', 'matte white cabinets')
      if (input === null) return
      replacement_prompt = input
    }
    const imageId = selectedImageId.replace('image-', '')
    try {
      const res = await axios.post('/api/v1/design/precise-edit', {
        room_image_id: imageId,
        mode: 'polygon',
        points_normalized: polyPts,
        operation,
        replacement_prompt,
      })
      if (res?.data) {
        setLastTransformation(res.data)
        const imgNode = nodes.find((n) => n.id === selectedImageId)
        setOrigImageForGallery(imgNode?.data?.imageUrl || null)
        setShowGallery(true)
      }
    } catch (e) {
      console.error('Precise edit failed', e)
      alert('Precise edit failed')
    } finally {
      setPolyPts([])
      setTool('select')
    }
  }, [selectedImageId, polyPts, nodes])
  // Update overlay rect during canvas panning/zooming
  const updateOverlayRect = useCallback(() => {
    if (!(tool === 'polygon' || tool === 'segment') || !selectedImageId) return
    const el = document.querySelector(`.react-flow__node[data-id="${selectedImageId}"] .image-node-preview`)
    if (el) setOverlayRect(el.getBoundingClientRect())
  }, [tool, selectedImageId])

  // Segment-mode precise edit
  const applySegmentEdit = useCallback(async () => {
    if (!selectedImageId) return
    const isReplace = window.confirm('Replace selected class? OK = Replace, Cancel = Remove')
    let replacement_prompt = null
    const operation = isReplace ? 'replace' : 'remove'
    if (isReplace) {
      const input = window.prompt('Describe the replacement (e.g., "matte white cabinets"):', 'matte white cabinets')
      if (input === null) return
      replacement_prompt = input
    }
    const imageId = selectedImageId.replace('image-', '')
    try {
      const res = await axios.post('/api/v1/design/precise-edit', {
        room_image_id: imageId,
        mode: 'segment',
        segment_class: segmentClass,
        operation,
        replacement_prompt,
      })
      if (res?.data) {
        setLastTransformation(res.data)
        const imgNode = nodes.find((n) => n.id === selectedImageId)
        setOrigImageForGallery(imgNode?.data?.imageUrl || null)
        setShowGallery(true)
      }
    } catch (e) {
      console.error('Segment edit failed', e)
      alert('Segment edit failed')
    } finally {
      setTool('select')
    }
  }, [selectedImageId, segmentClass, nodes])

  // Keyboard + cursor helpers for polygon UX
  useEffect(() => {
    const onKey = (e) => {
      if (tool === 'polygon') {
        if (e.key === 'Enter' && polyPts.length >= 3) {
          e.preventDefault()
          applyPreciseEdit()
        } else if (e.key === 'Escape') {
          e.preventDefault()
          setPolyPts([])
        }
      }
    }
    const onMove = (e) => {
      if (tool !== 'polygon' || !overlayRect || !selectedImageId) return
      const { left, top, width, height } = overlayRect
      const x = (e.clientX - left) / width
      const y = (e.clientY - top) / height
      if (x >= 0 && x <= 1 && y >= 0 && y <= 1) setHoverPt([x, y])
      else setHoverPt(null)
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('mousemove', onMove)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('mousemove', onMove)
    }
  }, [tool, polyPts.length, overlayRect, selectedImageId, applyPreciseEdit])


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
      <Toolbar tool={tool} onToolChange={setTool} onSave={onSave} saving={isSaving} onAutoArrange={onAutoArrange} />

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onSelectionChange={onSelectionChangeHandler}
        onPaneClick={onPaneClick}
        onMove={updateOverlayRect}
        onMoveEnd={updateOverlayRect}
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

      {tool === 'polygon' && overlayRect && selectedImageId && (
        <div
          style={{
            position: 'fixed',
            left: overlayRect.left,
            top: overlayRect.top,
            width: overlayRect.width,
            height: overlayRect.height,
            pointerEvents: 'none',
            zIndex: 50,
          }}
        >
          <svg viewBox="0 0 1 1" preserveAspectRatio="none" width="100%" height="100%">
            {polyPts.length >= 3 && (
              <polygon
                points={polyPts.map(([x, y]) => `${x},${y}`).join(' ')}
                fill="rgba(34,197,94,0.25)"
                stroke="#22c55e"
                strokeWidth={0.005}
              />
            )}
            {polyPts.length >= 2 && (
              <polyline
                points={polyPts.map(([x, y]) => `${x},${y}`).join(' ')}
                fill="none"
                stroke="#22c55e"
                strokeWidth={0.005}
              />
            )}
            {polyPts.length >= 1 && hoverPt && (
              <polyline
                points={`${polyPts[polyPts.length - 1][0]},${polyPts[polyPts.length - 1][1]} ${hoverPt[0]},${hoverPt[1]}`}
                fill="none"
                stroke="#22c55e"
                strokeWidth={0.004}
                strokeDasharray="0.01 0.01"
              />
            )}

            {polyPts.map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r={0.01} fill="#22c55e" />
            ))}
          </svg>
          <div style={{ position: 'absolute', right: 8, bottom: 8, display: 'flex', gap: 8, pointerEvents: 'auto' }}>
            <button className="toolbar-btn" onClick={() => setPolyPts([])}>Reset</button>
            <button className="toolbar-btn" disabled={polyPts.length < 3} onClick={applyPreciseEdit}>Apply edit</button>
          </div>
        </div>
      )}

        {tool === 'segment' && overlayRect && selectedImageId && (
          <div
            style={{
              position: 'fixed',
              left: overlayRect.left,
              top: Math.max(8, overlayRect.top - 52),
              zIndex: 60,
              pointerEvents: 'auto'
            }}
          >
            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: '#374151' }}>Segment class:</span>
              <select value={segmentClass} onChange={(e) => setSegmentClass(e.target.value)} style={{ padding: 4, borderRadius: 4, border: '1px solid #d1d5db' }}>
                {['floor','walls','ceiling','cabinets','countertops','backsplash','appliances','furniture','lighting'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <button className="toolbar-btn" onClick={applySegmentEdit}>Apply edit</button>
            </div>
          </div>
        )}


      </ReactFlow>

      {showGallery && lastTransformation && (
        <VariationGallery
          transformation={lastTransformation}
          originalImage={origImageForGallery}
          onClose={() => setShowGallery(false)}
          enableFavorite={false}
        />
      )}

    </div>
  )
}

export default StudioCanvas

