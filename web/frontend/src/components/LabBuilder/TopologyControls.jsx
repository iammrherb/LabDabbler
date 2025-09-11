import { useState } from 'react'
import './TopologyControls.css'

function TopologyControls({ 
  topology, 
  onClear, 
  onSave, 
  onLoad, 
  onExport, 
  onValidate, 
  validationErrors 
}) {
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [showLoadDialog, setShowLoadDialog] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [savedTopologies, setSavedTopologies] = useState([])
  const [loading, setLoading] = useState(false)

  const apiBase = window.location.protocol + '//' + window.location.hostname + ':8000'

  const handleSave = async () => {
    if (!saveName.trim()) {
      alert('Please enter a name for the topology')
      return
    }
    
    try {
      setLoading(true)
      await onSave(saveName)
      setShowSaveDialog(false)
      setSaveName('')
      loadSavedTopologies() // Refresh the list
    } catch (error) {
      console.error('Error saving topology:', error)
      alert('Failed to save topology')
    } finally {
      setLoading(false)
    }
  }

  const handleLoad = async (topologyData) => {
    try {
      setLoading(true)
      await onLoad(topologyData)
      setShowLoadDialog(false)
    } catch (error) {
      console.error('Error loading topology:', error)
      alert('Failed to load topology')
    } finally {
      setLoading(false)
    }
  }

  const loadSavedTopologies = async () => {
    try {
      const response = await fetch(`${apiBase}/api/lab-builder/saved`)
      if (response.ok) {
        const data = await response.json()
        setSavedTopologies(data.topologies || [])
      }
    } catch (error) {
      console.error('Error loading saved topologies:', error)
    }
  }

  const deleteSavedTopology = async (topologyId) => {
    if (!confirm('Are you sure you want to delete this topology?')) return
    
    try {
      const response = await fetch(`${apiBase}/api/lab-builder/saved/${topologyId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        loadSavedTopologies() // Refresh the list
      } else {
        alert('Failed to delete topology')
      }
    } catch (error) {
      console.error('Error deleting topology:', error)
      alert('Failed to delete topology')
    }
  }

  const exportToFile = () => {
    const exportData = {
      ...topology,
      exported_at: new Date().toISOString(),
      export_version: '1.0'
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${topology.name || 'topology'}-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const importFromFile = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json,.clab.yml,.yaml,.yml'
    
    input.onchange = (e) => {
      const file = e.target.files[0]
      if (!file) return
      
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          let data
          
          if (file.name.endsWith('.json')) {
            data = JSON.parse(e.target.result)
          } else {
            // Handle YAML files (would need yaml parser)
            alert('YAML import not yet implemented. Please export as JSON first.')
            return
          }
          
          handleLoad(data)
        } catch (error) {
          console.error('Error parsing file:', error)
          alert('Failed to parse topology file')
        }
      }
      
      reader.readAsText(file)
    }
    
    input.click()
  }

  const getTopologyStats = () => {
    const nodeCount = Object.keys(topology.nodes).length
    const linkCount = topology.links.length
    const kinds = [...new Set(Object.values(topology.nodes).map(node => node.kind))]
    
    return { nodeCount, linkCount, kinds }
  }

  const stats = getTopologyStats()

  return (
    <div className="topology-controls">
      <div className="control-group">
        <div className="topology-info">
          <h4>{topology.name}</h4>
          <div className="stats">
            <span className="stat">
              <span className="stat-icon">🖥️</span>
              {stats.nodeCount} nodes
            </span>
            <span className="stat">
              <span className="stat-icon">🔗</span>
              {stats.linkCount} links
            </span>
            <span className="stat">
              <span className="stat-icon">📦</span>
              {stats.kinds.length} types
            </span>
          </div>
        </div>
      </div>

      <div className="control-group">
        <button 
          className="control-btn primary"
          onClick={onValidate}
          title="Validate topology"
        >
          ✅ Validate
        </button>
        
        <button 
          className="control-btn secondary"
          onClick={() => setShowSaveDialog(true)}
          title="Save topology to workspace"
          disabled={stats.nodeCount === 0}
        >
          💾 Save
        </button>
        
        <button 
          className="control-btn secondary"
          onClick={() => {
            loadSavedTopologies()
            setShowLoadDialog(true)
          }}
          title="Load saved topology"
        >
          📁 Load
        </button>
      </div>

      <div className="control-group">
        <button 
          className="control-btn secondary"
          onClick={onExport}
          title="Export to .clab.yml"
          disabled={stats.nodeCount === 0}
        >
          📤 Export
        </button>
        
        <button 
          className="control-btn secondary"
          onClick={exportToFile}
          title="Export as JSON file"
          disabled={stats.nodeCount === 0}
        >
          💾 JSON
        </button>
        
        <button 
          className="control-btn secondary"
          onClick={importFromFile}
          title="Import topology file"
        >
          📥 Import
        </button>
      </div>

      <div className="control-group">
        <button 
          className="control-btn danger"
          onClick={() => {
            if (confirm('Are you sure you want to clear the entire topology?')) {
              onClear()
            }
          }}
          title="Clear all nodes and links"
          disabled={stats.nodeCount === 0}
        >
          🗑️ Clear
        </button>
      </div>

      {validationErrors.length > 0 && (
        <div className="validation-summary">
          <span className="validation-icon">⚠️</span>
          <span className="validation-count">{validationErrors.length} issues</span>
        </div>
      )}

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>💾 Save Topology</h3>
              <button 
                className="close-btn"
                onClick={() => setShowSaveDialog(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Topology Name</label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="Enter a descriptive name..."
                  autoFocus
                />
              </div>
              <div className="topology-preview">
                <p><strong>Preview:</strong></p>
                <ul>
                  <li>{stats.nodeCount} nodes</li>
                  <li>{stats.linkCount} links</li>
                  <li>Types: {stats.kinds.join(', ')}</li>
                </ul>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowSaveDialog(false)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={handleSave}
                disabled={!saveName.trim() || loading}
              >
                {loading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Dialog */}
      {showLoadDialog && (
        <div className="modal-overlay">
          <div className="modal large">
            <div className="modal-header">
              <h3>📁 Load Topology</h3>
              <button 
                className="close-btn"
                onClick={() => setShowLoadDialog(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              {savedTopologies.length === 0 ? (
                <div className="empty-state">
                  <p>No saved topologies found.</p>
                  <p>Create and save a topology to see it here.</p>
                </div>
              ) : (
                <div className="topology-list">
                  {savedTopologies.map((savedTopology) => {
                    const savedStats = {
                      nodeCount: Object.keys(savedTopology.nodes || {}).length,
                      linkCount: (savedTopology.links || []).length,
                      kinds: [...new Set(Object.values(savedTopology.nodes || {}).map(node => node.kind))]
                    }
                    
                    return (
                      <div key={savedTopology.id} className="topology-item">
                        <div className="topology-details">
                          <h4>{savedTopology.name}</h4>
                          <div className="topology-meta">
                            <span>{savedStats.nodeCount} nodes</span>
                            <span>{savedStats.linkCount} links</span>
                            <span>Types: {savedStats.kinds.join(', ')}</span>
                          </div>
                          <div className="topology-date">
                            Saved: {new Date(savedTopology.saved_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="topology-actions">
                          <button 
                            className="btn-primary small"
                            onClick={() => handleLoad(savedTopology)}
                            disabled={loading}
                          >
                            Load
                          </button>
                          <button 
                            className="btn-danger small"
                            onClick={() => deleteSavedTopology(savedTopology.id)}
                            disabled={loading}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowLoadDialog(false)}
                disabled={loading}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TopologyControls