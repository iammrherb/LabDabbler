import { useState, useEffect } from 'react'
import './App.css'
import ContainerCatalog from './components/ContainerCatalog'
import LabBuilder from './components/LabBuilder'
import CodespacesDeployment from './components/CodespacesDeployment'
import ErrorBoundary from './components/ErrorBoundary'
import './components/ErrorBoundary.css'
import { getApiBase, api } from './utils/api'

function App() {
  const [labs, setLabs] = useState([])
  const [containers, setContainers] = useState({})
  const [activeLabs, setActiveLabs] = useState([])
  const [loading, setLoading] = useState(true)
  const [currentView, setCurrentView] = useState('labs')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [labsData, containersData, activeLabsData] = await Promise.all([
        api.getWithParams('/api/labs', { include_github: true, include_repositories: true }),
        api.get('/api/containers'),
        api.get('/api/labs/active')
      ])
      
      setLabs(labsData)
      setContainers(containersData)
      setActiveLabs(activeLabsData.active_labs || [])
    } catch (error) {
      console.error('Error fetching data:', error)
      // Fallback sample data for when API is not available
      setLabs([
        {
          category: "Network Basics",
          source: "sample",
          labs: [
            {
              name: "Simple 2-Node Lab",
              description: "Basic two-router connectivity lab for learning network fundamentals",
              file_path: "labs/network/basic/simple-2node.clab.yml",
              nodes: 2,
              kinds: ["ceos"]
            },
            {
              name: "Spine-Leaf Fabric",
              description: "Classic spine-leaf data center fabric with hosts",
              file_path: "labs/network/basic/spine-leaf.clab.yml", 
              nodes: 5,
              kinds: ["ceos", "linux"]
            }
          ]
        },
        {
          category: "Security Labs",
          source: "sample", 
          labs: [
            {
              name: "TACACS+ Authentication",
              description: "Network device authentication using TACACS+ server",
              file_path: "labs/security/tacacs/tacacs-lab.clab.yml",
              nodes: 3,
              kinds: ["ceos", "linux"]
            }
          ]
        }
      ])
      setContainers({
        networking: [
          {
            name: "Arista cEOS",
            image: "ceos:4.27.0F",
            description: "Arista Networks container EOS for data center switching",
            vendor: "Arista",
            kind: "ceos",
            pull_count: 50000
          },
          {
            name: "Cisco IOL",
            image: "cisco/iol:15.6", 
            description: "Cisco IOS on Linux virtualization platform",
            vendor: "Cisco",
            kind: "cisco_iol",
            pull_count: 25000
          }
        ],
        hosts: [
          {
            name: "Alpine Linux",
            image: "alpine:latest",
            description: "Lightweight Linux distribution, perfect for network testing",
            vendor: "Alpine",
            kind: "linux",
            pull_count: 1000000
          }
        ]
      })
      setActiveLabs([])
    } finally {
      setLoading(false)
    }
  }

  const refreshContainers = async () => {
    setLoading(true)
    try {
      const data = await api.post('/api/containers/refresh', {})
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
      await api.post('/api/labs/scan', {})
      // Refresh labs after scanning
      const labsData = await api.getWithParams('/api/labs', { include_github: true })
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
      
      const data = await api.post('/api/labs/launch', { lab_file_path: labFilePath })
      alert(`Lab "${data.lab_name}" launched successfully!`)
      
      // Refresh active labs
      const activeLabsData = await api.get('/api/labs/active')
      setActiveLabs(activeLabsData.active_labs || [])
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
      const data = await api.post(`/api/labs/${labId}/stop`, {})
      alert(data.message)
      
      // Refresh active labs
      const activeLabsData = await api.get('/api/labs/active')
      setActiveLabs(activeLabsData.active_labs || [])
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
            className={`nav-btn ${currentView === 'labs' ? 'active' : ''}`}
            onClick={() => setCurrentView('labs')}
          >
            🧪 Labs
          </button>
          <button 
            className={`nav-btn ${currentView === 'builder' ? 'active' : ''}`}
            onClick={() => setCurrentView('builder')}
          >
            🎨 Lab Builder
          </button>
          <button 
            className={`nav-btn ${currentView === 'catalog' ? 'active' : ''}`}
            onClick={() => setCurrentView('catalog')}
          >
            📦 Containers
          </button>
          <button 
            className={`nav-btn deploy-btn ${currentView === 'deploy' ? 'active' : ''}`}
            onClick={() => setCurrentView('deploy')}
          >
            🚀 Deploy to Cloud
          </button>
        </nav>
      </header>

      <main className="container">
        {currentView === 'catalog' ? (
          <ContainerCatalog />
        ) : currentView === 'builder' ? (
          <LabBuilder />
        ) : currentView === 'deploy' ? (
          <CodespacesDeployment labData={labs} />
        ) : (
          <>
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <h2>🚀 Get Started with Network Labs</h2>
            <p>Launch existing labs or build your own custom network topologies</p>
            <div className="hero-actions">
              <button 
                className="btn-hero-primary" 
                onClick={() => setCurrentView('builder')}
              >
                🎨 Build New Lab
              </button>
              <button 
                className="btn-hero-secondary" 
                onClick={scanGitHubLabs} 
                disabled={loading}
              >
                {loading ? 'Importing...' : '📚 Import Labs from GitHub'}
              </button>
            </div>
          </div>
        </section>

        {/* Available Labs Section */}
        <section className="labs-section">
          <div className="section-header">
            <h3>Available Labs</h3>
            {labs.length > 0 && (
              <span className="lab-count">{labs.reduce((total, category) => total + category.labs.length, 0)} labs available</span>
            )}
          </div>
          {labs.length > 0 ? (
            <div className="lab-categories">
              {labs.map((category, idx) => (
                <div key={idx} className="lab-category">
                  <h4 className="category-title">
                    {category.category}
                    <span className="category-count">({category.labs.length})</span>
                  </h4>
                  <div className="lab-grid">
                    {category.labs.slice(0, 6).map((lab, labIdx) => (
                      <div key={labIdx} className="lab-card">
                        <div className="lab-header">
                          <h5>{lab.name}</h5>
                        </div>
                        <div className="lab-content">
                          <p className="lab-description">{lab.description || 'Network lab topology'}</p>
                          <div className="lab-meta">
                            {lab.nodes && <span className="meta-tag">📊 {lab.nodes} nodes</span>}
                            {lab.kinds && lab.kinds.length > 0 && (
                              <span className="meta-tag">🏷️ {lab.kinds.slice(0, 2).join(', ')}</span>
                            )}
                          </div>
                        </div>
                        <div className="lab-actions">
                          <button 
                            className="btn-launch" 
                            onClick={() => launchLab(lab)}
                            disabled={loading}
                          >
                            {loading ? '⏳' : '🚀'} Launch
                          </button>
                        </div>
                      </div>
                    ))}
                    {category.labs.length > 6 && (
                      <div className="lab-card more-labs">
                        <div className="more-content">
                          <span className="more-count">+{category.labs.length - 6}</span>
                          <span className="more-text">more labs</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">🔬</div>
              <h4>No labs found</h4>
              <p>Import labs from popular repositories or build your own custom lab</p>
              <div className="empty-actions">
                <button className="btn-primary" onClick={scanGitHubLabs} disabled={loading}>
                  📚 Import Labs
                </button>
                <button className="btn-secondary" onClick={() => setCurrentView('builder')}>
                  🎨 Build Lab
                </button>
              </div>
            </div>
          )}
        </section>


        {/* Active Labs Section */}
        {activeLabs.length > 0 && (
          <section className="active-labs-section">
            <div className="section-header">
              <h3>Running Labs</h3>
              <span className="active-count">{activeLabs.length} active</span>
            </div>
            <div className="active-labs-grid">
              {activeLabs.map((lab, idx) => (
                <div key={idx} className="active-lab-card">
                  <div className="lab-status-indicator running"></div>
                  <div className="active-lab-content">
                    <h5>{lab.name}</h5>
                    <div className="lab-details">
                      <span className="detail-item">🔗 {lab.node_count || 0} nodes</span>
                      <span className="detail-item">⏱️ {lab.created_at ? new Date(parseFloat(lab.created_at) * 1000).toLocaleDateString() : 'Unknown'}</span>
                    </div>
                  </div>
                  <button 
                    className="btn-stop" 
                    onClick={() => stopLab(lab.lab_id)}
                    disabled={loading}
                    title="Stop Lab"
                  >
                    {loading ? '⏳' : '⏹️'}
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

          </>
        )}
      </main>
    </div>
  )
}

export default App