import { forwardRef, useRef, useEffect, useState, useCallback } from 'react'
import './TopologyCanvas.css'

const TopologyCanvas = forwardRef(({
  topology,
  selectedNode,
  selectedLink,
  onNodeSelect,
  onLinkSelect,
  onNodeMove,
  onNodeDelete,
  onLinkDelete,
  onLinkCreate,
  dragging,
  setDragging,
  linking,
  setLinking,
  canvasOffset,
  setCanvasOffset,
  zoomLevel,
  setZoomLevel
}, ref) => {
  const canvasRef = useRef(null)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [contextMenu, setContextMenu] = useState(null)
  const [linkPreview, setLinkPreview] = useState(null)
  const [dropZone, setDropZone] = useState(null)

  // Set the forwarded ref
  useEffect(() => {
    if (ref) {
      ref.current = canvasRef.current
    }
  }, [ref])

  const getCanvasCoordinates = useCallback((clientX, clientY) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    
    const rect = canvas.getBoundingClientRect()
    return {
      x: (clientX - rect.left - canvasOffset.x) / zoomLevel,
      y: (clientY - rect.top - canvasOffset.y) / zoomLevel
    }
  }, [canvasOffset, zoomLevel])

  const getScreenCoordinates = useCallback((canvasX, canvasY) => {
    return {
      x: canvasX * zoomLevel + canvasOffset.x,
      y: canvasY * zoomLevel + canvasOffset.y
    }
  }, [canvasOffset, zoomLevel])

  // Handle container drops from palette
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    try {
      const containerData = JSON.parse(e.dataTransfer.getData('application/json'))
      const coords = getCanvasCoordinates(e.clientX, e.clientY)
      
      // Add the container to the topology
      const nodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      const newNode = {
        id: nodeId,
        name: containerData.name.toLowerCase().replace(/[^a-z0-9]/g, '-').substring(0, 20),
        kind: containerData.kind || 'linux',
        image: containerData.image,
        position: coords,
        config: {
          startup_config: '',
          env: {},
          ports: [],
          volumes: []
        },
        ...containerData
      }
      
      // Call parent's onContainerDrag method (simulated)
      if (window.labBuilderAddNode) {
        window.labBuilderAddNode(newNode, coords)
      }
    } catch (error) {
      console.error('Error handling container drop:', error)
    }
    setDropZone(null)
  }, [getCanvasCoordinates])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    const coords = getCanvasCoordinates(e.clientX, e.clientY)
    setDropZone(coords)
  }, [getCanvasCoordinates])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setDropZone(null)
  }, [])

  // Node interaction handlers
  const handleNodeMouseDown = useCallback((e, nodeId) => {
    e.stopPropagation()
    
    if (e.button === 0) { // Left click
      if (e.shiftKey) {
        // Shift+click to start linking
        setLinking({ sourceNode: nodeId, sourceInterface: 'eth0' })
      } else {
        // Regular click to select/drag
        onNodeSelect(nodeId)
        setDragging({ nodeId, startX: e.clientX, startY: e.clientY })
      }
    } else if (e.button === 2) { // Right click
      e.preventDefault()
      setContextMenu({
        type: 'node',
        nodeId,
        x: e.clientX,
        y: e.clientY
      })
    }
  }, [onNodeSelect, setDragging, setLinking])

  const handleNodeMouseUp = useCallback((e, nodeId) => {
    e.stopPropagation()
    
    if (linking && linking.sourceNode !== nodeId) {
      // Complete link creation
      const endpoint1 = { node: linking.sourceNode, interface: linking.sourceInterface }
      const endpoint2 = { node: nodeId, interface: 'eth0' }
      onLinkCreate(endpoint1, endpoint2)
      setLinking(null)
    }
  }, [linking, onLinkCreate, setLinking])

  // Canvas interaction handlers
  const handleCanvasMouseDown = useCallback((e) => {
    if (e.button === 0 && !e.target.closest('.node')) {
      // Start panning
      setIsPanning(true)
      setPanStart({ x: e.clientX - canvasOffset.x, y: e.clientY - canvasOffset.y })
      onNodeSelect(null) // Deselect nodes
      setContextMenu(null)
    }
  }, [canvasOffset, onNodeSelect])

  const handleCanvasMouseMove = useCallback((e) => {
    if (isPanning) {
      setCanvasOffset({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y
      })
    } else if (dragging) {
      const deltaX = e.clientX - dragging.startX
      const deltaY = e.clientY - dragging.startY
      const node = topology.nodes[dragging.nodeId]
      
      if (node) {
        const newPosition = {
          x: node.position.x + deltaX / zoomLevel,
          y: node.position.y + deltaY / zoomLevel
        }
        onNodeMove(dragging.nodeId, newPosition)
        setDragging({
          ...dragging,
          startX: e.clientX,
          startY: e.clientY
        })
      }
    } else if (linking) {
      const coords = getCanvasCoordinates(e.clientX, e.clientY)
      setLinkPreview(coords)
    }
  }, [isPanning, panStart, dragging, linking, topology.nodes, onNodeMove, setDragging, setCanvasOffset, zoomLevel, getCanvasCoordinates])

  const handleCanvasMouseUp = useCallback(() => {
    setIsPanning(false)
    setDragging(null)
    if (linking && !linkPreview) {
      setLinking(null) // Cancel linking if not over a node
    }
    setLinkPreview(null)
  }, [linking, linkPreview, setDragging, setLinking])

  const handleCanvasWheel = useCallback((e) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    const newZoom = Math.max(0.1, Math.min(3, zoomLevel * delta))
    
    // Zoom towards cursor position
    const rect = canvasRef.current.getBoundingClientRect()
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    const offsetX = (e.clientX - rect.left - centerX) * (1 - delta)
    const offsetY = (e.clientY - rect.top - centerY) * (1 - delta)
    
    setZoomLevel(newZoom)
    setCanvasOffset({
      x: canvasOffset.x + offsetX,
      y: canvasOffset.y + offsetY
    })
  }, [zoomLevel, canvasOffset, setZoomLevel, setCanvasOffset])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Delete' && selectedNode) {
      onNodeDelete(selectedNode)
    } else if (e.key === 'Escape') {
      setLinking(null)
      setContextMenu(null)
      onNodeSelect(null)
    }
  }, [selectedNode, onNodeDelete, onNodeSelect, setLinking])

  // Context menu handlers
  const handleContextMenuAction = useCallback((action, nodeId) => {
    switch (action) {
      case 'delete':
        onNodeDelete(nodeId)
        break
      case 'duplicate':
        const node = topology.nodes[nodeId]
        if (node) {
          const newNode = {
            ...node,
            id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            name: `${node.name}-copy`,
            position: {
              x: node.position.x + 50,
              y: node.position.y + 50
            }
          }
          if (window.labBuilderAddNode) {
            window.labBuilderAddNode(newNode, newNode.position)
          }
        }
        break
      case 'configure':
        onNodeSelect(nodeId)
        break
    }
    setContextMenu(null)
  }, [topology.nodes, onNodeDelete, onNodeSelect])

  // Event listeners
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.addEventListener('wheel', handleCanvasWheel, { passive: false })
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousemove', handleCanvasMouseMove)
    document.addEventListener('mouseup', handleCanvasMouseUp)

    return () => {
      canvas.removeEventListener('wheel', handleCanvasWheel)
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousemove', handleCanvasMouseMove)
      document.removeEventListener('mouseup', handleCanvasMouseUp)
    }
  }, [handleCanvasWheel, handleKeyDown, handleCanvasMouseMove, handleCanvasMouseUp])

  const getNodeIcon = (kind) => {
    const icons = {
      'nokia_srlinux': '🔧',
      'arista_ceos': '⚙️',
      'cisco': '🔗',
      'juniper': '🌿',
      'linux': '🐧',
      'bridge': '🌉',
      'ovs': '🔀'
    }
    return icons[kind] || '📦'
  }

  const getNodeColor = (kind, vendor) => {
    const vendorColors = {
      'nokia': '#124191',
      'arista': '#f05a28',
      'cisco': '#1ba0d7',
      'juniper': '#84bd00',
      'portnox': '#6c5ce7'
    }
    
    const kindColors = {
      'nokia_srlinux': '#124191',
      'arista_ceos': '#f05a28',
      'cisco': '#1ba0d7',
      'juniper': '#84bd00',
      'linux': '#2ecc71',
      'bridge': '#95a5a6',
      'ovs': '#9b59b6'
    }
    
    return vendorColors[(vendor || '').toLowerCase()] || kindColors[kind] || '#34495e'
  }

  const renderLink = (link) => {
    const node1 = topology.nodes[link.endpoints[0].node]
    const node2 = topology.nodes[link.endpoints[1].node]
    
    if (!node1 || !node2) return null
    
    const pos1 = getScreenCoordinates(node1.position.x, node1.position.y)
    const pos2 = getScreenCoordinates(node2.position.x, node2.position.y)
    
    const isSelected = selectedLink === link.id
    
    return (
      <line
        key={link.id}
        x1={pos1.x}
        y1={pos1.y}
        x2={pos2.x}
        y2={pos2.y}
        stroke={isSelected ? '#007bff' : '#666'}
        strokeWidth={isSelected ? 3 : 2}
        onClick={(e) => {
          e.stopPropagation()
          onLinkSelect(link.id)
        }}
        onContextMenu={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setContextMenu({
            type: 'link',
            linkId: link.id,
            x: e.clientX,
            y: e.clientY
          })
        }}
        className="link"
      />
    )
  }

  const renderNode = (node) => {
    const screenPos = getScreenCoordinates(node.position.x, node.position.y)
    const isSelected = selectedNode === node.id
    const isLinkSource = linking && linking.sourceNode === node.id
    const nodeColor = getNodeColor(node.kind, node.vendor)
    
    return (
      <g key={node.id} className="node-group">
        {/* Node background */}
        <circle
          cx={screenPos.x}
          cy={screenPos.y}
          r={25 * zoomLevel}
          fill={isSelected ? '#007bff' : nodeColor}
          stroke={isLinkSource ? '#28a745' : (isSelected ? '#0056b3' : '#333')}
          strokeWidth={isLinkSource ? 3 : (isSelected ? 3 : 1)}
          className="node-circle"
          onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
          onMouseUp={(e) => handleNodeMouseUp(e, node.id)}
        />
        
        {/* Node icon */}
        <text
          x={screenPos.x}
          y={screenPos.y + 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={12 * zoomLevel}
          fill="white"
          pointerEvents="none"
        >
          {getNodeIcon(node.kind)}
        </text>
        
        {/* Node label */}
        <text
          x={screenPos.x}
          y={screenPos.y + 40 * zoomLevel}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={10 * zoomLevel}
          fill="#333"
          className="node-label"
          pointerEvents="none"
        >
          {node.name}
        </text>
        
        {/* Node type label */}
        <text
          x={screenPos.x}
          y={screenPos.y + 52 * zoomLevel}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={8 * zoomLevel}
          fill="#666"
          className="node-type"
          pointerEvents="none"
        >
          {node.kind}
        </text>
      </g>
    )
  }

  return (
    <div className="topology-canvas">
      <div
        ref={canvasRef}
        className="canvas"
        onMouseDown={handleCanvasMouseDown}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{ cursor: isPanning ? 'grabbing' : linking ? 'crosshair' : 'default' }}
      >
        <svg
          width="100%"
          height="100%"
          className="canvas-svg"
        >
          {/* Grid pattern */}
          <defs>
            <pattern
              id="grid"
              width={20 * zoomLevel}
              height={20 * zoomLevel}
              patternUnits="userSpaceOnUse"
            >
              <path
                d={`M ${20 * zoomLevel} 0 L 0 0 0 ${20 * zoomLevel}`}
                fill="none"
                stroke="#e1e1e1"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Links */}
          {topology.links.map(renderLink)}
          
          {/* Link preview while linking */}
          {linking && linkPreview && (
            <line
              x1={getScreenCoordinates(topology.nodes[linking.sourceNode].position.x, topology.nodes[linking.sourceNode].position.y).x}
              y1={getScreenCoordinates(topology.nodes[linking.sourceNode].position.x, topology.nodes[linking.sourceNode].position.y).y}
              x2={getScreenCoordinates(linkPreview.x, linkPreview.y).x}
              y2={getScreenCoordinates(linkPreview.x, linkPreview.y).y}
              stroke="#28a745"
              strokeWidth="2"
              strokeDasharray="5,5"
              className="link-preview"
            />
          )}
          
          {/* Nodes */}
          {Object.values(topology.nodes).map(renderNode)}
          
          {/* Drop zone indicator */}
          {dropZone && (
            <circle
              cx={getScreenCoordinates(dropZone.x, dropZone.y).x}
              cy={getScreenCoordinates(dropZone.x, dropZone.y).y}
              r={30 * zoomLevel}
              fill="rgba(40, 167, 69, 0.2)"
              stroke="#28a745"
              strokeWidth="2"
              strokeDasharray="5,5"
              className="drop-zone"
            />
          )}
        </svg>
        
        {/* Canvas info overlay */}
        <div className="canvas-info">
          <div className="zoom-info">Zoom: {Math.round(zoomLevel * 100)}%</div>
          <div className="position-info">
            Offset: ({Math.round(canvasOffset.x)}, {Math.round(canvasOffset.y)})
          </div>
          <div className="node-count">
            Nodes: {Object.keys(topology.nodes).length} | Links: {topology.links.length}
          </div>
        </div>
        
        {/* Instructions */}
        {Object.keys(topology.nodes).length === 0 && (
          <div className="canvas-instructions">
            <h3>Welcome to the Visual Lab Builder!</h3>
            <ul>
              <li>🎯 Drag containers from the palette to add nodes</li>
              <li>🔗 Shift+click a node, then click another to create links</li>
              <li>⚙️ Click a node to configure its properties</li>
              <li>🖱️ Right-click for context menu options</li>
              <li>🔍 Use mouse wheel to zoom, drag to pan</li>
              <li>⌨️ Press Delete to remove selected items</li>
            </ul>
          </div>
        )}
        
        {linking && (
          <div className="linking-instruction">
            <p>🔗 Click on a target node to create a link, or press Escape to cancel</p>
          </div>
        )}
      </div>
      
      {/* Context menu */}
      {contextMenu && (
        <div
          className="context-menu"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onMouseLeave={() => setContextMenu(null)}
        >
          {contextMenu.type === 'node' && (
            <>
              <button onClick={() => handleContextMenuAction('configure', contextMenu.nodeId)}>
                ⚙️ Configure
              </button>
              <button onClick={() => handleContextMenuAction('duplicate', contextMenu.nodeId)}>
                📋 Duplicate
              </button>
              <button 
                onClick={() => handleContextMenuAction('delete', contextMenu.nodeId)}
                className="danger"
              >
                🗑️ Delete
              </button>
            </>
          )}
          {contextMenu.type === 'link' && (
            <button 
              onClick={() => {
                onLinkDelete(contextMenu.linkId)
                setContextMenu(null)
              }}
              className="danger"
            >
              🗑️ Delete Link
            </button>
          )}
        </div>
      )}
    </div>
  )
})

TopologyCanvas.displayName = 'TopologyCanvas'

export default TopologyCanvas