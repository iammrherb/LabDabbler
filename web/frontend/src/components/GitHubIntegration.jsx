import { useState, useEffect } from 'react'
import './GitHubIntegration.css'
import { getApiBase, api } from '../utils/api'

function GitHubIntegration({ topology, onClose }) {
  const [repositories, setRepositories] = useState([])
  const [selectedRepo, setSelectedRepo] = useState('')
  const [loading, setLoading] = useState(false)
  const [exportStatus, setExportStatus] = useState('')
  const [newRepoName, setNewRepoName] = useState('')
  const [createNew, setCreateNew] = useState(false)


  useEffect(() => {
    fetchUserRepositories()
  }, [])

  const fetchUserRepositories = async () => {
    try {
      setLoading(true)
      const data = await api.get('/api/github/repositories')
      setRepositories(data.repositories || [])
    } catch (error) {
      console.error('Error fetching repositories:', error)
      setExportStatus('Error connecting to GitHub API')
    } finally {
      setLoading(false)
    }
  }

  const handleExportToCodespaces = async () => {
    if (!selectedRepo && !newRepoName) {
      setExportStatus('Please select a repository or enter a new repository name')
      return
    }

    try {
      setLoading(true)
      setExportStatus('Exporting lab to GitHub Codespaces...')
      
      const [repoOwner, repoName] = createNew 
        ? [repositories[0]?.owner?.login || 'user', newRepoName]
        : selectedRepo.split('/')

      const data = await api.post('/api/github/export-to-codespaces', {
        topology: topology,
        repo_owner: repoOwner,
        repo_name: repoName
      })
      
      setExportStatus(
        <div>
          <p>✅ Lab exported successfully!</p>
          <p><strong>Repository:</strong> <a href={data.repository_url} target="_blank" rel="noopener noreferrer">{data.repository_url}</a></p>
          <p><strong>Open in Codespaces:</strong> <a href={data.codespaces_url} target="_blank" rel="noopener noreferrer">Launch Codespace</a></p>
          <p><strong>Files created:</strong> {data.files_created.join(', ')}</p>
        </div>
      )
    } catch (error) {
      console.error('Error exporting to Codespaces:', error)
      setExportStatus('Failed to export lab to GitHub Codespaces')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="github-integration-overlay">
      <div className="github-integration-modal">
        <div className="modal-header">
          <h2>🚀 Export to GitHub Codespaces</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-content">
          <div className="lab-info">
            <h3>Lab: {topology?.name || 'Unnamed Lab'}</h3>
            <p>Nodes: {Object.keys(topology?.nodes || {}).length}</p>
            <p>Links: {topology?.links?.length || 0}</p>
          </div>

          <div className="export-options">
            <div className="option-group">
              <label>
                <input
                  type="radio"
                  name="repo-option"
                  checked={!createNew}
                  onChange={() => setCreateNew(false)}
                />
                Use existing repository
              </label>
              
              {!createNew && (
                <select 
                  value={selectedRepo} 
                  onChange={(e) => setSelectedRepo(e.target.value)}
                  disabled={loading}
                >
                  <option value="">Select a repository...</option>
                  {repositories.map(repo => (
                    <option key={repo.id} value={repo.full_name}>
                      {repo.full_name} {repo.private ? '(Private)' : '(Public)'}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="option-group">
              <label>
                <input
                  type="radio"
                  name="repo-option" 
                  checked={createNew}
                  onChange={() => setCreateNew(true)}
                />
                Create new repository
              </label>
              
              {createNew && (
                <input
                  type="text"
                  placeholder="Enter new repository name"
                  value={newRepoName}
                  onChange={(e) => setNewRepoName(e.target.value)}
                  disabled={loading}
                />
              )}
            </div>
          </div>

          <div className="export-info">
            <h4>What will be included:</h4>
            <ul>
              <li>✅ Containerlab topology file ({topology?.name || 'lab'}.clab.yml)</li>
              <li>✅ GitHub Codespaces devcontainer configuration</li>
              <li>✅ Pre-installed containerlab, netlab, and LabDabbler tools</li>
              <li>✅ VS Code extensions for YAML, Docker, and networking</li>
              <li>✅ GitHub Actions workflow for lab validation</li>
              <li>✅ Complete README with setup instructions</li>
            </ul>
          </div>

          {exportStatus && (
            <div className={`export-status ${exportStatus.includes('✅') ? 'success' : exportStatus.includes('❌') || exportStatus.includes('Failed') ? 'error' : 'info'}`}>
              {exportStatus}
            </div>
          )}

          <div className="modal-actions">
            <button 
              className="btn-secondary" 
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button 
              className="btn-primary" 
              onClick={handleExportToCodespaces}
              disabled={loading || (!selectedRepo && !newRepoName)}
            >
              {loading ? 'Exporting...' : 'Export to Codespaces'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GitHubIntegration