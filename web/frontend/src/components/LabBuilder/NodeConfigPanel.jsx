import { useState, useEffect } from 'react'
import { api } from '../../utils/api'
import './NodeConfigPanel.css'

function NodeConfigPanel({ node, onUpdate, onClose }) {
  const [config, setConfig] = useState({
    name: '',
    image: '',
    kind: '',
    type: '',
    startup_config: '',
    license: '',
    env: {},
    ports: [],
    volumes: [],
    binds: [],
    sysctls: {},
    capabilities: [],
    privileged: false,
    user: '',
    group: '',
    cpu_limit: '',
    memory_limit: '',
    restart_policy: 'unless-stopped',
    network_mode: 'bridge',
    extra_hosts: [],
    ...node
  })
  
  const [activeTab, setActiveTab] = useState('general')
  const [newEnvKey, setNewEnvKey] = useState('')
  const [newEnvValue, setNewEnvValue] = useState('')
  const [newPort, setNewPort] = useState('')
  const [newVolume, setNewVolume] = useState('')
  const [newBind, setNewBind] = useState({ source: '', target: '' })
  const [newSysctlKey, setNewSysctlKey] = useState('')
  const [newSysctlValue, setNewSysctlValue] = useState('')
  const [newCapability, setNewCapability] = useState('')
  const [newExtraHost, setNewExtraHost] = useState('')
  const [kindTemplate, setKindTemplate] = useState(null)
  const [loadingTemplate, setLoadingTemplate] = useState(false)

  useEffect(() => {
    setConfig({
      name: '',
      image: '',
      kind: '',
      type: '',
      startup_config: '',
      license: '',
      env: {},
      ports: [],
      volumes: [],
      binds: [],
      sysctls: {},
      capabilities: [],
      privileged: false,
      user: '',
      group: '',
      cpu_limit: '',
      memory_limit: '',
      restart_policy: 'unless-stopped',
      network_mode: 'bridge',
      extra_hosts: [],
      ...node
    })
    
    // Load kind template when node changes
    if (node && node.kind) {
      loadKindTemplate(node.kind)
    }
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

  // Sysctls management
  const addSysctl = () => {
    if (newSysctlKey && newSysctlValue) {
      const newSysctls = { ...config.sysctls, [newSysctlKey]: newSysctlValue }
      handleInputChange('sysctls', newSysctls)
      setNewSysctlKey('')
      setNewSysctlValue('')
    }
  }

  const removeSysctl = (key) => {
    const newSysctls = { ...config.sysctls }
    delete newSysctls[key]
    handleInputChange('sysctls', newSysctls)
  }

  // Capabilities management
  const addCapability = () => {
    if (newCapability && !config.capabilities.includes(newCapability)) {
      handleInputChange('capabilities', [...config.capabilities, newCapability])
      setNewCapability('')
    }
  }

  const removeCapability = (index) => {
    const newCapabilities = config.capabilities.filter((_, i) => i !== index)
    handleInputChange('capabilities', newCapabilities)
  }

  // Extra hosts management
  const addExtraHost = () => {
    if (newExtraHost && !config.extra_hosts.includes(newExtraHost)) {
      handleInputChange('extra_hosts', [...config.extra_hosts, newExtraHost])
      setNewExtraHost('')
    }
  }

  const removeExtraHost = (index) => {
    const newExtraHosts = config.extra_hosts.filter((_, i) => i !== index)
    handleInputChange('extra_hosts', newExtraHosts)
  }

  // Load kind template from backend
  const loadKindTemplate = async (kind) => {
    if (!kind) return
    
    try {
      setLoadingTemplate(true)
      const response = await api.get(`/api/containerlab/kinds/${kind}/template`)
      setKindTemplate(response.template)
    } catch (error) {
      console.error('Error loading kind template:', error)
      setKindTemplate(null)
    } finally {
      setLoadingTemplate(false)
    }
  }

  // Apply template defaults to configuration
  const applyTemplateDefaults = () => {
    if (!kindTemplate) return

    const updates = {}
    
    // Apply default image if not set
    if (kindTemplate.default_image && !config.image) {
      updates.image = kindTemplate.default_image
    }
    
    // Apply default type if available
    if (kindTemplate.default_type && !config.type) {
      updates.type = kindTemplate.default_type
    }
    
    // Apply default environment variables
    if (kindTemplate.env) {
      updates.env = { ...kindTemplate.env, ...config.env }
    }
    
    // Apply default sysctls
    if (kindTemplate.sysctls) {
      updates.sysctls = { ...kindTemplate.sysctls, ...config.sysctls }
    }
    
    // Apply default capabilities
    if (kindTemplate.capabilities) {
      const newCapabilities = [...new Set([...config.capabilities, ...kindTemplate.capabilities])]
      updates.capabilities = newCapabilities
    }
    
    // Apply default ports
    if (kindTemplate.ports) {
      const newPorts = [...new Set([...config.ports, ...kindTemplate.ports])]
      updates.ports = newPorts
    }

    // Update config with all changes
    const newConfig = { ...config, ...updates }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const getKindInfo = (kind) => {
    // Use template data if available, otherwise fallback to static data
    if (kindTemplate) {
      return {
        description: kindTemplate.notes ? kindTemplate.notes[0] : `${kind} container`,
        defaultPorts: kindTemplate.ports || [],
        requiredEnv: kindTemplate.env || {},
        tips: kindTemplate.notes ? kindTemplate.notes.slice(1).join('; ') : 'Configure according to container requirements',
        documentation: kindTemplate.documentation,
        defaultCredentials: kindTemplate.default_credentials,
        requiredFields: kindTemplate.required_fields || [],
        capabilities: kindTemplate.capabilities || [],
        sysctls: kindTemplate.sysctls || {},
        defaultType: kindTemplate.default_type
      }
    }
    
    // Fallback static data
    const kindInfo = {
      'srl': {
        description: 'Nokia SR Linux Network OS',
        defaultPorts: ['22/tcp', '57400/tcp', '830/tcp'],
        requiredEnv: {},
        tips: 'NETCONF available on port 830, gRPC on 57400'
      },
      'ceos': {
        description: 'Arista Container EOS',
        defaultPorts: ['22/tcp', '443/tcp', '830/tcp'],
        requiredEnv: { 'CEOS_MODE': 'CONTAINER' },
        tips: 'Requires privileged mode and specific environment variables'
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
        <button 
          className={`tab ${activeTab === 'advanced' ? 'active' : ''}`}
          onClick={() => setActiveTab('advanced')}
        >
          Advanced
        </button>
        <button 
          className={`tab ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          Security
        </button>
        <button 
          className={`tab ${activeTab === 'resources' ? 'active' : ''}`}
          onClick={() => setActiveTab('resources')}
        >
          Resources
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
                onChange={(e) => {
                  handleInputChange('kind', e.target.value)
                  loadKindTemplate(e.target.value)
                }}
              >
                <option value="">Select kind...</option>
                
                {/* Infrastructure kinds */}
                <optgroup label="Infrastructure">
                  <option value="linux">Linux Container</option>
                  <option value="bridge">Software Bridge</option>
                  <option value="ovs">Open vSwitch</option>
                  <option value="host">Host Container</option>
                  <option value="ext_container">External Container</option>
                  <option value="generic_vm">Generic VM</option>
                  <option value="k8s_kind">Kubernetes Kind</option>
                </optgroup>
                
                {/* Nokia */}
                <optgroup label="Nokia">
                  <option value="srl">SR Linux (Container)</option>
                  <option value="sros">SR OS (Container)</option>
                  <option value="vr_sros">SR OS (VM)</option>
                </optgroup>
                
                {/* Arista */}
                <optgroup label="Arista">
                  <option value="ceos">cEOS (Container)</option>
                  <option value="vr_veos">vEOS (VM)</option>
                </optgroup>
                
                {/* Cisco */}
                <optgroup label="Cisco">
                  <option value="c8000">Catalyst 8000 (Container)</option>
                  <option value="xrd">XRd (Container)</option>
                  <option value="vr_csr">CSR 1000v (VM)</option>
                  <option value="vr_c8000v">Catalyst 8000V (VM)</option>
                  <option value="vr_cat9kv">Catalyst 9000V (VM)</option>
                  <option value="vr_xrv">XRv (VM)</option>
                  <option value="vr_xrv9k">XRv9000 (VM)</option>
                  <option value="vr_n9kv">Nexus 9000V (VM)</option>
                  <option value="vr_ftdv">FTDv (VM)</option>
                  <option value="iol">IOL</option>
                </optgroup>
                
                {/* Juniper */}
                <optgroup label="Juniper">
                  <option value="crpd">cRPD (Container)</option>
                  <option value="cjunosevolved">cJunos Evolved (Container)</option>
                  <option value="vr_vmx">vMX (VM)</option>
                  <option value="vr_vqfx">vQFX (VM)</option>
                  <option value="vr_vsrx">vSRX (VM)</option>
                  <option value="vr_vjunosevolved">vJunos Evolved (VM)</option>
                  <option value="vr_vjunosswitch">vJunos Switch (VM)</option>
                </optgroup>
                
                {/* Other Vendors */}
                <optgroup label="Other Network OS">
                  <option value="fortinet_fortigate">Fortinet FortiGate</option>
                  <option value="vr_pan">Palo Alto PAN-OS</option>
                  <option value="sonic">SONiC (Container)</option>
                  <option value="sonic_vm">SONiC (VM)</option>
                  <option value="dell_sonic">Dell SONiC</option>
                  <option value="vyosnetworks_vyos">VyOS</option>
                  <option value="cvx">Cumulus VX</option>
                  <option value="huawei_vrp">Huawei VRP</option>
                  <option value="ipinfusion_ocnos">IP Infusion OcNOS</option>
                  <option value="rare">RARE/freeRtr</option>
                  <option value="6wind_vsr">6WIND VSR</option>
                  <option value="vr_aoscx">Aruba AOS-CX</option>
                  <option value="vr_ftosv">Dell FTOS</option>
                  <option value="vr_ros">MikroTik RouterOS</option>
                  <option value="fdio_vpp">FD.io VPP</option>
                  <option value="checkpoint_cloudguard">Check Point CloudGuard</option>
                  <option value="keysight_ixiacone">Keysight IxiaC-One</option>
                </optgroup>
                
                {/* Virtual Platforms */}
                <optgroup label="Virtual Platforms">
                  <option value="vr_freebsd">FreeBSD</option>
                  <option value="vr_openbsd">OpenBSD</option>
                  <option value="vr_openwrt">OpenWrt</option>
                </optgroup>
              </select>
              {config.kind && (
                <div className="kind-info">
                  <p><strong>{kindInfo.description}</strong></p>
                  <p><small>{kindInfo.tips}</small></p>
                  
                  {kindTemplate && (
                    <div className="template-info">
                      {kindTemplate.documentation && (
                        <div className="template-docs">
                          <a 
                            href={kindTemplate.documentation} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="docs-link"
                          >
                            📖 Documentation
                          </a>
                        </div>
                      )}
                      
                      {kindTemplate.default_credentials && (
                        <div className="default-credentials">
                          <small>
                            <strong>Default credentials:</strong> 
                            {kindTemplate.default_credentials.username} / {kindTemplate.default_credentials.password}
                          </small>
                        </div>
                      )}
                      
                      {kindTemplate.required_fields && kindTemplate.required_fields.length > 0 && (
                        <div className="required-fields">
                          <small>
                            <strong>Required fields:</strong> {kindTemplate.required_fields.join(', ')}
                          </small>
                        </div>
                      )}
                      
                      <div className="template-actions">
                        <button 
                          onClick={applyTemplateDefaults} 
                          className="apply-template-btn"
                          disabled={loadingTemplate}
                        >
                          {loadingTemplate ? 'Loading...' : 'Apply Template Defaults'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {config.kind && kindTemplate && kindTemplate.default_type && (
              <div className="form-group">
                <label>Device Type</label>
                <input
                  type="text"
                  value={config.type}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  placeholder={kindTemplate.default_type}
                />
                <small>Device type for {config.kind} (default: {kindTemplate.default_type})</small>
              </div>
            )}
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.privileged}
                  onChange={(e) => handleInputChange('privileged', e.target.checked)}
                />
                <span>Privileged Mode</span>
              </label>
              <small>Enable privileged mode for containers that require it</small>
            </div>
            
            {config.user && (
              <div className="form-group">
                <label>Run as User</label>
                <input
                  type="text"
                  value={config.user}
                  onChange={(e) => handleInputChange('user', e.target.value)}
                  placeholder="user:group or uid:gid"
                />
                <small>User context to run the container</small>
              </div>
            )}
            
            {config.kind && (
              <div className="form-group">
                <label>License File</label>
                <input
                  type="text"
                  value={config.license}
                  onChange={(e) => handleInputChange('license', e.target.value)}
                  placeholder="Path to license file (optional)"
                />
                <small>Required for some commercial network OS images</small>
              </div>
            )}
            
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
        
        {activeTab === 'advanced' && (
          <div className="tab-content">
            <div className="form-group">
              <label>System Controls (sysctls)</label>
              <div className="sysctl-input">
                <div className="input-row">
                  <input
                    type="text"
                    value={newSysctlKey}
                    onChange={(e) => setNewSysctlKey(e.target.value)}
                    placeholder="Sysctl parameter (e.g., net.ipv4.ip_forward)"
                  />
                  <input
                    type="text"
                    value={newSysctlValue}
                    onChange={(e) => setNewSysctlValue(e.target.value)}
                    placeholder="Value (e.g., 1)"
                  />
                  <button onClick={addSysctl} disabled={!newSysctlKey || !newSysctlValue}>
                    Add
                  </button>
                </div>
                <div className="sysctl-list">
                  {Object.entries(config.sysctls || {}).map(([key, value]) => (
                    <div key={key} className="sysctl-item">
                      <span className="sysctl-key">{key}</span>
                      <span className="sysctl-value">{value}</span>
                      <button onClick={() => removeSysctl(key)}>Remove</button>
                    </div>
                  ))}
                </div>
                {kindTemplate && kindTemplate.sysctls && (
                  <div className="suggestions">
                    <small>Recommended sysctls for {config.kind}:</small>
                    {Object.entries(kindTemplate.sysctls).map(([key, value]) => (
                      <div key={key} className="suggested-sysctl">
                        <code>{key}={value}</code>
                        {!config.sysctls[key] && (
                          <button 
                            onClick={() => handleInputChange('sysctls', { ...config.sysctls, [key]: value })}
                            className="add-suggested"
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

            <div className="form-group">
              <label>Network Mode</label>
              <select
                value={config.network_mode}
                onChange={(e) => handleInputChange('network_mode', e.target.value)}
              >
                <option value="bridge">Bridge</option>
                <option value="host">Host</option>
                <option value="none">None</option>
                <option value="container">Container</option>
              </select>
              <small>Container networking mode</small>
            </div>

            <div className="form-group">
              <label>Restart Policy</label>
              <select
                value={config.restart_policy}
                onChange={(e) => handleInputChange('restart_policy', e.target.value)}
              >
                <option value="no">No</option>
                <option value="always">Always</option>
                <option value="unless-stopped">Unless Stopped</option>
                <option value="on-failure">On Failure</option>
              </select>
              <small>Container restart behavior</small>
            </div>

            <div className="form-group">
              <label>Extra Hosts</label>
              <div className="list-input">
                <div className="input-with-button">
                  <input
                    type="text"
                    value={newExtraHost}
                    onChange={(e) => setNewExtraHost(e.target.value)}
                    placeholder="hostname:ip (e.g., host.example.com:192.168.1.1)"
                  />
                  <button onClick={addExtraHost} disabled={!newExtraHost}>Add</button>
                </div>
                <div className="list-items">
                  {config.extra_hosts.map((host, index) => (
                    <div key={index} className="list-item">
                      <span>{host}</span>
                      <button onClick={() => removeExtraHost(index)}>Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'security' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Linux Capabilities</label>
              <div className="capability-input">
                <div className="input-with-button">
                  <select
                    value={newCapability}
                    onChange={(e) => setNewCapability(e.target.value)}
                  >
                    <option value="">Select capability...</option>
                    <option value="SYS_ADMIN">SYS_ADMIN</option>
                    <option value="NET_ADMIN">NET_ADMIN</option>
                    <option value="NET_RAW">NET_RAW</option>
                    <option value="SYS_PTRACE">SYS_PTRACE</option>
                    <option value="SYS_TIME">SYS_TIME</option>
                    <option value="MKNOD">MKNOD</option>
                    <option value="AUDIT_WRITE">AUDIT_WRITE</option>
                    <option value="CHOWN">CHOWN</option>
                    <option value="DAC_OVERRIDE">DAC_OVERRIDE</option>
                    <option value="FOWNER">FOWNER</option>
                    <option value="FSETID">FSETID</option>
                    <option value="KILL">KILL</option>
                    <option value="SETGID">SETGID</option>
                    <option value="SETUID">SETUID</option>
                    <option value="SETPCAP">SETPCAP</option>
                    <option value="LINUX_IMMUTABLE">LINUX_IMMUTABLE</option>
                    <option value="NET_BIND_SERVICE">NET_BIND_SERVICE</option>
                    <option value="NET_BROADCAST">NET_BROADCAST</option>
                    <option value="IPC_LOCK">IPC_LOCK</option>
                    <option value="IPC_OWNER">IPC_OWNER</option>
                    <option value="SYS_MODULE">SYS_MODULE</option>
                    <option value="SYS_RAWIO">SYS_RAWIO</option>
                    <option value="SYS_CHROOT">SYS_CHROOT</option>
                    <option value="SYS_PACCT">SYS_PACCT</option>
                    <option value="SYS_BOOT">SYS_BOOT</option>
                    <option value="SYS_NICE">SYS_NICE</option>
                    <option value="SYS_RESOURCE">SYS_RESOURCE</option>
                    <option value="SYS_TTY_CONFIG">SYS_TTY_CONFIG</option>
                    <option value="WAKE_ALARM">WAKE_ALARM</option>
                    <option value="BLOCK_SUSPEND">BLOCK_SUSPEND</option>
                  </select>
                  <button onClick={addCapability} disabled={!newCapability}>Add</button>
                </div>
                <div className="capability-list">
                  {config.capabilities.map((cap, index) => (
                    <div key={index} className="capability-item">
                      <span className="capability-name">{cap}</span>
                      <button onClick={() => removeCapability(index)}>Remove</button>
                    </div>
                  ))}
                </div>
                {kindTemplate && kindTemplate.capabilities && (
                  <div className="suggestions">
                    <small>Required capabilities for {config.kind}:</small>
                    {kindTemplate.capabilities.map(cap => (
                      <div key={cap} className="suggested-capability">
                        <code>{cap}</code>
                        {!config.capabilities.includes(cap) && (
                          <button 
                            onClick={() => handleInputChange('capabilities', [...config.capabilities, cap])}
                            className="add-suggested"
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

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.privileged}
                  onChange={(e) => handleInputChange('privileged', e.target.checked)}
                />
                Privileged Mode
              </label>
              <small>Grant extended privileges to this container (required for some network OS)</small>
            </div>

            <div className="form-group">
              <label>User</label>
              <input
                type="text"
                value={config.user}
                onChange={(e) => handleInputChange('user', e.target.value)}
                placeholder="User ID or name (optional)"
              />
              <small>User to run container processes as</small>
            </div>

            <div className="form-group">
              <label>Group</label>
              <input
                type="text"
                value={config.group}
                onChange={(e) => handleInputChange('group', e.target.value)}
                placeholder="Group ID or name (optional)"
              />
              <small>Primary group for container processes</small>
            </div>
          </div>
        )}
        
        {activeTab === 'resources' && (
          <div className="tab-content">
            <div className="form-group">
              <label>CPU Limit</label>
              <input
                type="text"
                value={config.cpu_limit}
                onChange={(e) => handleInputChange('cpu_limit', e.target.value)}
                placeholder="e.g., 0.5, 1.0, 2 (CPU cores)"
              />
              <small>Maximum CPU cores this container can use</small>
            </div>

            <div className="form-group">
              <label>Memory Limit</label>
              <input
                type="text"
                value={config.memory_limit}
                onChange={(e) => handleInputChange('memory_limit', e.target.value)}
                placeholder="e.g., 512m, 1g, 2g"
              />
              <small>Maximum memory this container can use</small>
            </div>

            <div className="resource-info">
              <h4>💡 Resource Guidelines</h4>
              <ul>
                <li><strong>Network OS containers</strong>: Usually need 1-2 CPU cores and 1-4GB RAM</li>
                <li><strong>Linux containers</strong>: Typically 0.5 CPU cores and 256-512MB RAM</li>
                <li><strong>Simulation containers</strong>: May require more resources for complex topologies</li>
                <li><strong>Leave empty</strong> to use container defaults</li>
              </ul>
            </div>

            {kindTemplate && kindTemplate.notes && (
              <div className="kind-notes">
                <h4>📋 Notes for {config.kind}</h4>
                <ul>
                  {kindTemplate.notes.map((note, index) => (
                    <li key={index}>{note}</li>
                  ))}
                </ul>
              </div>
            )}

            {kindTemplate && kindTemplate.documentation && (
              <div className="documentation-link">
                <h4>📚 Documentation</h4>
                <a 
                  href={kindTemplate.documentation} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="doc-link"
                >
                  {kindTemplate.documentation}
                </a>
              </div>
            )}
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