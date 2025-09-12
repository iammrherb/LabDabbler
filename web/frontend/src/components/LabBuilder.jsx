import { useState, useEffect, useRef, useCallback } from 'react'
import './LabBuilder.css'
import ContainerPalette from './LabBuilder/ContainerPalette'
import TopologyCanvas from './LabBuilder/TopologyCanvas'
import NodeConfigPanel from './LabBuilder/NodeConfigPanel'
import TopologyControls from './LabBuilder/TopologyControls'
import TopologyExporter from './LabBuilder/TopologyExporter'
import GitHubIntegration from './GitHubIntegration'

function LabBuilder() {
  // Topology state
  const [topology, setTopology] = useState({
    name: 'custom-lab',
    nodes: {},
    links: []
  })
  
  // Canvas and interaction state
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedLink, setSelectedLink] = useState(null)
  const [dragging, setDragging] = useState(null)
  const [linking, setLinking] = useState(null)
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 })
  const [zoomLevel, setZoomLevel] = useState(1)
  
  // UI state
  const [showNodeConfig, setShowNodeConfig] = useState(false)
  const [showExporter, setShowExporter] = useState(false)
  const [showGitHubExport, setShowGitHubExport] = useState(false)
  const [containers, setContainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [validationErrors, setValidationErrors] = useState([])
  
  // Refs
  const canvasRef = useRef(null)
  const getApiBase = () => {
    const domain = import.meta.env.VITE_REPLIT_DOMAINS || window.location.hostname
    return window.location.hostname.includes('replit.dev') 
      ? `${window.location.protocol}//${domain.replace('-00-', '-8000-')}`
      : `${window.location.protocol}//${window.location.hostname}:8000`
  }
  const apiBase = getApiBase()

  useEffect(() => {
    loadContainers()
  }, [])

  const loadContainers = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${apiBase}/api/containers/search?limit=1000`)
      const data = await response.json()
      setContainers(data.results || [])
    } catch (error) {
      console.error('Error loading containers:', error)
    } finally {
      setLoading(false)
    }
  }

  const addNode = useCallback((containerInfo, position) => {
    const nodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newNode = {
      id: nodeId,
      name: containerInfo.name.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      kind: containerInfo.kind || 'linux',
      image: containerInfo.image,
      position: position,
      config: {
        startup_config: '',
        env: {},
        ports: [],
        volumes: []
      },
      ...containerInfo
    }
    
    setTopology(prev => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: newNode
      }
    }))
    
    return nodeId
  }, [])

  // Set up global callbacks for TopologyCanvas to use
  useEffect(() => {
    window.labBuilderAddNode = addNode
    return () => {
      delete window.labBuilderAddNode
    }
  }, [addNode])

  const updateNode = useCallback((nodeId, updates) => {
    setTopology(prev => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: {
          ...prev.nodes[nodeId],
          ...updates
        }
      }
    }))
  }, [])

  const removeNode = useCallback((nodeId) => {
    setTopology(prev => {
      const newNodes = { ...prev.nodes }
      delete newNodes[nodeId]
      
      // Remove all links connected to this node
      const newLinks = prev.links.filter(link => 
        link.endpoints[0].node !== nodeId && 
        link.endpoints[1].node !== nodeId
      )
      
      return {
        ...prev,
        nodes: newNodes,
        links: newLinks
      }
    })
    
    if (selectedNode === nodeId) {
      setSelectedNode(null)
      setShowNodeConfig(false)
    }
  }, [selectedNode])

  const addLink = useCallback((endpoint1, endpoint2) => {
    const linkId = `link-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newLink = {
      id: linkId,
      endpoints: [endpoint1, endpoint2]
    }
    
    setTopology(prev => ({
      ...prev,
      links: [...prev.links, newLink]
    }))
    
    return linkId
  }, [])

  const removeLink = useCallback((linkId) => {
    setTopology(prev => ({
      ...prev,
      links: prev.links.filter(link => link.id !== linkId)
    }))
    
    if (selectedLink === linkId) {
      setSelectedLink(null)
    }
  }, [selectedLink])

  const validateTopology = useCallback(() => {
    const errors = []
    
    // Check for duplicate node names
    const nodeNames = Object.values(topology.nodes).map(node => node.name)
    const duplicateNames = nodeNames.filter((name, index) => nodeNames.indexOf(name) !== index)
    if (duplicateNames.length > 0) {
      errors.push(`Duplicate node names found: ${[...new Set(duplicateNames)].join(', ')}`)
    }
    
    // Check for nodes without connections (optional warning)
    const connectedNodes = new Set()
    topology.links.forEach(link => {
      connectedNodes.add(link.endpoints[0].node)
      connectedNodes.add(link.endpoints[1].node)
    })
    
    const isolatedNodes = Object.keys(topology.nodes).filter(nodeId => !connectedNodes.has(nodeId))
    if (isolatedNodes.length > 0) {
      errors.push(`Isolated nodes (no connections): ${isolatedNodes.map(id => topology.nodes[id].name).join(', ')}`)
    }
    
    // Check for invalid node configurations
    Object.entries(topology.nodes).forEach(([nodeId, node]) => {
      if (!node.name || node.name.trim() === '') {
        errors.push(`Node ${nodeId} has no name`)
      }
      if (!node.image || node.image.trim() === '') {
        errors.push(`Node ${node.name} has no container image specified`)
      }
    })
    
    setValidationErrors(errors)
    return errors.length === 0
  }, [topology])

  const clearTopology = () => {
    setTopology({
      name: 'custom-lab',
      nodes: {},
      links: []
    })
    setSelectedNode(null)
    setSelectedLink(null)
    setShowNodeConfig(false)
    setValidationErrors([])
  }

  const saveTopology = async (name) => {
    try {
      const topologyData = {
        ...topology,
        name: name,
        saved_at: new Date().toISOString()
      }
      
      const response = await fetch(`${apiBase}/api/lab-builder/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(topologyData)
      })
      
      if (response.ok) {
        alert(`Topology "${name}" saved successfully!`)
      } else {
        const error = await response.json()
        alert(`Failed to save topology: ${error.message}`)
      }
    } catch (error) {
      console.error('Error saving topology:', error)
      alert('Error saving topology')
    }
  }

  const loadTopology = async (topologyData) => {
    try {
      setTopology(topologyData)
      setSelectedNode(null)
      setSelectedLink(null)
      setShowNodeConfig(false)
      setValidationErrors([])
      
      // Reset canvas position
      setCanvasOffset({ x: 0, y: 0 })
      setZoomLevel(1)
    } catch (error) {
      console.error('Error loading topology:', error)
      alert('Error loading topology')
    }
  }

  if (loading) {
    return (
      <div className="lab-builder-loading">
        <div className="loading-spinner"></div>
        <p>Loading Lab Builder...</p>
      </div>
    )
  }

  return (
    <div className="lab-builder">
      <div className="lab-builder-header">
        <h1>🏗️ Visual Lab Builder</h1>
        <p>Drag and drop containers to build custom network topologies</p>
        
        <TopologyControls
          topology={topology}
          onClear={clearTopology}
          onSave={saveTopology}
          onLoad={loadTopology}
          onExport={() => setShowExporter(true)}
          onValidate={validateTopology}
          validationErrors={validationErrors}
        />
      </div>
      
      <div className="lab-builder-workspace">
        <ContainerPalette
          containers={containers}
          onContainerDrag={(container, position) => addNode(container, position)}
        />
        
        <div className="canvas-container">
          <TopologyCanvas
            ref={canvasRef}
            topology={topology}
            selectedNode={selectedNode}
            selectedLink={selectedLink}
            onNodeSelect={(nodeId) => {
              setSelectedNode(nodeId)
              setShowNodeConfig(true)
            }}
            onLinkSelect={setSelectedLink}
            onNodeMove={(nodeId, position) => updateNode(nodeId, { position })}
            onNodeDelete={removeNode}
            onLinkDelete={removeLink}
            onLinkCreate={addLink}
            dragging={dragging}
            setDragging={setDragging}
            linking={linking}
            setLinking={setLinking}
            canvasOffset={canvasOffset}
            setCanvasOffset={setCanvasOffset}
            zoomLevel={zoomLevel}
            setZoomLevel={setZoomLevel}
          />
          
          {validationErrors.length > 0 && (
            <div className="validation-overlay">
              <div className="validation-errors">
                <h4>⚠️ Validation Issues</h4>
                <ul>
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
        
        {showNodeConfig && selectedNode && (
          <NodeConfigPanel
            node={topology.nodes[selectedNode]}
            onUpdate={(updates) => updateNode(selectedNode, updates)}
            onClose={() => setShowNodeConfig(false)}
          />
        )}
      </div>
      
      {showExporter && (
        <TopologyExporter
          topology={topology}
          onClose={() => setShowExporter(false)}
          onExport={saveTopology}
          onGitHubExport={() => {
            setShowExporter(false)
            setShowGitHubExport(true)
          }}
        />
      )}
      
      {showGitHubExport && (
        <GitHubIntegration
          topology={topology}
          onClose={() => setShowGitHubExport(false)}
        />
      )}
    </div>
  )
}

export default LabBuilder