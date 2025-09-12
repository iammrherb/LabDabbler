import { useState, useEffect, useMemo } from 'react'
import './ContainerPalette.css'

// Helper functions defined outside component to avoid hoisting issues
const getCategoryIcon = (category) => {
  const icons = {
    'network_os_native': '🔧',
    'network_os_vm_based': '🖥️',
    'portnox': '🛡️',
    'open_source_network': '🌐',
    'security_firewalls': '🔥',
    'security': '🔒',
    'security_pentesting': '⚔️',
    'security_monitoring': '👁️',
    'services': '⚙️',
    'network_simulation': '🧪',
    'network_monitoring': '📊',
    'network_automation': '🤖',
    'development': '💻',
    'ci_cd': '🚀',
    'databases': '🗄️',
    'message_queues': '📬',
    'web_servers': '🌍',
    'monitoring_observability': '📈',
    'analytics': '📉',
    'testing_load': '⚡',
    'vrnetlab_built': '🏗️'
  }
  return icons[category] || '📦'
}

const getCategoryDisplayName = (category) => {
  const names = {
    'network_os_native': 'Network OS (Native)',
    'network_os_vm_based': 'Network OS (VM)',
    'portnox': 'Portnox Security',
    'open_source_network': 'Open Source Network',
    'security_firewalls': 'Firewalls',
    'security': 'Security Tools',
    'security_pentesting': 'Penetration Testing',
    'security_monitoring': 'Security Monitoring',
    'services': 'Network Services',
    'network_simulation': 'Network Simulation',
    'network_monitoring': 'Network Monitoring',
    'network_automation': 'Network Automation',
    'development': 'Development Tools',
    'ci_cd': 'CI/CD Tools',
    'databases': 'Databases',
    'message_queues': 'Message Queues',
    'web_servers': 'Web Servers',
    'monitoring_observability': 'Monitoring & Observability',
    'analytics': 'Analytics',
    'testing_load': 'Load Testing',
    'vrnetlab_built': 'VRNetlab Images'
  }
  return names[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const getContainerKind = (container) => {
  // Determine containerlab kind based on container info
  if (container.kind) return container.kind
  
  const image = container.image || ''
  const vendor = (container.vendor || '').toLowerCase()
  const name = (container.name || '').toLowerCase()
  
  // Network OS specific kinds
  if (image.includes('srlinux')) return 'nokia_srlinux'
  if (image.includes('ceos')) return 'arista_ceos'
  if (image.includes('sros')) return 'nokia_sros'
  if (image.includes('juniper')) return 'juniper'
  if (image.includes('cisco')) return 'cisco'
  if (vendor.includes('nokia')) return 'nokia_srlinux'
  if (vendor.includes('arista')) return 'arista_ceos'
  if (vendor.includes('juniper')) return 'juniper'
  if (vendor.includes('cisco')) return 'cisco'
  
  // Default to linux for most containers
  return 'linux'
}

const getVendorColor = (vendor) => {
  const colors = {
    'nokia': '#124191',
    'arista': '#f05a28',
    'cisco': '#1ba0d7',
    'juniper': '#84bd00',
    'portnox': '#6c5ce7',
    'fortinet': '#ee5a52',
    'palo alto': '#fa6d1c'
  }
  return colors[(vendor || '').toLowerCase()] || '#666'
}

function ContainerPalette({ containers, onContainerDrag }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [expandedCategories, setExpandedCategories] = useState(new Set(['network_os_native', 'portnox', 'open_source_network']))
  const [draggedContainer, setDraggedContainer] = useState(null)

  // Categorize containers
  const categorizedContainers = useMemo(() => {
    const categories = {}
    
    containers.forEach(container => {
      const category = container.category || 'other'
      if (!categories[category]) {
        categories[category] = {
          name: category,
          icon: getCategoryIcon(category),
          containers: []
        }
      }
      categories[category].containers.push(container)
    })
    
    // Sort containers within each category
    Object.values(categories).forEach(category => {
      category.containers.sort((a, b) => {
        // Sort by vendor first, then by name
        const vendorCompare = (a.vendor || '').localeCompare(b.vendor || '')
        if (vendorCompare !== 0) return vendorCompare
        return (a.name || '').localeCompare(b.name || '')
      })
    })
    
    return categories
  }, [containers])

  // Filter containers based on search and category
  const filteredCategories = useMemo(() => {
    const filtered = {}
    
    Object.entries(categorizedContainers).forEach(([key, category]) => {
      if (selectedCategory && key !== selectedCategory) return
      
      const filteredContainers = category.containers.filter(container => {
        if (!searchQuery) return true
        
        const searchLower = searchQuery.toLowerCase()
        return (
          (container.name || '').toLowerCase().includes(searchLower) ||
          (container.vendor || '').toLowerCase().includes(searchLower) ||
          (container.description || '').toLowerCase().includes(searchLower) ||
          (container.image || '').toLowerCase().includes(searchLower)
        )
      })
      
      if (filteredContainers.length > 0) {
        filtered[key] = {
          ...category,
          containers: filteredContainers
        }
      }
    })
    
    return filtered
  }, [categorizedContainers, searchQuery, selectedCategory])

  const toggleCategory = (categoryKey) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(categoryKey)) {
      newExpanded.delete(categoryKey)
    } else {
      newExpanded.add(categoryKey)
    }
    setExpandedCategories(newExpanded)
  }

  const handleDragStart = (e, container) => {
    setDraggedContainer(container)
    e.dataTransfer.setData('application/json', JSON.stringify(container))
    e.dataTransfer.effectAllowed = 'copy'
    
    // Create a custom drag image
    const dragImage = e.target.cloneNode(true)
    dragImage.style.transform = 'rotate(-5deg)'
    dragImage.style.opacity = '0.8'
    document.body.appendChild(dragImage)
    e.dataTransfer.setDragImage(dragImage, 50, 25)
    
    setTimeout(() => {
      document.body.removeChild(dragImage)
    }, 0)
  }

  const handleDragEnd = () => {
    setDraggedContainer(null)
  }


  return (
    <div className="container-palette">
      <div className="palette-header">
        <h3>🧰 Container Palette</h3>
        <p>Drag containers to the canvas</p>
      </div>
      
      <div className="palette-controls">
        <input
          type="text"
          placeholder="Search containers..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="category-filter"
        >
          <option value="">All Categories</option>
          {Object.keys(categorizedContainers).map(key => (
            <option key={key} value={key}>
              {getCategoryIcon(key)} {getCategoryDisplayName(key)}
            </option>
          ))}
        </select>
      </div>
      
      <div className="palette-content">
        {Object.entries(filteredCategories).map(([categoryKey, category]) => (
          <div key={categoryKey} className="container-category">
            <div 
              className="category-header"
              onClick={() => toggleCategory(categoryKey)}
            >
              <span className="category-icon">{category.icon}</span>
              <span className="category-name">{getCategoryDisplayName(categoryKey)}</span>
              <span className="container-count">({category.containers.length})</span>
              <span className={`expand-icon ${expandedCategories.has(categoryKey) ? 'expanded' : ''}`}>
                ▼
              </span>
            </div>
            
            {expandedCategories.has(categoryKey) && (
              <div className="category-containers">
                {category.containers.map((container, index) => (
                  <div
                    key={`${container.image}-${index}`}
                    className={`container-item ${draggedContainer === container ? 'dragging' : ''}`}
                    draggable
                    onDragStart={(e) => handleDragStart(e, container)}
                    onDragEnd={handleDragEnd}
                    title={`${container.name}\n${container.description || 'No description'}\nImage: ${container.image}\nKind: ${getContainerKind(container)}`}
                  >
                    <div className="container-header">
                      <span 
                        className="vendor-badge"
                        style={{ backgroundColor: getVendorColor(container.vendor) }}
                      >
                        {(container.vendor || 'Unknown').substring(0, 3).toUpperCase()}
                      </span>
                      <span className="container-name">{container.name}</span>
                    </div>
                    
                    <div className="container-details">
                      <div className="container-image">
                        {container.image}
                      </div>
                      <div className="container-kind">
                        Kind: {getContainerKind(container)}
                      </div>
                      {container.architecture && (
                        <div className="container-arch">
                          Arch: {Array.isArray(container.architecture) ? container.architecture.join(', ') : container.architecture}
                        </div>
                      )}
                    </div>
                    
                    <div className="drag-indicator">
                      ⋮⋮
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {Object.keys(filteredCategories).length === 0 && (
          <div className="no-containers">
            <p>No containers found matching your search criteria.</p>
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="clear-search">
                Clear Search
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ContainerPalette