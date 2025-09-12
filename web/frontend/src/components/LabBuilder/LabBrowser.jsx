import { useState, useEffect } from 'react'
import './LabBrowser.css'
import { api } from '../../utils/api'

function LabBrowser({ onLoadLab, onClose, onEditLab }) {
  const [labs, setLabs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [sortBy, setSortBy] = useState('name')
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'

  useEffect(() => {
    loadLabs()
  }, [])

  const loadLabs = async () => {
    try {
      setLoading(true)
      
      // Load labs from multiple sources
      const [localLabs, repoLabs, savedTopologies] = await Promise.all([
        api.get('/api/labs').catch(() => ({ labs: [] })),
        api.get('/api/repositories/labs').catch(() => ({ labs: [] })),
        api.get('/api/lab-builder/saved').catch(() => ({ topologies: [] }))
      ])
      
      // Combine and normalize lab data
      const allLabs = [
        // Local labs
        ...(localLabs.labs || []).map(lab => ({
          ...lab,
          source: 'local',
          type: 'lab',
          editable: true
        })),
        
        // Repository labs
        ...(repoLabs.labs || []).map(lab => ({
          ...lab,
          source: 'repository',
          type: 'lab',
          editable: false,
          repository: lab.repository
        })),
        
        // Saved topologies from Lab Builder
        ...(savedTopologies.topologies || []).map(topology => ({
          id: topology.id,
          name: topology.name,
          description: `Lab Builder topology with ${Object.keys(topology.nodes || {}).length} nodes`,
          category: 'lab-builder',
          source: 'lab-builder',
          type: 'topology',
          editable: true,
          saved_at: topology.saved_at,
          metadata: {
            node_count: Object.keys(topology.nodes || {}).length,
            link_count: (topology.links || []).length,
            kinds: [...new Set(Object.values(topology.nodes || {}).map(node => node.kind))]
          },
          topology_data: topology
        }))
      ]
      
      setLabs(allLabs)
    } catch (error) {
      console.error('Error loading labs:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredLabs = labs.filter(lab => {
    // Filter by category
    if (selectedCategory !== 'all' && lab.category !== selectedCategory) {
      return false
    }
    
    // Filter by source
    if (filter !== 'all' && lab.source !== filter) {
      return false
    }
    
    // Search filter
    if (searchTerm && !lab.name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    
    return true
  })

  const sortedLabs = filteredLabs.sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'category':
        return (a.category || '').localeCompare(b.category || '')
      case 'source':
        return a.source.localeCompare(b.source)
      case 'date':
        const dateA = new Date(a.saved_at || a.last_modified || 0)
        const dateB = new Date(b.saved_at || b.last_modified || 0)
        return dateB - dateA
      default:
        return 0
    }
  })

  const categories = [...new Set(labs.map(lab => lab.category).filter(Boolean))]
  const sources = [...new Set(labs.map(lab => lab.source))]

  const handleLoadLab = async (lab) => {
    try {
      if (lab.type === 'topology') {
        // Load Lab Builder topology directly
        onLoadLab(lab.topology_data)
      } else {
        // Load containerlab file
        const response = await api.get(`/api/labs/${lab.id}/content`)
        onLoadLab(response.topology)
      }
      onClose()
    } catch (error) {
      console.error('Error loading lab:', error)
      alert('Failed to load lab')
    }
  }

  const handleEditLab = (lab) => {
    if (onEditLab) {
      onEditLab(lab)
    } else {
      handleLoadLab(lab) // Fallback to loading
    }
  }

  const deleteLab = async (lab) => {
    if (!confirm(`Are you sure you want to delete "${lab.name}"?`)) return
    
    try {
      if (lab.type === 'topology') {
        await api.delete(`/api/lab-builder/saved/${lab.id}`)
      } else {
        await api.delete(`/api/labs/${lab.id}`)
      }
      
      await loadLabs() // Refresh list
    } catch (error) {
      console.error('Error deleting lab:', error)
      alert('Failed to delete lab')
    }
  }

  const getLabIcon = (lab) => {
    switch (lab.source) {
      case 'local': return '🏠'
      case 'repository': return '📚'
      case 'lab-builder': return '🏗️'
      default: return '📄'
    }
  }

  const getLabBadgeColor = (source) => {
    switch (source) {
      case 'local': return '#28a745'
      case 'repository': return '#007bff'
      case 'lab-builder': return '#fd7e14'
      default: return '#6c757d'
    }
  }

  if (loading) {
    return (
      <div className="lab-browser-overlay">
        <div className="lab-browser-modal">
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading labs...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="lab-browser-overlay">
      <div className="lab-browser-modal">
        <div className="browser-header">
          <h3>📚 Browse & Load Labs</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="browser-filters">
          <div className="filter-row">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search labs..."
              className="search-input"
            />
            
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
            
            <select 
              value={filter} 
              onChange={(e) => setFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Sources</option>
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
            
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="filter-select"
            >
              <option value="name">Sort by Name</option>
              <option value="category">Sort by Category</option>
              <option value="source">Sort by Source</option>
              <option value="date">Sort by Date</option>
            </select>
          </div>
          
          <div className="view-controls">
            <button 
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
            >
              ⚏ Grid
            </button>
            <button 
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
            >
              ☰ List
            </button>
          </div>
        </div>
        
        <div className="browser-content">
          {sortedLabs.length === 0 ? (
            <div className="empty-state">
              <p>No labs found matching your criteria.</p>
              <p>Try adjusting your filters or search terms.</p>
            </div>
          ) : (
            <div className={`labs-container ${viewMode}`}>
              {sortedLabs.map((lab) => (
                <div key={`${lab.source}-${lab.id}`} className="lab-card">
                  <div className="lab-card-header">
                    <div className="lab-icon">{getLabIcon(lab)}</div>
                    <div className="lab-title">
                      <h4>{lab.name}</h4>
                      <div 
                        className="lab-badge" 
                        style={{ backgroundColor: getLabBadgeColor(lab.source) }}
                      >
                        {lab.source}
                      </div>
                    </div>
                  </div>
                  
                  <div className="lab-description">
                    <p>{lab.description || 'No description available'}</p>
                  </div>
                  
                  <div className="lab-metadata">
                    {lab.category && (
                      <span className="metadata-item">
                        📂 {lab.category}
                      </span>
                    )}
                    
                    {lab.metadata && (
                      <>
                        {lab.metadata.node_count !== undefined && (
                          <span className="metadata-item">
                            🖥️ {lab.metadata.node_count} nodes
                          </span>
                        )}
                        {lab.metadata.link_count !== undefined && (
                          <span className="metadata-item">
                            🔗 {lab.metadata.link_count} links
                          </span>
                        )}
                        {lab.metadata.kinds && lab.metadata.kinds.length > 0 && (
                          <span className="metadata-item">
                            📦 {lab.metadata.kinds.join(', ')}
                          </span>
                        )}
                      </>
                    )}
                    
                    {lab.repository && (
                      <span className="metadata-item">
                        📚 {lab.repository}
                      </span>
                    )}
                    
                    {(lab.saved_at || lab.last_modified) && (
                      <span className="metadata-item">
                        📅 {new Date(lab.saved_at || lab.last_modified).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  
                  <div className="lab-actions">
                    <button 
                      className="btn-primary small"
                      onClick={() => handleLoadLab(lab)}
                    >
                      📁 Load
                    </button>
                    
                    {lab.editable && (
                      <button 
                        className="btn-secondary small"
                        onClick={() => handleEditLab(lab)}
                      >
                        ✏️ Edit
                      </button>
                    )}
                    
                    <button 
                      className="btn-info small"
                      onClick={() => window.open(lab.documentation || '#', '_blank')}
                      disabled={!lab.documentation}
                    >
                      📖 Docs
                    </button>
                    
                    {lab.editable && (
                      <button 
                        className="btn-danger small"
                        onClick={() => deleteLab(lab)}
                      >
                        🗑️ Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="browser-footer">
          <div className="results-count">
            Showing {sortedLabs.length} of {labs.length} labs
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default LabBrowser