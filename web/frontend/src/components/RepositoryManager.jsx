import { useState, useEffect } from 'react'
import './RepositoryManager.css'

function RepositoryManager() {
  const [repositories, setRepositories] = useState([])
  const [syncStatus, setSyncStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [showAddRepo, setShowAddRepo] = useState(false)
  const [newRepo, setNewRepo] = useState({
    name: '',
    url: '',
    branch: 'main',
    category: 'custom',
    description: '',
    auto_sync: false
  })

  let apiBase = 'http://localhost:8000'
  if (window.location.hostname.includes('replit.dev')) {
    const hostname = window.location.hostname
    const replitBase = hostname.split('.')[0]
    const replitDomain = hostname.split('.').slice(1).join('.')
    apiBase = `${window.location.protocol}//${replitBase.replace(/(-\d+-|-00-)/, '-8000-')}.${replitDomain}`
  }

  useEffect(() => {
    fetchRepositories()
    fetchSyncStatus()
  }, [])

  const fetchRepositories = async () => {
    try {
      const response = await fetch(`${apiBase}/api/repositories`)
      const data = await response.json()
      if (data.success) {
        setRepositories(data.repositories)
      }
    } catch (error) {
      console.error('Error fetching repositories:', error)
    }
  }

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch(`${apiBase}/api/repositories/sync-status`)
      const data = await response.json()
      if (data.success) {
        setSyncStatus(data.sync_status)
      }
    } catch (error) {
      console.error('Error fetching sync status:', error)
    }
  }

  const initializeRepositories = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/repositories/initialize`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.success) {
        alert('Repositories initialized successfully!')
        await fetchRepositories()
        await fetchSyncStatus()
      } else {
        alert(`Failed to initialize repositories: ${data.error}`)
      }
    } catch (error) {
      console.error('Error initializing repositories:', error)
      alert('Error initializing repositories')
    } finally {
      setLoading(false)
    }
  }

  const syncRepository = async (repoName) => {
    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/repositories/${repoName}/sync`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.success) {
        alert(`Repository "${repoName}" synced successfully!`)
        await fetchRepositories()
        await fetchSyncStatus()
      } else {
        alert(`Failed to sync repository: ${data.error}`)
      }
    } catch (error) {
      console.error('Error syncing repository:', error)
      alert('Error syncing repository')
    } finally {
      setLoading(false)
    }
  }

  const syncAllRepositories = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/repositories/sync-all`, {
        method: 'POST'
      })
      const data = await response.json()
      alert(data.message)
      await fetchRepositories()
      await fetchSyncStatus()
    } catch (error) {
      console.error('Error syncing all repositories:', error)
      alert('Error syncing all repositories')
    } finally {
      setLoading(false)
    }
  }

  const addRepository = async () => {
    if (!newRepo.name || !newRepo.url) {
      alert('Name and URL are required')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/repositories/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newRepo)
      })
      const data = await response.json()
      if (data.success) {
        alert(`Repository "${newRepo.name}" added successfully!`)
        setShowAddRepo(false)
        setNewRepo({
          name: '',
          url: '',
          branch: 'main',
          category: 'custom',
          description: '',
          auto_sync: false
        })
        await fetchRepositories()
        await fetchSyncStatus()
      } else {
        alert(`Failed to add repository: ${data.error}`)
      }
    } catch (error) {
      console.error('Error adding repository:', error)
      alert('Error adding repository')
    } finally {
      setLoading(false)
    }
  }

  const removeRepository = async (repoName) => {
    if (!confirm(`Are you sure you want to remove repository "${repoName}"?`)) {
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/repositories/${repoName}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.success) {
        alert(`Repository "${repoName}" removed successfully!`)
        await fetchRepositories()
        await fetchSyncStatus()
      } else {
        alert(`Failed to remove repository: ${data.error}`)
      }
    } catch (error) {
      console.error('Error removing repository:', error)
      alert('Error removing repository')
    } finally {
      setLoading(false)
    }
  }

  const getRepositoryStatus = async (repoName) => {
    try {
      const response = await fetch(`${apiBase}/api/repositories/${repoName}/status`)
      const data = await response.json()
      if (data.success) {
        setSelectedRepo(data.status)
      } else {
        alert(`Failed to get repository status: ${data.error}`)
      }
    } catch (error) {
      console.error('Error getting repository status:', error)
      alert('Error getting repository status')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  const getCategoryColor = (category) => {
    const colors = {
      'official': '#4CAF50',
      'community': '#2196F3',
      'educational': '#FF9800',
      'demo': '#9C27B0',
      'custom': '#607D8B'
    }
    return colors[category] || '#757575'
  }

  if (loading && repositories.length === 0) {
    return (
      <div className="repository-manager">
        <div className="loading">
          Loading Repository Manager...
        </div>
      </div>
    )
  }

  return (
    <div className="repository-manager">
      <div className="repository-header">
        <h2>🗂️ Repository Management</h2>
        <p>Centralized management of containerlab repository collections</p>
        
        <div className="repository-actions">
          <button 
            className="btn-primary" 
            onClick={initializeRepositories}
            disabled={loading}
          >
            {loading ? 'Initializing...' : 'Initialize Repositories'}
          </button>
          <button 
            className="btn-secondary" 
            onClick={syncAllRepositories}
            disabled={loading}
          >
            {loading ? 'Syncing...' : 'Sync All'}
          </button>
          <button 
            className="btn-secondary" 
            onClick={() => setShowAddRepo(true)}
          >
            Add Repository
          </button>
        </div>
      </div>

      {repositories.length === 0 && !loading && (
        <div className="empty-state">
          <h3>No repositories configured</h3>
          <p>Click "Initialize Repositories" to set up default containerlab repositories</p>
        </div>
      )}

      {repositories.length > 0 && (
        <div className="repositories-grid">
          {repositories.map((repo) => {
            const sync = syncStatus[repo.name] || {}
            return (
              <div key={repo.name} className="repository-card">
                <div className="repository-header-card">
                  <h3>{repo.name}</h3>
                  <span 
                    className="category-badge" 
                    style={{ backgroundColor: getCategoryColor(repo.category) }}
                  >
                    {repo.category}
                  </span>
                </div>
                
                <p className="repository-description">{repo.description}</p>
                <p className="repository-url">{repo.url}</p>
                
                <div className="repository-status">
                  <div className={`status-indicator ${repo.exists ? 'exists' : 'missing'}`}>
                    {repo.exists ? '✅ Cloned' : '❌ Not Cloned'}
                  </div>
                  {repo.auto_sync && (
                    <div className="auto-sync-indicator">🔄 Auto-sync enabled</div>
                  )}
                </div>

                {sync.last_sync && (
                  <div className="sync-info">
                    <small>Last sync: {formatDate(sync.last_sync)}</small>
                    <small>{sync.success ? '✅ Success' : '❌ Failed'}</small>
                  </div>
                )}

                {repo.metadata && repo.metadata.lab_count > 0 && (
                  <div className="lab-count">
                    📄 {repo.metadata.lab_count} labs found
                  </div>
                )}

                <div className="repository-actions-card">
                  <button 
                    className="btn-small btn-primary" 
                    onClick={() => syncRepository(repo.name)}
                    disabled={loading}
                  >
                    Sync
                  </button>
                  <button 
                    className="btn-small btn-secondary" 
                    onClick={() => getRepositoryStatus(repo.name)}
                  >
                    Details
                  </button>
                  {repo.category === 'custom' && (
                    <button 
                      className="btn-small btn-danger" 
                      onClick={() => removeRepository(repo.name)}
                      disabled={loading}
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Add Repository Modal */}
      {showAddRepo && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Add New Repository</h3>
            <form onSubmit={(e) => { e.preventDefault(); addRepository(); }}>
              <div className="form-group">
                <label>Repository Name *</label>
                <input
                  type="text"
                  value={newRepo.name}
                  onChange={(e) => setNewRepo({...newRepo, name: e.target.value})}
                  placeholder="e.g., my-custom-labs"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Repository URL *</label>
                <input
                  type="url"
                  value={newRepo.url}
                  onChange={(e) => setNewRepo({...newRepo, url: e.target.value})}
                  placeholder="https://github.com/user/repo.git"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Branch</label>
                <input
                  type="text"
                  value={newRepo.branch}
                  onChange={(e) => setNewRepo({...newRepo, branch: e.target.value})}
                  placeholder="main"
                />
              </div>
              
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newRepo.category}
                  onChange={(e) => setNewRepo({...newRepo, category: e.target.value})}
                >
                  <option value="custom">Custom</option>
                  <option value="community">Community</option>
                  <option value="educational">Educational</option>
                  <option value="demo">Demo</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newRepo.description}
                  onChange={(e) => setNewRepo({...newRepo, description: e.target.value})}
                  placeholder="Description of this repository..."
                  rows="3"
                />
              </div>
              
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newRepo.auto_sync}
                    onChange={(e) => setNewRepo({...newRepo, auto_sync: e.target.checked})}
                  />
                  Enable auto-sync
                </label>
              </div>
              
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowAddRepo(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Adding...' : 'Add Repository'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Repository Details Modal */}
      {selectedRepo && (
        <div className="modal-overlay">
          <div className="modal modal-large">
            <h3>Repository Details: {selectedRepo.name}</h3>
            
            <div className="repository-details">
              <div className="detail-section">
                <h4>Basic Information</h4>
                <p><strong>URL:</strong> {selectedRepo.config.url}</p>
                <p><strong>Branch:</strong> {selectedRepo.config.branch}</p>
                <p><strong>Category:</strong> {selectedRepo.config.category}</p>
                <p><strong>Exists:</strong> {selectedRepo.exists ? 'Yes' : 'No'}</p>
                {selectedRepo.path && (
                  <p><strong>Local Path:</strong> <code>{selectedRepo.path}</code></p>
                )}
              </div>

              {selectedRepo.current_branch && (
                <div className="detail-section">
                  <h4>Git Information</h4>
                  <p><strong>Current Branch:</strong> {selectedRepo.current_branch}</p>
                  {selectedRepo.last_commit && (
                    <div className="commit-info">
                      <p><strong>Last Commit:</strong></p>
                      <ul>
                        <li><strong>Hash:</strong> <code>{selectedRepo.last_commit.hash.substring(0, 8)}</code></li>
                        <li><strong>Author:</strong> {selectedRepo.last_commit.author}</li>
                        <li><strong>Date:</strong> {selectedRepo.last_commit.date}</li>
                        <li><strong>Message:</strong> {selectedRepo.last_commit.message}</li>
                      </ul>
                    </div>
                  )}
                  <p><strong>Up to Date:</strong> {selectedRepo.up_to_date ? 'Yes' : 'No'}</p>
                  {selectedRepo.needs_pull && (
                    <p className="warning">⚠️ Repository needs to be pulled</p>
                  )}
                </div>
              )}

              {selectedRepo.labs && selectedRepo.labs.length > 0 && (
                <div className="detail-section">
                  <h4>Labs Found ({selectedRepo.lab_count})</h4>
                  <div className="labs-list">
                    {selectedRepo.labs.map((lab, index) => (
                      <div key={index} className="lab-item">
                        <h5>{lab.name}</h5>
                        <p>{lab.description}</p>
                        <small>
                          {lab.nodes} nodes • 
                          Kinds: {lab.kinds.join(', ')} • 
                          Path: {lab.relative_path}
                        </small>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="modal-actions">
              <button 
                className="btn-primary" 
                onClick={() => syncRepository(selectedRepo.name)}
                disabled={loading}
              >
                Sync Repository
              </button>
              <button className="btn-secondary" onClick={() => setSelectedRepo(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RepositoryManager