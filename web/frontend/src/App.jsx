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
        fetch('http://localhost:8000/api/labs'),
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
          <h2>Available Labs</h2>
          {labs.length > 0 ? (
            labs.map((category, idx) => (
              <div key={idx} className="lab-category">
                <h3>{category.category}</h3>
                <div className="lab-grid">
                  {category.labs.map((lab, labIdx) => (
                    <div key={labIdx} className="lab-card">
                      <h4>{lab.name}</h4>
                      <p>{lab.description}</p>
                      <button className="btn-primary">Launch Lab</button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p>No labs found. Create your first lab below!</p>
          )}
        </section>

        <section className="containers-section">
          <h2>Available Containers</h2>
          {Object.keys(containers).length > 0 ? (
            Object.entries(containers).map(([category, containerList]) => (
              <div key={category} className="container-category">
                <h3>{category.replace('_', ' ').toUpperCase()}</h3>
                <div className="container-grid">
                  {containerList.map((container, idx) => (
                    <div key={idx} className="container-card">
                      <h4>{container.name}</h4>
                      <p className="image-name">{container.image}</p>
                      <p>{container.description}</p>
                      <button className="btn-secondary">Add to Lab</button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p>Loading containers...</p>
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