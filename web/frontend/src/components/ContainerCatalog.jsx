import { useState, useEffect } from 'react'
import './ContainerCatalog.css'

function ContainerCatalog() {
  const [containers, setContainers] = useState([])
  const [categories, setCategories] = useState({})
  const [vendors, setVendors] = useState([])
  const [architectures, setArchitectures] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedVendor, setSelectedVendor] = useState('')
  const [selectedArchitecture, setSelectedArchitecture] = useState('')
  const [viewMode, setViewMode] = useState('grid') // grid, list, categories
  const [sortBy, setSortBy] = useState('name') // name, vendor, category
  const [selectedContainers, setSelectedContainers] = useState(new Set())

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const resultsPerPage = 24

  const apiBase = window.location.protocol + '//' + window.location.hostname + ':8000'

  useEffect(() => {
    fetchInitialData()
  }, [])

  useEffect(() => {
    searchContainers()
  }, [searchQuery, selectedCategory, selectedVendor, selectedArchitecture, currentPage, sortBy])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      const [categoriesRes, vendorsRes, architecturesRes, statsRes] = await Promise.all([
        fetch(`${apiBase}/api/containers/categories`),
        fetch(`${apiBase}/api/containers/vendors`),
        fetch(`${apiBase}/api/containers/architectures`),
        fetch(`${apiBase}/api/containers/stats`)
      ])

      const [categoriesData, vendorsData, architecturesData, statsData] = await Promise.all([
        categoriesRes.json(),
        vendorsRes.json(),
        architecturesRes.json(),
        statsRes.json()
      ])

      setCategories(categoriesData.categories)
      setVendors(vendorsData.vendors)
      setArchitectures(architecturesData.architectures)
      setStats(statsData)

      // Trigger initial search
      searchContainers()
    } catch (error) {
      console.error('Error fetching initial data:', error)
      setError('Failed to load container catalog')
    } finally {
      setLoading(false)
    }
  }

  const searchContainers = async () => {
    try {
      const offset = (currentPage - 1) * resultsPerPage
      const url = new URL(`${apiBase}/api/containers/search`)
      
      url.searchParams.append('q', searchQuery)
      url.searchParams.append('category', selectedCategory)
      url.searchParams.append('vendor', selectedVendor)
      url.searchParams.append('architecture', selectedArchitecture)
      url.searchParams.append('limit', resultsPerPage.toString())
      url.searchParams.append('offset', offset.toString())

      const response = await fetch(url)
      const data = await response.json()

      setContainers(data.results)
      setTotalResults(data.total)
      setHasMore(data.pagination.has_more)
      setError('')
    } catch (error) {
      console.error('Error searching containers:', error)
      setError('Failed to search containers')
    }
  }

  const refreshCatalog = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${apiBase}/api/containers/refresh`, {
        method: 'POST'
      })
      const data = await response.json()
      
      alert(`Container catalog refreshed! Found ${data.stats.total_containers} containers in ${data.stats.total_categories} categories.`)
      
      // Refresh data
      await fetchInitialData()
    } catch (error) {
      console.error('Error refreshing catalog:', error)
      alert('Failed to refresh catalog')
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedCategory('')
    setSelectedVendor('')
    setSelectedArchitecture('')
    setCurrentPage(1)
  }

  const toggleContainerSelection = (containerImage) => {
    const newSelected = new Set(selectedContainers)
    if (newSelected.has(containerImage)) {
      newSelected.delete(containerImage)
    } else {
      newSelected.add(containerImage)
    }
    setSelectedContainers(newSelected)
  }

  const exportSelectedContainers = () => {
    if (selectedContainers.size === 0) {
      alert('No containers selected')
      return
    }

    const selectedData = containers.filter(container => 
      selectedContainers.has(container.image)
    )

    const exportData = {
      containers: selectedData,
      exported_at: new Date().toISOString(),
      total_count: selectedData.length
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `container-selection-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const copyContainerCommand = (container) => {
    const command = `docker run -d ${container.ports ? container.ports.map(p => `-p ${p}`).join(' ') : ''} ${container.image}`.replace(/\s+/g, ' ').trim()
    navigator.clipboard.writeText(command)
    alert('Docker command copied to clipboard!')
  }

  const formatArchitectures = (archs) => {
    if (!archs) return 'Unknown'
    if (Array.isArray(archs)) return archs.join(', ')
    return archs
  }

  const getCategoryIcon = (categoryName) => {
    return categories[categoryName]?.icon || '📦'
  }

  const getCategoryColor = (categoryName) => {
    return categories[categoryName]?.color || '#666'
  }

  if (loading && containers.length === 0) {
    return (
      <div className="catalog-loading">
        <div className="loading-spinner"></div>
        <p>Loading container catalog...</p>
      </div>
    )
  }

  return (
    <div className="container-catalog">
      <div className="catalog-header">
        <div className="header-main">
          <h1>🐳 Container Catalog</h1>
          <p>Comprehensive Docker application catalog for containerlab environments</p>
        </div>
        
        <div className="header-stats">
          <div className="stat-card">
            <span className="stat-number">{stats.total_containers || 0}</span>
            <span className="stat-label">Containers</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{stats.total_categories || 0}</span>
            <span className="stat-label">Categories</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{vendors.length}</span>
            <span className="stat-label">Vendors</span>
          </div>
        </div>

        <div className="header-actions">
          <button 
            className="btn-secondary" 
            onClick={refreshCatalog}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : '🔄 Refresh Catalog'}
          </button>
          
          {selectedContainers.size > 0 && (
            <button className="btn-primary" onClick={exportSelectedContainers}>
              📥 Export Selected ({selectedContainers.size})
            </button>
          )}
        </div>
      </div>

      <div className="catalog-controls">
        <div className="search-section">
          <div className="search-input">
            <input
              type="text"
              placeholder="Search containers by name, description, or features..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setCurrentPage(1)
              }}
            />
            <span className="search-icon">🔍</span>
          </div>
          
          <div className="filter-controls">
            <select 
              value={selectedCategory} 
              onChange={(e) => {
                setSelectedCategory(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">All Categories</option>
              {Object.entries(categories).map(([id, category]) => (
                <option key={id} value={id}>
                  {category.icon} {category.name} ({category.container_count})
                </option>
              ))}
            </select>

            <select 
              value={selectedVendor} 
              onChange={(e) => {
                setSelectedVendor(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">All Vendors</option>
              {vendors.map(vendor => (
                <option key={vendor} value={vendor}>{vendor}</option>
              ))}
            </select>

            <select 
              value={selectedArchitecture} 
              onChange={(e) => {
                setSelectedArchitecture(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">All Architectures</option>
              {architectures.map(arch => (
                <option key={arch} value={arch}>{arch}</option>
              ))}
            </select>

            <button className="btn-clear" onClick={clearFilters}>
              Clear Filters
            </button>
          </div>
        </div>

        <div className="view-controls">
          <div className="view-mode">
            <button 
              className={viewMode === 'categories' ? 'active' : ''} 
              onClick={() => setViewMode('categories')}
              title="Category View"
            >
              📋
            </button>
            <button 
              className={viewMode === 'grid' ? 'active' : ''} 
              onClick={() => setViewMode('grid')}
              title="Grid View"
            >
              ⊞
            </button>
            <button 
              className={viewMode === 'list' ? 'active' : ''} 
              onClick={() => setViewMode('list')}
              title="List View"
            >
              ☰
            </button>
          </div>

          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="name">Sort by Name</option>
            <option value="vendor">Sort by Vendor</option>
            <option value="category">Sort by Category</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="catalog-results">
        <div className="results-summary">
          <p>
            {totalResults > 0 ? (
              <>
                Showing {containers.length} of {totalResults} containers
                {(searchQuery || selectedCategory || selectedVendor || selectedArchitecture) && (
                  <span className="filtered"> (filtered)</span>
                )}
              </>
            ) : (
              'No containers found'
            )}
          </p>
        </div>

        {viewMode === 'categories' && (
          <div className="category-view">
            {Object.entries(categories).map(([categoryId, category]) => (
              <div key={categoryId} className="category-section">
                <div className="category-header">
                  <h3>
                    <span className="category-icon">{category.icon}</span>
                    {category.name}
                    <span className="category-count">({category.container_count})</span>
                  </h3>
                  <p className="category-description">{category.description}</p>
                </div>
                <div className="category-containers">
                  {containers
                    .filter(container => container.category_name === categoryId)
                    .slice(0, 6) // Show first 6 containers per category
                    .map((container, index) => (
                      <div key={index} className="container-card mini">
                        <h4>{container.name}</h4>
                        <p className="container-vendor">{container.vendor}</p>
                        <div className="container-image">{container.image}</div>
                      </div>
                    ))}
                  {containers.filter(container => container.category_name === categoryId).length > 6 && (
                    <button 
                      className="show-more-btn"
                      onClick={() => {
                        setSelectedCategory(categoryId)
                        setViewMode('grid')
                      }}
                    >
                      +{containers.filter(container => container.category_name === categoryId).length - 6} more
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {(viewMode === 'grid' || viewMode === 'list') && (
          <div className={`containers-${viewMode}`}>
            {containers.map((container, index) => (
              <div key={index} className={`container-card ${viewMode} ${selectedContainers.has(container.image) ? 'selected' : ''}`}>
                <div className="container-header">
                  <div className="container-title">
                    <input
                      type="checkbox"
                      checked={selectedContainers.has(container.image)}
                      onChange={() => toggleContainerSelection(container.image)}
                    />
                    <h3>{container.name}</h3>
                    <span 
                      className="category-badge"
                      style={{ backgroundColor: getCategoryColor(container.category_name) }}
                    >
                      {getCategoryIcon(container.category_name)} {categories[container.category_name]?.name || container.category_name}
                    </span>
                  </div>
                  
                  <div className="container-actions">
                    <button 
                      className="btn-icon"
                      onClick={() => copyContainerCommand(container)}
                      title="Copy Docker command"
                    >
                      📋
                    </button>
                  </div>
                </div>

                <div className="container-details">
                  <p className="container-description">{container.description}</p>
                  
                  <div className="container-meta">
                    <div className="meta-item">
                      <strong>Vendor:</strong> {container.vendor}
                    </div>
                    <div className="meta-item">
                      <strong>Image:</strong> 
                      <code>{container.image}</code>
                    </div>
                    <div className="meta-item">
                      <strong>Architecture:</strong> {formatArchitectures(container.architecture)}
                    </div>
                    <div className="meta-item">
                      <strong>Access:</strong> 
                      <span className={`access-badge ${container.access || 'unknown'}`}>
                        {container.access || 'Unknown'}
                      </span>
                    </div>
                    {container.registry && (
                      <div className="meta-item">
                        <strong>Registry:</strong> {container.registry}
                      </div>
                    )}
                  </div>

                  {container.ports && (
                    <div className="container-ports">
                      <strong>Ports:</strong>
                      {container.ports.map((port, idx) => (
                        <span key={idx} className="port-badge">{port}</span>
                      ))}
                    </div>
                  )}

                  {container.features && (
                    <div className="container-features">
                      <strong>Features:</strong>
                      {container.features.map((feature, idx) => (
                        <span key={idx} className="feature-badge">{feature}</span>
                      ))}
                    </div>
                  )}

                  {container.protocols && (
                    <div className="container-protocols">
                      <strong>Protocols:</strong>
                      {container.protocols.map((protocol, idx) => (
                        <span key={idx} className="protocol-badge">{protocol}</span>
                      ))}
                    </div>
                  )}

                  {container.tools && (
                    <div className="container-tools">
                      <strong>Tools:</strong>
                      {container.tools.map((tool, idx) => (
                        <span key={idx} className="tool-badge">{tool}</span>
                      ))}
                    </div>
                  )}

                  {(container.documentation || container.download_url) && (
                    <div className="container-links">
                      {container.documentation && (
                        <a 
                          href={container.documentation} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="link-btn"
                        >
                          📚 Documentation
                        </a>
                      )}
                      {container.download_url && (
                        <a 
                          href={container.download_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="link-btn"
                        >
                          💾 Download
                        </a>
                      )}
                    </div>
                  )}

                  {(container.requirements || container.installation_notes) && (
                    <div className="container-notes">
                      {container.requirements && (
                        <div className="note requirements">
                          <strong>Requirements:</strong> {container.requirements}
                        </div>
                      )}
                      {container.installation_notes && (
                        <div className="note installation">
                          <strong>Installation:</strong> {container.installation_notes}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {containers.length === 0 && !loading && (
          <div className="empty-results">
            <div className="empty-icon">📦</div>
            <h3>No containers found</h3>
            <p>Try adjusting your search criteria or filters</p>
            <button className="btn-primary" onClick={clearFilters}>
              Clear All Filters
            </button>
          </div>
        )}

        {totalResults > resultsPerPage && (
          <div className="pagination">
            <button 
              disabled={currentPage === 1} 
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              Previous
            </button>
            <span className="page-info">
              Page {currentPage} of {Math.ceil(totalResults / resultsPerPage)}
            </span>
            <button 
              disabled={!hasMore} 
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              Next
            </button>
          </div>
        )}
      </div>

      {stats.last_updated && (
        <div className="catalog-footer">
          <p>
            Last updated: {new Date(parseFloat(stats.last_updated) * 1000).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  )
}

export default ContainerCatalog