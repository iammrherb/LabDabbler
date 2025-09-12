import { useState, useEffect } from 'react'
import './LinkConfigPanel.css'

function LinkConfigPanel({ link, nodes, onUpdate, onClose, onDelete }) {
  const [config, setConfig] = useState({
    id: '',
    name: '',
    type: 'ethernet',
    endpoints: [
      { node: '', interface: 'eth0', ip: '', vlan: '', mode: 'access' },
      { node: '', interface: 'eth0', ip: '', vlan: '', mode: 'access' }
    ],
    properties: {
      bandwidth: '',
      mtu: '1500',
      delay: '0ms',
      jitter: '0ms',
      loss: '0%',
      duplex: 'full',
      auto_negotiate: true
    },
    vlan_config: {
      enabled: false,
      native_vlan: '1',
      allowed_vlans: '',
      encapsulation: '802.1q'
    },
    advanced: {
      mac_learning: true,
      stp_enabled: false,
      storm_control: false,
      flow_control: false
    },
    ...link
  })

  const [activeTab, setActiveTab] = useState('general')
  const [validationErrors, setValidationErrors] = useState([])

  useEffect(() => {
    setConfig({
      id: '',
      name: '',
      type: 'ethernet',
      endpoints: [
        { node: '', interface: 'eth0', ip: '', vlan: '', mode: 'access' },
        { node: '', interface: 'eth0', ip: '', vlan: '', mode: 'access' }
      ],
      properties: {
        bandwidth: '',
        mtu: '1500',
        delay: '0ms',
        jitter: '0ms',
        loss: '0%',
        duplex: 'full',
        auto_negotiate: true
      },
      vlan_config: {
        enabled: false,
        native_vlan: '1',
        allowed_vlans: '',
        encapsulation: '802.1q'
      },
      advanced: {
        mac_learning: true,
        stp_enabled: false,
        storm_control: false,
        flow_control: false
      },
      ...link
    })
  }, [link])

  const handleInputChange = (field, value) => {
    const newConfig = { ...config, [field]: value }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const handleNestedChange = (section, field, value) => {
    const newSection = { ...config[section], [field]: value }
    const newConfig = { ...config, [section]: newSection }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const handleEndpointChange = (index, field, value) => {
    const newEndpoints = [...config.endpoints]
    newEndpoints[index] = { ...newEndpoints[index], [field]: value }
    const newConfig = { ...config, endpoints: newEndpoints }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const generateInterfaceOptions = (nodeId) => {
    const node = nodes[nodeId]
    if (!node) return ['eth0']
    
    // Generate interface options based on node kind
    const interfaceCount = getNodeInterfaceCount(node.kind)
    const interfaces = []
    
    for (let i = 0; i < interfaceCount; i++) {
      interfaces.push(`eth${i}`)
    }
    
    // Add special interfaces for certain kinds
    if (node.kind === 'bridge' || node.kind === 'ovs') {
      interfaces.push('br0', 'mgmt')
    }
    
    if (node.kind === 'srl' || node.kind === 'sros') {
      interfaces.push('mgmt0', 'system0')
    }
    
    return interfaces
  }

  const getNodeInterfaceCount = (kind) => {
    const interfaceCounts = {
      'srl': 48,
      'sros': 48,
      'ceos': 48,
      'vr_vmx': 12,
      'vr_csr': 8,
      'vr_xrv9k': 48,
      'fortinet_fortigate': 24,
      'vr_pan': 8,
      'linux': 4,
      'host': 2,
      'bridge': 32,
      'ovs': 32
    }
    return interfaceCounts[kind] || 8
  }

  const getLinkTypeInfo = (type) => {
    const types = {
      'ethernet': {
        description: 'Standard Ethernet Connection',
        icon: '🔗',
        defaultBandwidth: '1Gbps',
        supportedVlans: true
      },
      'fiber': {
        description: 'Fiber Optic Connection',
        icon: '💫',
        defaultBandwidth: '10Gbps',
        supportedVlans: true
      },
      'serial': {
        description: 'Serial Point-to-Point',
        icon: '📡',
        defaultBandwidth: '1.544Mbps',
        supportedVlans: false
      },
      'tunnel': {
        description: 'Overlay Tunnel',
        icon: '🚇',
        defaultBandwidth: '1Gbps',
        supportedVlans: false
      },
      'lag': {
        description: 'Link Aggregation Group',
        icon: '🔀',
        defaultBandwidth: '10Gbps',
        supportedVlans: true
      },
      'management': {
        description: 'Management Interface',
        icon: '⚙️',
        defaultBandwidth: '100Mbps',
        supportedVlans: false
      }
    }
    return types[type] || types['ethernet']
  }

  const validateConfiguration = () => {
    const errors = []
    
    // Check if both endpoints are configured
    if (!config.endpoints[0].node || !config.endpoints[1].node) {
      errors.push('Both link endpoints must be configured')
    }
    
    // Check if connecting to the same node
    if (config.endpoints[0].node === config.endpoints[1].node) {
      errors.push('Cannot connect a node to itself')
    }
    
    // Check for duplicate interfaces on the same node
    const ep1 = config.endpoints[0]
    const ep2 = config.endpoints[1]
    if (ep1.node === ep2.node && ep1.interface === ep2.interface) {
      errors.push('Cannot use the same interface twice on the same node')
    }
    
    // Validate VLAN configuration
    if (config.vlan_config.enabled) {
      const nativeVlan = parseInt(config.vlan_config.native_vlan)
      if (isNaN(nativeVlan) || nativeVlan < 1 || nativeVlan > 4094) {
        errors.push('Native VLAN must be between 1 and 4094')
      }
      
      if (config.vlan_config.allowed_vlans) {
        const vlanPattern = /^(\d+(-\d+)?,?)*$/
        if (!vlanPattern.test(config.vlan_config.allowed_vlans.replace(/\s/g, ''))) {
          errors.push('Invalid VLAN range format (use: 1,2,10-20,30)')
        }
      }
    }
    
    // Validate bandwidth format
    if (config.properties.bandwidth) {
      const bandwidthPattern = /^\d+(\.\d+)?(Mbps|Gbps|Kbps)$/i
      if (!bandwidthPattern.test(config.properties.bandwidth)) {
        errors.push('Invalid bandwidth format (use: 100Mbps, 1Gbps, etc.)')
      }
    }
    
    // Validate MTU
    const mtu = parseInt(config.properties.mtu)
    if (isNaN(mtu) || mtu < 64 || mtu > 9216) {
      errors.push('MTU must be between 64 and 9216 bytes')
    }
    
    setValidationErrors(errors)
    return errors.length === 0
  }

  const linkTypeInfo = getLinkTypeInfo(config.type)

  return (
    <div className="link-config-panel">
      <div className="config-header">
        <h3>🔗 Link Configuration</h3>
        <div className="header-actions">
          {onDelete && (
            <button className="delete-button" onClick={onDelete} title="Delete Link">
              🗑️
            </button>
          )}
          <button className="close-button" onClick={onClose}>×</button>
        </div>
      </div>
      
      <div className="config-tabs">
        <button 
          className={`tab ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
        <button 
          className={`tab ${activeTab === 'endpoints' ? 'active' : ''}`}
          onClick={() => setActiveTab('endpoints')}
        >
          Endpoints
        </button>
        <button 
          className={`tab ${activeTab === 'vlan' ? 'active' : ''}`}
          onClick={() => setActiveTab('vlan')}
        >
          VLAN
        </button>
        <button 
          className={`tab ${activeTab === 'properties' ? 'active' : ''}`}
          onClick={() => setActiveTab('properties')}
        >
          Properties
        </button>
        <button 
          className={`tab ${activeTab === 'advanced' ? 'active' : ''}`}
          onClick={() => setActiveTab('advanced')}
        >
          Advanced
        </button>
      </div>
      
      <div className="config-content">
        {activeTab === 'general' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Link Name</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter link name (optional)"
              />
              <small>Human-readable name for this connection</small>
            </div>
            
            <div className="form-group">
              <label>Link Type</label>
              <select
                value={config.type}
                onChange={(e) => handleInputChange('type', e.target.value)}
              >
                <option value="ethernet">Ethernet</option>
                <option value="fiber">Fiber Optic</option>
                <option value="serial">Serial</option>
                <option value="tunnel">Tunnel/Overlay</option>
                <option value="lag">Link Aggregation (LAG)</option>
                <option value="management">Management</option>
              </select>
              <div className="link-type-info">
                <span className="type-icon">{linkTypeInfo.icon}</span>
                <span className="type-description">{linkTypeInfo.description}</span>
                <small>Default: {linkTypeInfo.defaultBandwidth}</small>
              </div>
            </div>
            
            <div className="link-summary">
              <h4>Connection Summary</h4>
              <div className="connection-display">
                <div className="endpoint">
                  <strong>{config.endpoints[0].node || 'Node A'}</strong>
                  <small>{config.endpoints[0].interface}</small>
                </div>
                <div className="link-arrow">
                  {linkTypeInfo.icon} ↔️ {linkTypeInfo.icon}
                </div>
                <div className="endpoint">
                  <strong>{config.endpoints[1].node || 'Node B'}</strong>
                  <small>{config.endpoints[1].interface}</small>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'endpoints' && (
          <div className="tab-content">
            {config.endpoints.map((endpoint, index) => (
              <div key={index} className="endpoint-config">
                <h4>Endpoint {index + 1}</h4>
                
                <div className="form-group">
                  <label>Node</label>
                  <select
                    value={endpoint.node}
                    onChange={(e) => handleEndpointChange(index, 'node', e.target.value)}
                  >
                    <option value="">Select node...</option>
                    {Object.entries(nodes).map(([nodeId, node]) => (
                      <option key={nodeId} value={nodeId}>
                        {node.name} ({node.kind})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Interface</label>
                  <select
                    value={endpoint.interface}
                    onChange={(e) => handleEndpointChange(index, 'interface', e.target.value)}
                    disabled={!endpoint.node}
                  >
                    {generateInterfaceOptions(endpoint.node).map(iface => (
                      <option key={iface} value={iface}>{iface}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>IP Address</label>
                  <input
                    type="text"
                    value={endpoint.ip}
                    onChange={(e) => handleEndpointChange(index, 'ip', e.target.value)}
                    placeholder="192.168.1.1/24 (optional)"
                  />
                  <small>IP address for this interface (optional)</small>
                </div>
                
                {linkTypeInfo.supportedVlans && (
                  <div className="form-group">
                    <label>Interface Mode</label>
                    <select
                      value={endpoint.mode}
                      onChange={(e) => handleEndpointChange(index, 'mode', e.target.value)}
                    >
                      <option value="access">Access</option>
                      <option value="trunk">Trunk</option>
                      <option value="hybrid">Hybrid</option>
                    </select>
                  </div>
                )}
                
                {endpoint.mode === 'access' && linkTypeInfo.supportedVlans && (
                  <div className="form-group">
                    <label>Access VLAN</label>
                    <input
                      type="number"
                      value={endpoint.vlan}
                      onChange={(e) => handleEndpointChange(index, 'vlan', e.target.value)}
                      placeholder="1"
                      min="1"
                      max="4094"
                    />
                    <small>VLAN ID for access mode</small>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'vlan' && (
          <div className="tab-content">
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.vlan_config.enabled}
                  onChange={(e) => handleNestedChange('vlan_config', 'enabled', e.target.checked)}
                  disabled={!linkTypeInfo.supportedVlans}
                />
                Enable VLAN Configuration
              </label>
              {!linkTypeInfo.supportedVlans && (
                <small>VLAN configuration not supported for {config.type} links</small>
              )}
            </div>
            
            {config.vlan_config.enabled && linkTypeInfo.supportedVlans && (
              <>
                <div className="form-group">
                  <label>Native VLAN</label>
                  <input
                    type="number"
                    value={config.vlan_config.native_vlan}
                    onChange={(e) => handleNestedChange('vlan_config', 'native_vlan', e.target.value)}
                    min="1"
                    max="4094"
                  />
                  <small>Default VLAN for untagged traffic</small>
                </div>
                
                <div className="form-group">
                  <label>Allowed VLANs</label>
                  <input
                    type="text"
                    value={config.vlan_config.allowed_vlans}
                    onChange={(e) => handleNestedChange('vlan_config', 'allowed_vlans', e.target.value)}
                    placeholder="1,10,20-30,100-200"
                  />
                  <small>VLAN ranges (e.g., 1,10,20-30,100-200)</small>
                </div>
                
                <div className="form-group">
                  <label>Encapsulation</label>
                  <select
                    value={config.vlan_config.encapsulation}
                    onChange={(e) => handleNestedChange('vlan_config', 'encapsulation', e.target.value)}
                  >
                    <option value="802.1q">802.1Q</option>
                    <option value="802.1ad">802.1ad (QinQ)</option>
                    <option value="isl">ISL (Legacy)</option>
                  </select>
                  <small>VLAN tagging method</small>
                </div>
              </>
            )}
          </div>
        )}
        
        {activeTab === 'properties' && (
          <div className="tab-content">
            <div className="form-group">
              <label>Bandwidth</label>
              <input
                type="text"
                value={config.properties.bandwidth}
                onChange={(e) => handleNestedChange('properties', 'bandwidth', e.target.value)}
                placeholder={linkTypeInfo.defaultBandwidth}
              />
              <small>Link bandwidth (e.g., 100Mbps, 1Gbps, 10Gbps)</small>
            </div>
            
            <div className="form-group">
              <label>MTU (Maximum Transmission Unit)</label>
              <input
                type="number"
                value={config.properties.mtu}
                onChange={(e) => handleNestedChange('properties', 'mtu', e.target.value)}
                min="64"
                max="9216"
              />
              <small>Maximum frame size in bytes (64-9216)</small>
            </div>
            
            <div className="form-group">
              <label>Delay</label>
              <input
                type="text"
                value={config.properties.delay}
                onChange={(e) => handleNestedChange('properties', 'delay', e.target.value)}
                placeholder="0ms"
              />
              <small>Link propagation delay (e.g., 1ms, 10ms)</small>
            </div>
            
            <div className="form-group">
              <label>Jitter</label>
              <input
                type="text"
                value={config.properties.jitter}
                onChange={(e) => handleNestedChange('properties', 'jitter', e.target.value)}
                placeholder="0ms"
              />
              <small>Delay variation (e.g., 0.1ms, 1ms)</small>
            </div>
            
            <div className="form-group">
              <label>Packet Loss</label>
              <input
                type="text"
                value={config.properties.loss}
                onChange={(e) => handleNestedChange('properties', 'loss', e.target.value)}
                placeholder="0%"
              />
              <small>Packet loss percentage (e.g., 0.1%, 1%)</small>
            </div>
            
            <div className="form-group">
              <label>Duplex Mode</label>
              <select
                value={config.properties.duplex}
                onChange={(e) => handleNestedChange('properties', 'duplex', e.target.value)}
              >
                <option value="full">Full Duplex</option>
                <option value="half">Half Duplex</option>
                <option value="auto">Auto Negotiate</option>
              </select>
              <small>Communication mode</small>
            </div>
            
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.properties.auto_negotiate}
                  onChange={(e) => handleNestedChange('properties', 'auto_negotiate', e.target.checked)}
                />
                Auto Negotiation
              </label>
              <small>Automatically negotiate link parameters</small>
            </div>
          </div>
        )}
        
        {activeTab === 'advanced' && (
          <div className="tab-content">
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.advanced.mac_learning}
                  onChange={(e) => handleNestedChange('advanced', 'mac_learning', e.target.checked)}
                />
                MAC Address Learning
              </label>
              <small>Enable MAC address learning on this link</small>
            </div>
            
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.advanced.stp_enabled}
                  onChange={(e) => handleNestedChange('advanced', 'stp_enabled', e.target.checked)}
                />
                Spanning Tree Protocol
              </label>
              <small>Enable STP/RSTP on this link</small>
            </div>
            
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.advanced.storm_control}
                  onChange={(e) => handleNestedChange('advanced', 'storm_control', e.target.checked)}
                />
                Storm Control
              </label>
              <small>Enable broadcast/multicast storm control</small>
            </div>
            
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={config.advanced.flow_control}
                  onChange={(e) => handleNestedChange('advanced', 'flow_control', e.target.checked)}
                />
                Flow Control
              </label>
              <small>Enable IEEE 802.3x flow control</small>
            </div>
            
            <div className="advanced-info">
              <h4>🔧 Advanced Features</h4>
              <p>These settings control low-level link behavior and are typically used for:</p>
              <ul>
                <li><strong>MAC Learning</strong>: Required for switching behavior</li>
                <li><strong>STP</strong>: Prevents network loops in switched environments</li>
                <li><strong>Storm Control</strong>: Protects against broadcast storms</li>
                <li><strong>Flow Control</strong>: Manages traffic flow between devices</li>
              </ul>
            </div>
          </div>
        )}
      </div>
      
      {validationErrors.length > 0 && (
        <div className="validation-issues">
          <h4>⚠️ Configuration Issues</h4>
          <ul>
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="config-footer">
        <div className="config-summary">
          <small>
            Type: <strong>{config.type}</strong> |
            Endpoints: <strong>{config.endpoints.filter(ep => ep.node).length}/2</strong> |
            VLAN: <strong>{config.vlan_config.enabled ? 'Enabled' : 'Disabled'}</strong>
          </small>
        </div>
        <div className="config-actions">
          <button 
            onClick={validateConfiguration}
            className="validate-btn"
          >
            🔍 Validate
          </button>
        </div>
      </div>
    </div>
  )
}

export default LinkConfigPanel