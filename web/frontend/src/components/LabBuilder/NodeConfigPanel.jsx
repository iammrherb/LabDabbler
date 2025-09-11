import { useState, useEffect } from 'react'
import './NodeConfigPanel.css'

function NodeConfigPanel({ node, onUpdate, onClose }) {
  const [config, setConfig] = useState({
    name: '',
    image: '',
    kind: '',
    startup_config: '',
    env: {},
    ports: [],
    volumes: [],
    binds: [],
    ...node
  })
  
  const [activeTab, setActiveTab] = useState('general')
  const [newEnvKey, setNewEnvKey] = useState('')
  const [newEnvValue, setNewEnvValue] = useState('')
  const [newPort, setNewPort] = useState('')
  const [newVolume, setNewVolume] = useState('')
  const [newBind, setNewBind] = useState({ source: '', target: '' })

  useEffect(() => {
    setConfig({
      name: '',
      image: '',
      kind: '',
      startup_config: '',
      env: {},
      ports: [],
      volumes: [],
      binds: [],
      ...node
    })
  }, [node])

  const handleInputChange = (field, value) => {
    const newConfig = { ...config, [field]: value }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const addEnvironmentVariable = () => {
    if (newEnvKey && newEnvValue) {
      const newEnv = { ...config.env, [newEnvKey]: newEnvValue }
      handleInputChange('env', newEnv)
      setNewEnvKey('')
      setNewEnvValue('')
    }
  }

  const removeEnvironmentVariable = (key) => {
    const newEnv = { ...config.env }
    delete newEnv[key]
    handleInputChange('env', newEnv)
  }

  const addPort = () => {
    if (newPort && !config.ports.includes(newPort)) {
      handleInputChange('ports', [...config.ports, newPort])
      setNewPort('')
    }
  }

  const removePort = (index) => {
    const newPorts = config.ports.filter((_, i) => i !== index)
    handleInputChange('ports', newPorts)
  }

  const addVolume = () => {
    if (newVolume && !config.volumes.includes(newVolume)) {
      handleInputChange('volumes', [...config.volumes, newVolume])
      setNewVolume('')
    }
  }

  const removeVolume = (index) => {
    const newVolumes = config.volumes.filter((_, i) => i !== index)
    handleInputChange('volumes', newVolumes)
  }

  const addBind = () => {
    if (newBind.source && newBind.target) {
      const bindString = `${newBind.source}:${newBind.target}`
      if (!config.binds.includes(bindString)) {
        handleInputChange('binds', [...config.binds, bindString])
        setNewBind({ source: '', target: '' })
      }
    }
  }

  const removeBind = (index) => {
    const newBinds = config.binds.filter((_, i) => i !== index)
    handleInputChange('binds', newBinds)
  }

  const getKindInfo = (kind) => {
    const kindInfo = {
      'nokia_srlinux': {
        description: 'Nokia SR Linux Network OS',
        defaultPorts: ['22/tcp', '57400/tcp', '830/tcp'],
        requiredEnv: {},
        tips: 'NETCONF available on port 830, gRPC on 57400'
      },
      'arista_ceos': {
        description: 'Arista Container EOS',
        defaultPorts: ['22/tcp', '443/tcp', '830/tcp'],
        requiredEnv: { 'CEOS_MODE': 'CONTAINER' },
        tips: 'Requires privileged mode and specific environment variables'
      },
      'cisco': {
        description: 'Cisco Network Device',
        defaultPorts: ['22/tcp', '830/tcp'],
        requiredEnv: {},
        tips: 'SSH and NETCONF support typical'
      },
      'juniper': {
        description: 'Juniper Network Device',
        defaultPorts: ['22/tcp', '830/tcp'],
        requiredEnv: {},
        tips: 'Junos-based virtual devices'
      },
      'linux': {
        description: 'Generic Linux Container',
        defaultPorts: ['22/tcp'],
        requiredEnv: {},
        tips: 'Standard Linux container with networking capabilities'
      }
    }
    return kindInfo[kind] || {
      description: 'Custom container',
      defaultPorts: [],
      requiredEnv: {},
      tips: 'Configure according to container requirements'
    }
  }

  const kindInfo = getKindInfo(config.kind)

  const validateConfiguration = () => {
    const issues = []
    
    if (!config.name || config.name.trim() === '') {
      issues.push('Node name is required')
    }
    
    if (!config.image || config.image.trim() === '') {
      issues.push('Container image is required')
    }
    
    if (!config.kind || config.kind.trim() === '') {
      issues.push('Container kind is required')
    }
    
    // Check for invalid characters in name
    if (config.name && !/^[a-zA-Z0-9-_]+$/.test(config.name)) {
      issues.push('Node name can only contain letters, numbers, hyphens, and underscores')
    }
    
    return issues
  }

  const validationIssues = validateConfiguration()

  return (
    <div className="node-config-panel">
      <div className="config-header">
        <h3>⚙️ Node Configuration</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="config-tabs">
        <button 
          className={`tab ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
        <button 
          className={`tab ${activeTab === 'networking' ? 'active' : ''}`}
          onClick={() => setActiveTab('networking')}
        >
          Networking
        </button>
        <button 
          className={`tab ${activeTab === 'environment' ? 'active' : ''}`}
          onClick={() => setActiveTab('environment')}
        >
          Environment
        </button>
        <button 
          className={`tab ${activeTab === 'storage' ? 'active' : ''}`}
          onClick={() => setActiveTab('storage')}
        >
          Storage
        </button>
      </div>
      
      <div className="config-content">
        {activeTab === 'general' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Node Name</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter node name (e.g., router1, switch1)"
              />
              <small>Must be unique within the topology</small>
            </div>
            
            <div className="form-group">
              <label>Container Image</label>
              <input
                type="text"
                value={config.image}
                onChange={(e) => handleInputChange('image', e.target.value)}
                placeholder="Container image (e.g., ghcr.io/nokia/srlinux:latest)"
              />
            </div>
            
            <div className="form-group">
              <label>Container Kind</label>
              <select
                value={config.kind}
                onChange={(e) => handleInputChange('kind', e.target.value)}
              >
                <option value="">Select kind...</option>
                <option value="nokia_srlinux">Nokia SR Linux</option>
                <option value="arista_ceos">Arista cEOS</option>
                <option value="cisco">Cisco</option>
                <option value="juniper">Juniper</option>
                <option value="linux">Linux</option>
                <option value="bridge">Bridge</option>
                <option value="ovs">Open vSwitch</option>
              </select>
              {config.kind && (
                <div className="kind-info">
                  <p><strong>{kindInfo.description}</strong></p>
                  <p><small>{kindInfo.tips}</small></p>
                </div>
              )}
            </div>
            
            <div className="form-group">
              <label>Startup Configuration</label>
              <textarea
                value={config.startup_config}
                onChange={(e) => handleInputChange('startup_config', e.target.value)}
                placeholder="Path to startup configuration file (optional)"
                rows="3"
              />
              <small>Relative path to configuration file in lab directory</small>
            </div>
          </div>
        )}
        
        {activeTab === 'networking' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Port Mappings</label>
              <div className="list-input">
                <div className="input-with-button">
                  <input
                    type="text"
                    value={newPort}
                    onChange={(e) => setNewPort(e.target.value)}
                    placeholder="Port mapping (e.g., 8080:80, 22:22)"
                  />
                  <button onClick={addPort} disabled={!newPort}>Add</button>
                </div>
                <div className="list-items">
                  {config.ports.map((port, index) => (
                    <div key={index} className="list-item">
                      <span>{port}</span>
                      <button onClick={() => removePort(index)}>Remove</button>
                    </div>
                  ))}
                </div>
                {kindInfo.defaultPorts.length > 0 && (
                  <div className="suggestions">
                    <small>Suggested ports for {config.kind}: {kindInfo.defaultPorts.join(', ')}</small>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'environment' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Environment Variables</label>
              <div className="env-input">
                <div className="input-row">
                  <input
                    type="text"
                    value={newEnvKey}
                    onChange={(e) => setNewEnvKey(e.target.value)}
                    placeholder="Variable name"
                  />
                  <input
                    type="text"
                    value={newEnvValue}
                    onChange={(e) => setNewEnvValue(e.target.value)}
                    placeholder="Variable value"
                  />
                  <button onClick={addEnvironmentVariable} disabled={!newEnvKey || !newEnvValue}>
                    Add
                  </button>
                </div>
                <div className="env-list">
                  {Object.entries(config.env).map(([key, value]) => (
                    <div key={key} className="env-item">
                      <span className="env-key">{key}</span>
                      <span className="env-value">{value}</span>
                      <button onClick={() => removeEnvironmentVariable(key)}>Remove</button>
                    </div>
                  ))}
                </div>
                {Object.keys(kindInfo.requiredEnv).length > 0 && (
                  <div className="suggestions">
                    <small>Required for {config.kind}:</small>
                    {Object.entries(kindInfo.requiredEnv).map(([key, value]) => (
                      <div key={key} className="required-env">
                        <code>{key}={value}</code>
                        {!config.env[key] && (
                          <button 
                            onClick={() => handleInputChange('env', { ...config.env, [key]: value })}
                            className="add-required"
                          >
                            Add
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'storage' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Volumes</label>
              <div className="list-input">
                <div className="input-with-button">
                  <input
                    type="text"
                    value={newVolume}
                    onChange={(e) => setNewVolume(e.target.value)}
                    placeholder="Volume name"
                  />
                  <button onClick={addVolume} disabled={!newVolume}>Add</button>
                </div>
                <div className="list-items">
                  {config.volumes.map((volume, index) => (
                    <div key={index} className="list-item">
                      <span>{volume}</span>
                      <button onClick={() => removeVolume(index)}>Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="form-group">
              <label>Bind Mounts</label>
              <div className="bind-input">
                <div className="input-row">
                  <input
                    type="text"
                    value={newBind.source}
                    onChange={(e) => setNewBind({ ...newBind, source: e.target.value })}
                    placeholder="Host path"
                  />
                  <input
                    type="text"
                    value={newBind.target}
                    onChange={(e) => setNewBind({ ...newBind, target: e.target.value })}
                    placeholder="Container path"
                  />
                  <button onClick={addBind} disabled={!newBind.source || !newBind.target}>
                    Add
                  </button>
                </div>
                <div className="list-items">
                  {config.binds.map((bind, index) => (
                    <div key={index} className="list-item">
                      <span>{bind}</span>
                      <button onClick={() => removeBind(index)}>Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {validationIssues.length > 0 && (
        <div className="validation-issues">
          <h4>⚠️ Configuration Issues</h4>
          <ul>
            {validationIssues.map((issue, index) => (
              <li key={index}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="config-footer">
        <div className="config-summary">
          <small>
            Node: <strong>{config.name || 'Unnamed'}</strong> |
            Kind: <strong>{config.kind || 'Unknown'}</strong> |
            Ports: <strong>{config.ports.length}</strong> |
            Env vars: <strong>{Object.keys(config.env).length}</strong>
          </small>
        </div>
      </div>
    </div>
  )
}

export default NodeConfigPanel