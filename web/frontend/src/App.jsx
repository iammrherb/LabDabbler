import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [labs, setLabs] = useState([])
  const [containers, setContainers] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      // Note: Using localhost for backend API calls in development
      const [labsRes, containersRes] = await Promise.all([
        fetch('http://localhost:8000/api/labs?include_github=true'),
        fetch('http://localhost:8000/api/containers')
      ])
      
      const labsData = await labsRes.json()
      const containersData = await containersRes.json()
      
      setLabs(labsData)
      setContainers(containersData)
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshContainers = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/containers/refresh', {
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
      const response = await fetch('http://localhost:8000/api/labs/scan', {
        method: 'POST'
      })
      const data = await response.json()
      // Refresh labs after scanning
      const labsRes = await fetch('http://localhost:8000/api/labs?include_github=true')
      const labsData = await labsRes.json()
      setLabs(labsData)
    } catch (error) {
      console.error('Error scanning GitHub labs:', error)
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
      </header>

      <main className="container">
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
                      {lab.nodes && <p className="lab-meta">Nodes: {lab.nodes}</p>}
                      {lab.kinds && lab.kinds.length > 0 && (
                        <p className="lab-meta">Kinds: {lab.kinds.join(', ')}</p>
                      )}
                      <button className="btn-primary">Launch Lab</button>
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

        <section className="lab-builder">
          <h2>Custom Lab Builder</h2>
          <div className="builder-placeholder">
            <p>🏗️ Drag-and-drop lab builder coming soon...</p>
            <button className="btn-primary">Create Custom Lab</button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App