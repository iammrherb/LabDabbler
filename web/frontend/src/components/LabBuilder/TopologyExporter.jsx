import { useState, useMemo } from 'react'
import './TopologyExporter.css'

function TopologyExporter({ topology, onClose, onExport, onGitHubExport }) {
  const [exportFormat, setExportFormat] = useState('clab')
  const [includeConfigs, setIncludeConfigs] = useState(true)
  const [generateConfigFiles, setGenerateConfigFiles] = useState(false)
  const [labDirectory, setLabDirectory] = useState('')
  const [containerPrefix, setContainerPrefix] = useState('')
  const [includeManagement, setIncludeManagement] = useState(true)
  const [managementNetwork, setManagementNetwork] = useState('mgmt')

  const generateContainerlabYAML = () => {
    const nodes = {}
    const links = []

    // Process nodes
    Object.values(topology.nodes).forEach(node => {
      const nodeConfig = {
        kind: node.kind,
        image: node.image
      }

      // Add optional configurations
      if (node.config.startup_config) {
        nodeConfig.startup_config = node.config.startup_config
      }

      if (node.config.env && Object.keys(node.config.env).length > 0) {
        nodeConfig.env = node.config.env
      }

      if (node.config.ports && node.config.ports.length > 0) {
        nodeConfig.ports = node.config.ports
      }

      if (node.config.binds && node.config.binds.length > 0) {
        nodeConfig.binds = node.config.binds
      }

      if (node.config.volumes && node.config.volumes.length > 0) {
        nodeConfig.volumes = node.config.volumes
      }

      nodes[node.name] = nodeConfig
    })

    // Process links
    topology.links.forEach(link => {
      const node1 = topology.nodes[link.endpoints[0].node]
      const node2 = topology.nodes[link.endpoints[1].node]
      
      if (node1 && node2) {
        const endpoints = [
          `${node1.name}:${link.endpoints[0].interface}`,
          `${node2.name}:${link.endpoints[1].interface}`
        ]
        links.push({ endpoints })
      }
    })

    // Build the complete YAML structure
    const labConfig = {
      name: topology.name,
      topology: {
        nodes,
        links
      }
    }

    // Add optional global settings
    if (containerPrefix) {
      labConfig.prefix = containerPrefix
    }

    if (includeManagement) {
      labConfig.mgmt = {
        network: managementNetwork,
        ipv4_subnet: '172.20.20.0/24'
      }
    }

    return labConfig
  }

  const generateYAMLString = (obj) => {
    // Simple YAML generator (for complex cases, would use a proper YAML library)
    const yamlLines = []
    
    const processObject = (obj, indent = 0) => {
      const spaces = '  '.repeat(indent)
      
      Object.entries(obj).forEach(([key, value]) => {
        if (value === null || value === undefined) {
          yamlLines.push(`${spaces}${key}: null`)
        } else if (typeof value === 'string') {
          yamlLines.push(`${spaces}${key}: "${value}"`)
        } else if (typeof value === 'number' || typeof value === 'boolean') {
          yamlLines.push(`${spaces}${key}: ${value}`)
        } else if (Array.isArray(value)) {
          if (value.length === 0) {
            yamlLines.push(`${spaces}${key}: []`)
          } else {
            yamlLines.push(`${spaces}${key}:`)
            value.forEach(item => {
              if (typeof item === 'object') {
                yamlLines.push(`${spaces}  -`)
                processObject(item, indent + 2)
              } else {
                yamlLines.push(`${spaces}  - ${item}`)
              }
            })
          }
        } else if (typeof value === 'object') {
          yamlLines.push(`${spaces}${key}:`)
          processObject(value, indent + 1)
        }
      })
    }

    processObject(obj)
    return yamlLines.join('\n')
  }

  const exportContent = useMemo(() => {
    if (exportFormat === 'clab') {
      const labConfig = generateContainerlabYAML()
      return generateYAMLString(labConfig)
    } else if (exportFormat === 'json') {
      return JSON.stringify(topology, null, 2)
    }
    return ''
  }, [topology, exportFormat, containerPrefix, includeManagement, managementNetwork])

  const downloadFile = () => {
    const extension = exportFormat === 'clab' ? 'clab.yml' : 'json'
    const filename = `${topology.name}.${extension}`
    const mimeType = exportFormat === 'clab' ? 'text/yaml' : 'application/json'
    
    const blob = new Blob([exportContent], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(exportContent)
    alert('Content copied to clipboard!')
  }

  const saveAndLaunch = async () => {
    try {
      // First save the topology
      await onExport(`${topology.name}-${Date.now()}`)
      
      // Then attempt to launch it
      const domain = import.meta.env.VITE_REPLIT_DOMAINS || window.location.hostname
      const apiBase = window.location.hostname.includes('replit.dev') 
        ? `${window.location.protocol}//${domain.replace('-00-', '-8000-')}`
        : `${window.location.protocol}//${window.location.hostname}:8000`
      const response = await fetch(`${apiBase}/api/lab-builder/launch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          topology: generateContainerlabYAML(),
          name: topology.name
        })
      })
      
      if (response.ok) {
        alert('Topology exported and launched successfully!')
        onClose()
      } else {
        const error = await response.json()
        alert(`Failed to launch topology: ${error.message}`)
      }
    } catch (error) {
      console.error('Error saving and launching:', error)
      alert('Failed to save and launch topology')
    }
  }

  const validateTopology = () => {
    const issues = []
    
    // Check node names
    const nodeNames = Object.values(topology.nodes).map(node => node.name)
    const duplicates = nodeNames.filter((name, index) => nodeNames.indexOf(name) !== index)
    if (duplicates.length > 0) {
      issues.push(`Duplicate node names: ${[...new Set(duplicates)].join(', ')}`)
    }
    
    // Check for required fields
    Object.values(topology.nodes).forEach(node => {
      if (!node.name || !node.image || !node.kind) {
        issues.push(`Node ${node.id} missing required fields`)
      }
    })
    
    // Check links
    topology.links.forEach((link, index) => {
      const node1 = topology.nodes[link.endpoints[0].node]
      const node2 = topology.nodes[link.endpoints[1].node]
      if (!node1 || !node2) {
        issues.push(`Link ${index + 1} references non-existent nodes`)
      }
    })
    
    return issues
  }

  const validationIssues = validateTopology()
  const isValid = validationIssues.length === 0

  return (
    <div className="topology-exporter">
      <div className="exporter-overlay">
        <div className="exporter-modal">
          <div className="exporter-header">
            <h3>📤 Export Topology</h3>
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
          
          <div className="exporter-content">
            <div className="export-options">
              <div className="option-group">
                <label>Export Format</label>
                <div className="radio-group">
                  <label className="radio-option">
                    <input
                      type="radio"
                      value="clab"
                      checked={exportFormat === 'clab'}
                      onChange={(e) => setExportFormat(e.target.value)}
                    />
                    <span>Containerlab YAML (.clab.yml)</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={(e) => setExportFormat(e.target.value)}
                    />
                    <span>JSON Format (.json)</span>
                  </label>
                </div>
              </div>

              {exportFormat === 'clab' && (
                <>
                  <div className="option-group">
                    <label>Container Prefix (optional)</label>
                    <input
                      type="text"
                      value={containerPrefix}
                      onChange={(e) => setContainerPrefix(e.target.value)}
                      placeholder="e.g., lab-, demo-"
                    />
                    <small>Prefix for all container names</small>
                  </div>

                  <div className="option-group">
                    <label className="checkbox-option">
                      <input
                        type="checkbox"
                        checked={includeManagement}
                        onChange={(e) => setIncludeManagement(e.target.checked)}
                      />
                      <span>Include Management Network</span>
                    </label>
                    {includeManagement && (
                      <input
                        type="text"
                        value={managementNetwork}
                        onChange={(e) => setManagementNetwork(e.target.value)}
                        placeholder="Management network name"
                      />
                    )}
                  </div>

                  <div className="option-group">
                    <label className="checkbox-option">
                      <input
                        type="checkbox"
                        checked={includeConfigs}
                        onChange={(e) => setIncludeConfigs(e.target.checked)}
                      />
                      <span>Include Configuration Files</span>
                    </label>
                  </div>

                  <div className="option-group">
                    <label className="checkbox-option">
                      <input
                        type="checkbox"
                        checked={generateConfigFiles}
                        onChange={(e) => setGenerateConfigFiles(e.target.checked)}
                      />
                      <span>Generate Basic Config Files</span>
                    </label>
                    <small>Create starter configuration files for network devices</small>
                  </div>
                </>
              )}
            </div>

            {validationIssues.length > 0 && (
              <div className="validation-errors">
                <h4>⚠️ Validation Issues</h4>
                <ul>
                  {validationIssues.map((issue, index) => (
                    <li key={index}>{issue}</li>
                  ))}
                </ul>
                <p><strong>Please fix these issues before exporting.</strong></p>
              </div>
            )}

            <div className="export-preview">
              <div className="preview-header">
                <h4>📋 Export Preview</h4>
                <div className="preview-stats">
                  <span>{Object.keys(topology.nodes).length} nodes</span>
                  <span>{topology.links.length} links</span>
                  <span>{exportContent.split('\n').length} lines</span>
                </div>
              </div>
              <pre className="preview-content">
                {exportContent}
              </pre>
            </div>
          </div>
          
          <div className="exporter-footer">
            <div className="footer-left">
              <button 
                className="btn-secondary"
                onClick={copyToClipboard}
                disabled={!isValid}
              >
                📋 Copy
              </button>
              <button 
                className="btn-secondary"
                onClick={downloadFile}
                disabled={!isValid}
              >
                💾 Download
              </button>
            </div>
            
            <div className="footer-right">
              <button 
                className="btn-secondary"
                onClick={onClose}
              >
                Cancel
              </button>
              {exportFormat === 'clab' && onGitHubExport && (
                <button 
                  className="btn-github"
                  onClick={onGitHubExport}
                  disabled={!isValid}
                >
                  🚀 Export to Codespaces
                </button>
              )}
              {exportFormat === 'clab' && (
                <button 
                  className="btn-primary"
                  onClick={saveAndLaunch}
                  disabled={!isValid}
                >
                  🚀 Save & Launch
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TopologyExporter