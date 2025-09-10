import { useState, useEffect } from 'react'
import './VRNetLabManager.css'

function VRNetLabManager() {
  // State management
  const [activeTab, setActiveTab] = useState('upload')
  const [vmImages, setVmImages] = useState([])
  const [builds, setBuilds] = useState([])
  const [builtContainers, setBuiltContainers] = useState([])
  const [supportedVendors, setSupportedVendors] = useState({})
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    file: null,
    vendor: '',
    platform: '',
    version: 'latest'
  })

  // Build form state
  const [buildForm, setBuildForm] = useState({
    imageId: '',
    containerName: '',
    containerTag: 'latest'
  })

  // Get API base URL
  const apiBase = window.location.protocol + '//' + window.location.hostname + ':8000'

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        fetchVmImages(),
        fetchBuilds(),
        fetchBuiltContainers(),
        fetchSupportedVendors()
      ])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchVmImages = async () => {
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/images`)
      const data = await response.json()
      if (data.success) {
        setVmImages(data.images)
      }
    } catch (error) {
      console.error('Error fetching VM images:', error)
    }
  }

  const fetchBuilds = async () => {
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/builds`)
      const data = await response.json()
      if (data.success) {
        setBuilds(data.builds)
      }
    } catch (error) {
      console.error('Error fetching builds:', error)
    }
  }

  const fetchBuiltContainers = async () => {
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/containers`)
      const data = await response.json()
      if (data.success) {
        setBuiltContainers(data.containers)
      }
    } catch (error) {
      console.error('Error fetching built containers:', error)
    }
  }

  const fetchSupportedVendors = async () => {
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/vendors`)
      const data = await response.json()
      if (data.success) {
        setSupportedVendors(data.vendors)
      }
    } catch (error) {
      console.error('Error fetching supported vendors:', error)
    }
  }

  const handleFileUpload = async (event) => {
    event.preventDefault()
    if (!uploadForm.file || !uploadForm.vendor || !uploadForm.platform) {
      alert('Please fill in all required fields and select a file')
      return
    }

    setLoading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('vendor', uploadForm.vendor)
      formData.append('platform', uploadForm.platform)
      formData.append('version', uploadForm.version)

      const response = await fetch(`${apiBase}/api/vrnetlab/upload`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (response.ok && data.success) {
        alert(`VM image uploaded successfully: ${data.metadata.filename}`)
        setUploadForm({ file: null, vendor: '', platform: '', version: 'latest' })
        // Reset file input
        document.getElementById('fileInput').value = ''
        await fetchVmImages()
      } else {
        alert(`Upload failed: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error uploading file:', error)
      alert('Error uploading file')
    } finally {
      setLoading(false)
      setUploadProgress(0)
    }
  }

  const handleBuildContainer = async (event) => {
    event.preventDefault()
    if (!buildForm.imageId) {
      alert('Please select a VM image to build')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/build`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_id: buildForm.imageId,
          container_name: buildForm.containerName || undefined,
          container_tag: buildForm.containerTag
        })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        alert(`Container build started: ${data.container_name}\\nBuild ID: ${data.build_id}`)
        setBuildForm({ imageId: '', containerName: '', containerTag: 'latest' })
        await fetchBuilds()
      } else {
        alert(`Build failed: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error starting build:', error)
      alert('Error starting build')
    } finally {
      setLoading(false)
    }
  }

  const initializeVRNetlab = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/init`, {
        method: 'POST'
      })

      const data = await response.json()

      if (response.ok && data.success) {
        alert('VRNetlab repository initialized successfully!')
      } else {
        alert(`Initialization failed: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error initializing VRNetlab:', error)
      alert('Error initializing VRNetlab repository')
    } finally {
      setLoading(false)
    }
  }

  const deleteVmImage = async (imageId, filename) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
      return
    }

    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/images/${imageId}`, {
        method: 'DELETE'
      })

      const data = await response.json()

      if (response.ok && data.success) {
        alert(data.message)
        await fetchVmImages()
      } else {
        alert(`Delete failed: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error deleting VM image:', error)
      alert('Error deleting VM image')
    }
  }

  const getBuildStatus = async (buildId) => {
    try {
      const response = await fetch(`${apiBase}/api/vrnetlab/builds/${buildId}/status`)
      const data = await response.json()
      
      if (response.ok && data.success) {
        // Update the specific build in the builds array
        setBuilds(prevBuilds => 
          prevBuilds.map(build => 
            build.build_id === buildId ? data.build : build
          )
        )
      }
    } catch (error) {
      console.error('Error fetching build status:', error)
    }
  }

  const formatFileSize = (bytes) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    if (bytes === 0) return '0 Byte'
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString()
  }

  if (loading && vmImages.length === 0) {
    return <div className="vrnetlab-loading">Loading VRNetlab Manager...</div>
  }

  return (
    <div className="vrnetlab-manager">
      <div className="vrnetlab-header">
        <h2>🏗️ VRNetlab VM-to-Container Converter</h2>
        <p>Upload VM images and convert them to containerlab-ready containers</p>
        <button 
          className="btn-secondary init-btn" 
          onClick={initializeVRNetlab}
          disabled={loading}
        >
          {loading ? 'Initializing...' : 'Initialize VRNetlab'}
        </button>
      </div>

      <div className="vrnetlab-tabs">
        <button 
          className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload VM Images
        </button>
        <button 
          className={`tab-btn ${activeTab === 'images' ? 'active' : ''}`}
          onClick={() => setActiveTab('images')}
        >
          VM Images ({vmImages.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'builds' ? 'active' : ''}`}
          onClick={() => setActiveTab('builds')}
        >
          Build Status ({builds.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'containers' ? 'active' : ''}`}
          onClick={() => setActiveTab('containers')}
        >
          Built Containers ({builtContainers.length})
        </button>
      </div>

      <div className="vrnetlab-content">
        {activeTab === 'upload' && (
          <div className="upload-section">
            <h3>Upload VM Image</h3>
            <form onSubmit={handleFileUpload} className="upload-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="vendor">Vendor *</label>
                  <select 
                    id="vendor" 
                    value={uploadForm.vendor} 
                    onChange={(e) => {
                      setUploadForm({...uploadForm, vendor: e.target.value, platform: ''})
                    }}
                    required
                  >
                    <option value="">Select Vendor</option>
                    {Object.keys(supportedVendors).map(vendor => (
                      <option key={vendor} value={vendor}>{vendor.charAt(0).toUpperCase() + vendor.slice(1)}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label htmlFor="platform">Platform *</label>
                  <select 
                    id="platform" 
                    value={uploadForm.platform} 
                    onChange={(e) => setUploadForm({...uploadForm, platform: e.target.value})}
                    required
                    disabled={!uploadForm.vendor}
                  >
                    <option value="">Select Platform</option>
                    {uploadForm.vendor && supportedVendors[uploadForm.vendor] && 
                      Object.keys(supportedVendors[uploadForm.vendor]).map(platform => (
                        <option key={platform} value={platform}>{platform.toUpperCase()}</option>
                      ))
                    }
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="version">Version</label>
                  <input 
                    type="text" 
                    id="version" 
                    value={uploadForm.version} 
                    onChange={(e) => setUploadForm({...uploadForm, version: e.target.value})}
                    placeholder="latest"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="fileInput">VM Image File *</label>
                <input 
                  type="file" 
                  id="fileInput"
                  onChange={(e) => setUploadForm({...uploadForm, file: e.target.files[0]})}
                  accept=".qcow2,.vmdk,.ova,.bin,.tar,.tgz,.tar.xz,.iso"
                  required
                />
                {uploadForm.vendor && uploadForm.platform && supportedVendors[uploadForm.vendor]?.[uploadForm.platform] && (
                  <small className="file-info">
                    Supported extensions: {supportedVendors[uploadForm.vendor][uploadForm.platform].extensions.join(', ')}
                  </small>
                )}
              </div>

              {uploadProgress > 0 && (
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: `${uploadProgress}%`}}></div>
                </div>
              )}

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Uploading...' : 'Upload VM Image'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'images' && (
          <div className="images-section">
            <div className="section-header">
              <h3>Uploaded VM Images</h3>
              <button className="btn-secondary" onClick={fetchVmImages}>
                Refresh
              </button>
            </div>
            
            {vmImages.length === 0 ? (
              <p className="empty-state">No VM images uploaded yet. Upload your first VM image above!</p>
            ) : (
              <div className="images-grid">
                {vmImages.map((image, idx) => (
                  <div key={idx} className="image-card">
                    <div className="image-header">
                      <h4>{image.filename}</h4>
                      <span className={`status-badge ${image.status}`}>{image.status}</span>
                    </div>
                    
                    <div className="image-details">
                      <p><strong>Vendor:</strong> {image.vendor}</p>
                      <p><strong>Platform:</strong> {image.platform}</p>
                      <p><strong>Version:</strong> {image.version}</p>
                      <p><strong>Size:</strong> {formatFileSize(image.file_size)}</p>
                      <p><strong>Uploaded:</strong> {formatDate(image.uploaded_at)}</p>
                      <p><strong>VRNetlab:</strong> {image.vrnetlab_name}</p>
                    </div>
                    
                    <div className="image-actions">
                      <button 
                        className="btn-primary"
                        onClick={() => {
                          setBuildForm({...buildForm, imageId: image.id})
                          setActiveTab('builds')
                        }}
                      >
                        Build Container
                      </button>
                      <button 
                        className="btn-danger"
                        onClick={() => deleteVmImage(image.id, image.filename)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'builds' && (
          <div className="builds-section">
            <div className="section-header">
              <h3>Container Builds</h3>
              <button className="btn-secondary" onClick={fetchBuilds}>
                Refresh
              </button>
            </div>

            <div className="build-form-section">
              <h4>Start New Build</h4>
              <form onSubmit={handleBuildContainer} className="build-form">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="imageSelect">VM Image *</label>
                    <select 
                      id="imageSelect"
                      value={buildForm.imageId} 
                      onChange={(e) => setBuildForm({...buildForm, imageId: e.target.value})}
                      required
                    >
                      <option value="">Select VM Image</option>
                      {vmImages.map((image) => (
                        <option key={image.id} value={image.id}>
                          {image.filename} ({image.vendor}/{image.platform})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="containerName">Container Name (optional)</label>
                    <input 
                      type="text" 
                      id="containerName"
                      value={buildForm.containerName} 
                      onChange={(e) => setBuildForm({...buildForm, containerName: e.target.value})}
                      placeholder="Auto-generated if empty"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="containerTag">Container Tag</label>
                    <input 
                      type="text" 
                      id="containerTag"
                      value={buildForm.containerTag} 
                      onChange={(e) => setBuildForm({...buildForm, containerTag: e.target.value})}
                      placeholder="latest"
                    />
                  </div>
                </div>

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Starting Build...' : 'Start Build'}
                </button>
              </form>
            </div>

            {builds.length === 0 ? (
              <p className="empty-state">No builds started yet. Upload VM images and start your first build!</p>
            ) : (
              <div className="builds-list">
                {builds.map((build, idx) => (
                  <div key={idx} className={`build-card ${build.status}`}>
                    <div className="build-header">
                      <h4>{build.container_name}</h4>
                      <span className={`status-badge ${build.status}`}>{build.status}</span>
                      <button 
                        className="btn-sm"
                        onClick={() => getBuildStatus(build.build_id)}
                      >
                        Refresh Status
                      </button>
                    </div>
                    
                    <div className="build-details">
                      <p><strong>Build ID:</strong> {build.build_id}</p>
                      <p><strong>Vendor:</strong> {build.vendor}</p>
                      <p><strong>Platform:</strong> {build.platform}</p>
                      <p><strong>VRNetlab:</strong> {build.vrnetlab_name}</p>
                      <p><strong>Started:</strong> {formatDate(build.started_at)}</p>
                      {build.completed_at && (
                        <p><strong>Completed:</strong> {formatDate(build.completed_at)}</p>
                      )}
                      {build.failed_at && (
                        <p><strong>Failed:</strong> {formatDate(build.failed_at)}</p>
                      )}
                      {build.container_image && (
                        <p><strong>Image:</strong> {build.container_image}</p>
                      )}
                      {build.error && (
                        <p className="error-text"><strong>Error:</strong> {build.error}</p>
                      )}
                    </div>

                    {build.logs && build.logs.length > 0 && (
                      <div className="build-logs">
                        <h5>Build Logs (last 5 lines):</h5>
                        <pre>{build.logs.slice(-5).join('\\n')}</pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'containers' && (
          <div className="containers-section">
            <div className="section-header">
              <h3>Built Containers</h3>
              <button className="btn-secondary" onClick={fetchBuiltContainers}>
                Refresh
              </button>
            </div>
            
            {builtContainers.length === 0 ? (
              <p className="empty-state">No containers built yet. Build your first container from uploaded VM images!</p>
            ) : (
              <div className="containers-grid">
                {builtContainers.map((container, idx) => (
                  <div key={idx} className="container-card built">
                    <div className="container-header">
                      <h4>{container.name}</h4>
                      <span className="status-badge completed">Ready</span>
                    </div>
                    
                    <div className="container-details">
                      <p><strong>Image:</strong> {container.image}</p>
                      <p><strong>Vendor:</strong> {container.vendor}</p>
                      <p><strong>Platform:</strong> {container.platform}</p>
                      <p><strong>Kind:</strong> {container.kind}</p>
                      <p><strong>Build ID:</strong> {container.build_id}</p>
                      <p><strong>Created:</strong> {formatDate(container.created_at)}</p>
                    </div>

                    <div className="container-actions">
                      <button className="btn-primary">
                        Use in Lab
                      </button>
                      <button className="btn-secondary">
                        Export
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default VRNetLabManager