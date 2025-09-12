import { useState, useEffect } from 'react'
import { api } from '../../utils/api'
import './LabTemplates.css'

function LabTemplates({ onLoadTemplate, onClose }) {
  const [labs, setLabs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLab, setSelectedLab] = useState(null)
  const [loadingLab, setLoadingLab] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadLabCollections()
  }, [])

  const loadLabCollections = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/labs')
      setLabs(response)
    } catch (error) {
      console.error('Error loading lab collections:', error)
      setError('Failed to load lab collections. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const loadSpecificLab = async (labName) => {
    try {
      setLoadingLab(true)
      setError(null)
      const response = await api.get(`/api/labs/${labName}`)
      return response
    } catch (error) {
      console.error('Error loading specific lab:', error)
      setError(`Failed to load lab '${labName}'. Please try again.`)
      return null
    } finally {
      setLoadingLab(false)
    }
  }

  const handleLoadLab = async (lab) => {
    const labData = await loadSpecificLab(lab.name)
    if (labData) {
      // Convert containerlab format to internal topology format
      const topology = convertContainerlabToTopology(labData, lab)
      onLoadTemplate(topology, lab)
      onClose()
    }
  }

  const convertContainerlabToTopology = (labData, labMeta) => {
    const nodes = {}
    const links = []

    // Convert nodes from containerlab format
    if (labData.topology && labData.topology.nodes) {
      Object.entries(labData.topology.nodes).forEach(([nodeName, nodeConfig]) => {
        const nodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        nodes[nodeId] = {
          id: nodeId,
          name: nodeName,
          kind: nodeConfig.kind || 'linux',
          image: nodeConfig.image || '',
          position: {
            x: Math.random() * 800 + 100,
            y: Math.random() * 600 + 100
          },
          // Map containerlab config to internal format
          startup_config: nodeConfig.startup_config || '',
          env: nodeConfig.env || {},
          ports: nodeConfig.ports || [],
          volumes: nodeConfig.volumes || [],
          binds: nodeConfig.binds || [],
          sysctls: nodeConfig.sysctls || {},
          capabilities: nodeConfig.capabilities || [],
          privileged: nodeConfig.privileged || false,
          type: nodeConfig.type || '',
          license: nodeConfig.license || '',
          user: nodeConfig.user || '',
          group: nodeConfig.group || '',
          cpu_limit: nodeConfig.cpu_limit || '',
          memory_limit: nodeConfig.memory_limit || '',
          restart_policy: nodeConfig.restart_policy || 'unless-stopped',
          network_mode: nodeConfig.network_mode || 'bridge',
          extra_hosts: nodeConfig.extra_hosts || []
        }
      })
    }

    // Convert links from containerlab format
    if (labData.topology && labData.topology.links) {
      labData.topology.links.forEach(link => {
        const linkId = `link-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        
        // Parse containerlab link format (node1:interface1 - node2:interface2)
        const [endpoint1, endpoint2] = link.endpoints || []
        if (endpoint1 && endpoint2) {
          const [node1, interface1] = endpoint1.split(':')
          const [node2, interface2] = endpoint2.split(':')
          
          // Find corresponding node IDs
          const node1Id = Object.keys(nodes).find(id => nodes[id].name === node1)
          const node2Id = Object.keys(nodes).find(id => nodes[id].name === node2)
          
          if (node1Id && node2Id) {
            links.push({
              id: linkId,
              name: `${node1}-${node2}`,
              type: link.type || 'ethernet',
              endpoints: [
                { 
                  node: node1Id, 
                  interface: interface1 || 'eth0',
                  ip: '',
                  vlan: '',
                  mode: 'access'
                },
                { 
                  node: node2Id, 
                  interface: interface2 || 'eth0',
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
            })
          }
        }
      })
    }

    return {
      name: labMeta.name,
      description: labMeta.description,
      metadata: {
        author: labData.name || 'Unknown',
        version: '1.0',
        category: labMeta.category || 'general',
        created_at: new Date().toISOString(),
        source: labMeta.source || 'local'
      },
      nodes,
      links
    }
  }

  const getAllLabs = () => {
    return labs.flatMap(category => 
      category.labs.map(lab => ({ ...lab, category: category.category }))
    )
  }

  const getFilteredLabs = () => {
    let allLabs = getAllLabs()
    
    // Filter by category
    if (selectedCategory !== 'all') {
      allLabs = allLabs.filter(lab => lab.category === selectedCategory)
    }
    
    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      allLabs = allLabs.filter(lab => 
        lab.name.toLowerCase().includes(term) ||
        lab.description.toLowerCase().includes(term) ||
        lab.kinds.some(kind => kind.toLowerCase().includes(term))
      )
    }
    
    return allLabs
  }

  const getCategories = () => {
    const categories = labs.map(cat => cat.category)
    return ['all', ...categories]
  }

  const getCategoryDisplayName = (category) => {
    const names = {
      'all': '🌍 All Labs',
      'security': '🔒 Security',
      'networking': '🌐 Networking', 
      'datacenter': '🏢 Data Center',
      'service_provider': '📡 Service Provider',
      'campus': '🏫 Campus',
      'cloud': '☁️ Cloud',
      'automation': '🤖 Automation',
      'testing': '🧪 Testing',
      'training': '📚 Training'
    }
    return names[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const getKindIcon = (kind) => {
    const icons = {
      'srl': '📶',
      'sros': '📶', 
      'ceos': '🔸',
      'linux': '🐧',
      'bridge': '🌉',
      'ovs': '🔀',
      'host': '💻',
      'fortinet_fortigate': '🛡️',
      'vr_vmx': '🌿',
      'vr_csr': '🔷',
      'sonic': '🔊'
    }
    return icons[kind] || '📦'
  }

  const filteredLabs = getFilteredLabs()

  if (loading) {
    return (
      <div className="lab-templates-overlay">
        <div className="lab-templates-panel">
          <div className="templates-header">
            <h2>🧪 Lab Templates</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading lab collections...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="lab-templates-overlay">
      <div className="lab-templates-panel">
        <div className="templates-header">
          <h2>🧪 Lab Templates</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="templates-filters">
          <div className="category-filter">
            <label>Category:</label>
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {getCategories().map(category => (
                <option key={category} value={category}>
                  {getCategoryDisplayName(category)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="search-filter">
            <label>Search:</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search labs by name, description, or device type..."
            />
          </div>
        </div>

        <div className="templates-stats">
          <div className="stats-item">
            <strong>{filteredLabs.length}</strong>
            <span>Lab{filteredLabs.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="stats-item">
            <strong>{getCategories().length - 1}</strong>
            <span>Categories</span>
          </div>
          <div className="stats-item">
            <strong>{getAllLabs().reduce((total, lab) => total + lab.nodes, 0)}</strong>
            <span>Total Nodes</span>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <span>⚠️ {error}</span>
            <button onClick={loadLabCollections}>Retry</button>
          </div>
        )}

        <div className="templates-grid">
          {filteredLabs.length === 0 ? (
            <div className="no-labs">
              <p>🔍 No labs found matching your criteria.</p>
              <p>Try adjusting your search or category filter.</p>
            </div>
          ) : (
            filteredLabs.map((lab, index) => (
              <div 
                key={`${lab.category}-${lab.name}-${index}`}
                className={`lab-card ${selectedLab?.name === lab.name ? 'selected' : ''}`}
                onClick={() => setSelectedLab(lab)}
              >
                <div className="lab-card-header">
                  <h3>{lab.name}</h3>
                  <div className="lab-category">
                    {getCategoryDisplayName(lab.category)}
                  </div>
                </div>
                
                <div className="lab-description">
                  {lab.description}
                </div>
                
                <div className="lab-metadata">
                  <div className="metadata-item">
                    <span className="label">Nodes:</span>
                    <span className="value">{lab.nodes}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="label">Source:</span>
                    <span className="value">{lab.source}</span>
                  </div>
                </div>
                
                <div className="lab-kinds">
                  <span className="kinds-label">Device Types:</span>
                  <div className="kinds-list">
                    {lab.kinds.map(kind => (
                      <span key={kind} className="kind-tag">
                        {getKindIcon(kind)} {kind}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="lab-actions">
                  <button 
                    className="load-lab-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleLoadLab(lab)
                    }}
                    disabled={loadingLab}
                  >
                    {loadingLab ? 'Loading...' : '📂 Load Lab'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {selectedLab && (
          <div className="selected-lab-details">
            <div className="details-header">
              <h3>📋 Lab Details: {selectedLab.name}</h3>
            </div>
            <div className="details-content">
              <div className="detail-row">
                <strong>Description:</strong> {selectedLab.description}
              </div>
              <div className="detail-row">
                <strong>Category:</strong> {getCategoryDisplayName(selectedLab.category)}
              </div>
              <div className="detail-row">
                <strong>Node Count:</strong> {selectedLab.nodes}
              </div>
              <div className="detail-row">
                <strong>File Path:</strong> <code>{selectedLab.file_path}</code>
              </div>
              <div className="detail-row">
                <strong>Device Types:</strong>
                <div className="kinds-detail">
                  {selectedLab.kinds.map(kind => (
                    <span key={kind} className="kind-tag">
                      {getKindIcon(kind)} {kind}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="details-actions">
              <button 
                className="load-selected-btn"
                onClick={() => handleLoadLab(selectedLab)}
                disabled={loadingLab}
              >
                {loadingLab ? '⏳ Loading Lab...' : '🚀 Load This Lab'}
              </button>
            </div>
          </div>
        )}

        <div className="templates-footer">
          <div className="footer-info">
            <small>💡 Select a lab template to view details and load it into the editor</small>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LabTemplates