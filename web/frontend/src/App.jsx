import { useState, useEffect } from 'react'
import './App.css'
import VRNetLabManager from './components/VRNetLabManager'
import ContainerCatalog from './components/ContainerCatalog'
import RepositoryManager from './components/RepositoryManager'
import LabBuilder from './components/LabBuilder'
import ErrorBoundary from './components/ErrorBoundary'
import './components/ErrorBoundary.css'

function App() {
  const [labs, setLabs] = useState([])
  const [containers, setContainers] = useState({})
  const [activeLabs, setActiveLabs] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentView, setCurrentView] = useState('dashboard')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      // API base - determine correct endpoint for Replit environment
      const apiBase = window.location.hostname.includes('replit.dev') 
        ? `${window.location.protocol}//${window.location.hostname.replace('-00-', '-8000-')}`
        : 'http://localhost:8000'
      const [labsRes, containersRes, activeLabsRes] = await Promise.all([
        fetch(`${apiBase}/api/labs?include_github=true&include_repositories=true`),
        fetch(`${apiBase}/api/containers`),
        fetch(`${apiBase}/api/labs/active`)
      ])
      
      const labsData = await labsRes.json()
      const containersData = await containersRes.json()
      const activeLabsData = await activeLabsRes.json()
      
      setLabs(labsData)
      setContainers(containersData)
      setActiveLabs(activeLabsData.active_labs || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshContainers = async () => {
    setLoading(true)
    try {
      const apiBase = window.location.hostname.includes('replit.dev') 
        ? `${window.location.protocol}//${window.location.hostname.replace('-00-', '-8000-')}`
        : 'http://localhost:8000'
      const response = await fetch(`${apiBase}/api/containers/refresh`, {
        method: 'POST'
      })
      const data = await response.json()
      setContainers(data.containers)
    } catch (error) {
      console.error('Error refreshing containers:', error)
    } finally {
      setLoading(false)
    }
  }

  const scanGitHubLabs = async () => {
    setLoading(true)
    try {
      const apiBase = window.location.hostname.includes('replit.dev') 
        ? `${window.location.protocol}//${window.location.hostname.replace('-00-', '-8000-')}`
        : 'http://localhost:8000'
      const response = await fetch(`${apiBase}/api/labs/scan`, {
        method: 'POST'
      })
      const data = await response.json()
      // Refresh labs after scanning
      const labsRes = await fetch(`${apiBase}/api/labs?include_github=true`)
      const labsData = await labsRes.json()
      setLabs(labsData)
    } catch (error) {
      console.error('Error scanning GitHub labs:', error)
    } finally {
      setLoading(false)
    }
  }

  const launchLab = async (lab) => {
    setLoading(true)
    try {
      // Use the file_path from the lab object
      const labFilePath = lab.file_path || lab.path // fallback to path for backward compatibility
      
      if (!labFilePath) {
        alert('No lab file path provided')
        return
      }
      
      const apiBase = window.location.hostname.includes('replit.dev') 
        ? `${window.location.protocol}//${window.location.hostname.replace('-00-', '-8000-')}`
        : 'http://localhost:8000'
      const response = await fetch(`${apiBase}/api/labs/launch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ lab_file_path: labFilePath })
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(`Lab "${data.lab_name}" launched successfully!`)
        // Refresh active labs
        const activeLabsRes = await fetch(`${apiBase}/api/labs/active`)
        const activeLabsData = await activeLabsRes.json()
        setActiveLabs(activeLabsData.active_labs || [])
      } else {
        const error = await response.json()
        alert(`Failed to launch lab: ${error.detail?.message || error.message || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error launching lab:', error)
      alert('Error launching lab. Please check if containerlab is installed.')
    } finally {
      setLoading(false)
    }
  }

  const stopLab = async (labId) => {
    setLoading(true)
    try {
      const apiBase = window.location.hostname.includes('replit.dev') 
        ? `${window.location.protocol}//${window.location.hostname.replace('-00-', '-8000-')}`
        : 'http://localhost:8000'
      const response = await fetch(`${apiBase}/api/labs/${labId}/stop`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(data.message)
        // Refresh active labs
        const activeLabsRes = await fetch(`${apiBase}/api/labs/active`)
        const activeLabsData = await activeLabsRes.json()
        setActiveLabs(activeLabsData.active_labs || [])
      } else {
        const error = await response.json()
        alert(`Failed to stop lab: ${error.detail?.message || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error stopping lab:', error)
      alert('Error stopping lab')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading LabDabbler...</div>
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>🧪 LabDabbler</h1>
        <p>Master Lab Repository - Launch any lab, anywhere</p>
        
        <nav className="main-navigation">
          <button 
            className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={`nav-btn ${currentView === 'repositories' ? 'active' : ''}`}
            onClick={() => setCurrentView('repositories')}
          >
            🗂️ Repositories
          </button>
          <button 
            className={`nav-btn ${currentView === 'catalog' ? 'active' : ''}`}
            onClick={() => setCurrentView('catalog')}
          >
            📦 Container Catalog
          </button>
          <button 
            className={`nav-btn ${currentView === 'vrnetlab' ? 'active' : ''}`}
            onClick={() => setCurrentView('vrnetlab')}
          >
            🏗️ VRNetlab
          </button>
          <button 
            className={`nav-btn ${currentView === 'builder' ? 'active' : ''}`}
            onClick={() => setCurrentView('builder')}
          >
            🎨 Lab Builder
          </button>
        </nav>
      </header>

      <main className="container">
        {currentView === 'catalog' ? (
          <ContainerCatalog />
        ) : currentView === 'repositories' ? (
          <RepositoryManager />
        ) : currentView === 'vrnetlab' ? (
          <VRNetLabManager />
        ) : currentView === 'builder' ? (
          <LabBuilder />
        ) : (
          <>
        <section className="labs-section">
          <div className="section-header">
            <h2>Available Labs</h2>
            <button className="btn-secondary" onClick={scanGitHubLabs} disabled={loading}>
              {loading ? 'Scanning...' : 'Scan GitHub Labs'}
            </button>
          </div>
          {labs.length > 0 ? (
            labs.map((category, idx) => (
              <div key={idx} className="lab-category">
                <h3>
                  {category.category}
                  {category.source && (
                    <span className={`source-badge ${category.source}`}>
                      {category.source}
                    </span>
                  )}
                  {category.repository && (
                    <span className="repo-info">
                      from {category.repository}
                    </span>
                  )}
                </h3>
                <div className="lab-grid">
                  {category.labs.map((lab, labIdx) => (
                    <div key={labIdx} className="lab-card">
                      <h4>{lab.name}</h4>
                      <p>{lab.description}</p>
                      {lab.file_path && <p className="lab-meta">File: {lab.file_path}</p>}
                      {lab.nodes && <p className="lab-meta">Nodes: {lab.nodes}</p>}
                      {lab.kinds && lab.kinds.length > 0 && (
                        <p className="lab-meta">Kinds: {lab.kinds.join(', ')}</p>
                      )}
                      <button 
                        className="btn-primary" 
                        onClick={() => launchLab(lab)}
                        disabled={loading}
                      >
                        {loading ? 'Launching...' : 'Launch Lab'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p>No labs found. Click "Scan GitHub Labs" to discover labs or create your first lab below!</p>
          )}
        </section>

        <section className="containers-section">
          <div className="section-header">
            <h2>Available Containers</h2>
            <button className="btn-secondary" onClick={refreshContainers} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh Containers'}
            </button>
          </div>
          {Object.keys(containers).length > 0 ? (
            Object.entries(containers).filter(([key]) => key !== 'last_updated').map(([category, containerList]) => (
              <div key={category} className="container-category">
                <h3>{category.replace('_', ' ').toUpperCase()}</h3>
                <div className="container-grid">
                  {Array.isArray(containerList) && containerList.map((container, idx) => (
                    <div key={idx} className="container-card">
                      <h4>{container.name}</h4>
                      <p className="image-name">{container.image}</p>
                      <p>{container.description}</p>
                      {container.vendor && <p className="container-meta">Vendor: {container.vendor}</p>}
                      {container.kind && <p className="container-meta">Kind: {container.kind}</p>}
                      {container.pull_count && <p className="container-meta">Pulls: {container.pull_count.toLocaleString()}</p>}
                      <button className="btn-secondary">Add to Lab</button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p>No containers loaded. Click "Refresh Containers" to discover available containers!</p>
          )}
        </section>

        <section className="active-labs-section">
          <h2>Active Labs</h2>
          {activeLabs.length > 0 ? (
            <div className="active-labs-grid">
              {activeLabs.map((lab, idx) => (
                <div key={idx} className="active-lab-card">
                  <h4>{lab.name}</h4>
                  <p className="lab-id">ID: {lab.lab_id}</p>
                  <p className="lab-meta">Nodes: {lab.node_count || 0}</p>
                  <p className={`status ${lab.status}`}>Status: {lab.status}</p>
                  {lab.original_file && <p className="lab-meta">File: {lab.original_file}</p>}
                  {lab.created_at && (
                    <p className="lab-meta">
                      Created: {new Date(parseFloat(lab.created_at) * 1000).toLocaleString()}
                    </p>
                  )}
                  <button 
                    className="btn-danger" 
                    onClick={() => stopLab(lab.lab_id)}
                    disabled={loading}
                  >
                    {loading ? 'Stopping...' : 'Stop Lab'}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p>No active labs. Launch a lab from the available labs above!</p>
          )}
        </section>

        <section className="lab-builder">
          <h2>Custom Lab Builder</h2>
          <div className="builder-placeholder">
            <p>🏗️ Drag-and-drop lab builder coming soon...</p>
            <button className="btn-primary">Create Custom Lab</button>
          </div>
        </section>
          </>
        )}
      </main>
    </div>
  )
}

export default App