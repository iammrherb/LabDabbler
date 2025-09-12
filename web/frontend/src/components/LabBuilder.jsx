import { useState, useEffect, useRef, useCallback } from 'react'
import './LabBuilder.css'
import ContainerPalette from './LabBuilder/ContainerPalette'
import TopologyCanvas from './LabBuilder/TopologyCanvas'
import NodeConfigPanel from './LabBuilder/NodeConfigPanel'
import TopologyControls from './LabBuilder/TopologyControls'
import TopologyExporter from './LabBuilder/TopologyExporter'
import LinkConfigPanel from './LabBuilder/LinkConfigPanel'
import LabTemplates from './LabBuilder/LabTemplates'
import EnvironmentSettingsPanel from './LabBuilder/EnvironmentSettingsPanel'
import LabBrowser from './LabBuilder/LabBrowser'
import GitHubIntegration from './GitHubIntegration'
import { getApiBase, api } from '../utils/api'

function LabBuilder() {
  // Topology state
  const [topology, setTopology] = useState({
    name: 'custom-lab',
    nodes: {},
    links: []
  })
  
  // Environment configuration state
  const [environmentConfig, setEnvironmentConfig] = useState({
    mgmt: {
      network: 'mgmt',
      ipv4_subnet: '172.20.20.0/24',
      bridge: 'br-mgmt',
      mtu: 1500,
      external_access: true
    },
    deployment: {
      runtime: 'docker',
      auto_remove: true,
      debug: false
    }
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
  const [showLinkConfig, setShowLinkConfig] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const [showExporter, setShowExporter] = useState(false)
  const [showGitHubExport, setShowGitHubExport] = useState(false)
  const [showEnvironmentSettings, setShowEnvironmentSettings] = useState(false)
  const [showLabBrowser, setShowLabBrowser] = useState(false)
  const [containers, setContainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [validationErrors, setValidationErrors] = useState([])
  
  // Refs
  const canvasRef = useRef(null)

  useEffect(() => {
    loadContainers()
  }, [])

  const loadContainers = async () => {
    try {
      setLoading(true)
      // Load both regular containers and containerlab kinds
      const [containersData, clabKindsData] = await Promise.all([
        api.getWithParams('/api/containers/search', { limit: 1000 }).catch(() => ({ results: [] })),
        api.get('/api/containerlab/kinds').catch(() => ({ kinds: [] }))
      ])
      
      // Combine both data sources
      const regularContainers = containersData.results || []
      const clabContainers = clabKindsData.kinds || []
      
      // Mark containerlab kinds with a special flag
      const enhancedClabContainers = clabContainers.map(container => ({
        ...container,
        image: container.default_image,
        isContainerlabKind: true
      }))
      
      setContainers([...regularContainers, ...enhancedClabContainers])
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
      name: `${endpoint1.node}-${endpoint2.node}`,
      type: 'ethernet',
      endpoints: [
        { 
          node: endpoint1.node, 
          interface: endpoint1.interface || 'eth0',
          ip: '',
          vlan: '',
          mode: 'access'
        },
        { 
          node: endpoint2.node, 
          interface: endpoint2.interface || 'eth0',
          ip: '',
          vlan: '',
          mode: 'access'
        }
      ],
      properties: {
        bandwidth: '',
        mtu: '1500',
        delay: '0ms',
        jitter: '0ms',
        loss: '0%',
        duplex: 'full',
        auto_negotiate: true
      },
      vlan_config: {
        enabled: false,
        native_vlan: '1',
        allowed_vlans: '',
        encapsulation: '802.1q'
      },
      advanced: {
        mac_learning: true,
        stp_enabled: false,
        storm_control: false,
        flow_control: false
      }
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
      setShowLinkConfig(false)
    }
  }, [selectedLink])

  const updateLink = useCallback((linkId, updates) => {
    setTopology(prev => ({
      ...prev,
      links: prev.links.map(link => 
        link.id === linkId ? { ...link, ...updates } : link
      )
    }))
  }, [])

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
      
      const data = await api.post('/api/lab-builder/save', topologyData)
      alert(`Topology "${name}" saved successfully!`)
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

  const loadTemplate = useCallback((topology, templateMeta) => {
    setTopology(topology)
    setSelectedNode(null)
    setSelectedLink(null)
    setLinking(null)
    setShowNodeConfig(false)
    setShowLinkConfig(false)
    setShowTemplates(false)
    console.log(`Loaded lab template: ${templateMeta.name}`)
  }, [])

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
          onLoadTemplate={() => setShowTemplates(true)}
          onBrowseLabs={() => setShowLabBrowser(true)}
          onExport={() => setShowExporter(true)}
          onEnvironmentSettings={() => setShowEnvironmentSettings(true)}
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
            onLinkSelect={(linkId) => {
              setSelectedLink(linkId)
              setShowLinkConfig(true)
            }}
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
        
        {showLinkConfig && selectedLink && (
          <LinkConfigPanel
            link={topology.links.find(l => l.id === selectedLink)}
            nodes={topology.nodes}
            onUpdate={(updates) => updateLink(selectedLink, updates)}
            onClose={() => setShowLinkConfig(false)}
            onDelete={() => {
              removeLink(selectedLink)
              setShowLinkConfig(false)
            }}
          />
        )}
        
        {showTemplates && (
          <LabTemplates
            onLoadTemplate={loadTemplate}
            onClose={() => setShowTemplates(false)}
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
      
      {showEnvironmentSettings && (
        <EnvironmentSettingsPanel
          environmentConfig={environmentConfig}
          onUpdate={setEnvironmentConfig}
          onClose={() => setShowEnvironmentSettings(false)}
        />
      )}
      
      {showLabBrowser && (
        <LabBrowser
          onLoadLab={loadTopology}
          onEditLab={(lab) => {
            loadTopology(lab.topology_data || lab)
            setShowLabBrowser(false)
          }}
          onClose={() => setShowLabBrowser(false)}
        />
      )}
    </div>
  )
}

export default LabBuilder