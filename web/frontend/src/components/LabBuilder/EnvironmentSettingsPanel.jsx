import { useState, useEffect } from 'react'
import './EnvironmentSettingsPanel.css'

function EnvironmentSettingsPanel({ environmentConfig, onUpdate, onClose }) {
  const [config, setConfig] = useState({
    mgmt: {
      network: 'mgmt',
      ipv4_subnet: '172.20.20.0/24',
      ipv6_subnet: '',
      bridge: 'br-mgmt',
      mtu: 1500,
      external_access: true
    },
    deployment: {
      runtime: 'docker',
      host_requirements: {
        min_memory: '4GB',
        min_cpu: '2',
        min_disk: '10GB',
        architecture: 'x86_64'
      },
      machine_type: 'standard',
      region: 'local',
      auto_remove: true,
      debug: false
    },
    dns: {
      servers: ['8.8.8.8', '8.8.4.4'],
      search_domains: [],
      custom_domains: []
    },
    ntp: {
      servers: ['pool.ntp.org'],
      timezone: 'UTC'
    },
    secrets: {
      env_file: '',
      vault_integration: false,
      auto_generate_passwords: true
    },
    address_pools: {
      ipv4_pools: [
        { name: 'mgmt', subnet: '172.20.20.0/24', start: '172.20.20.10', end: '172.20.20.100' },
        { name: 'data', subnet: '192.168.1.0/24', start: '192.168.1.10', end: '192.168.1.100' }
      ],
      ipv6_pools: []
    },
    security: {
      container_security: 'restricted',
      network_isolation: true,
      privileged_allowed: false,
      sysctls_allowed: [],
      capabilities_allowed: ['NET_ADMIN', 'SYS_ADMIN']
    },
    ...environmentConfig
  })

  const [activeTab, setActiveTab] = useState('management')
  const [newDnsServer, setNewDnsServer] = useState('')
  const [newNtpServer, setNewNtpServer] = useState('')
  const [newSearchDomain, setNewSearchDomain] = useState('')
  const [newCustomDomain, setNewCustomDomain] = useState('')
  const [newAddressPool, setNewAddressPool] = useState({
    name: '',
    subnet: '',
    start: '',
    end: '',
    type: 'ipv4'
  })
  const [newCapability, setNewCapability] = useState('')
  const [newSysctl, setNewSysctl] = useState('')

  useEffect(() => {
    setConfig({
      mgmt: {
        network: 'mgmt',
        ipv4_subnet: '172.20.20.0/24',
        ipv6_subnet: '',
        bridge: 'br-mgmt',
        mtu: 1500,
        external_access: true
      },
      deployment: {
        runtime: 'docker',
        host_requirements: {
          min_memory: '4GB',
          min_cpu: '2',
          min_disk: '10GB',
          architecture: 'x86_64'
        },
        machine_type: 'standard',
        region: 'local',
        auto_remove: true,
        debug: false
      },
      dns: {
        servers: ['8.8.8.8', '8.8.4.4'],
        search_domains: [],
        custom_domains: []
      },
      ntp: {
        servers: ['pool.ntp.org'],
        timezone: 'UTC'
      },
      secrets: {
        env_file: '',
        vault_integration: false,
        auto_generate_passwords: true
      },
      address_pools: {
        ipv4_pools: [
          { name: 'mgmt', subnet: '172.20.20.0/24', start: '172.20.20.10', end: '172.20.20.100' },
          { name: 'data', subnet: '192.168.1.0/24', start: '192.168.1.10', end: '192.168.1.100' }
        ],
        ipv6_pools: []
      },
      security: {
        container_security: 'restricted',
        network_isolation: true,
        privileged_allowed: false,
        sysctls_allowed: [],
        capabilities_allowed: ['NET_ADMIN', 'SYS_ADMIN']
      },
      ...environmentConfig
    })
  }, [environmentConfig])

  const handleInputChange = (section, field, value) => {
    const newConfig = {
      ...config,
      [section]: {
        ...config[section],
        [field]: value
      }
    }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const handleNestedInputChange = (section, subsection, field, value) => {
    const newConfig = {
      ...config,
      [section]: {
        ...config[section],
        [subsection]: {
          ...config[section][subsection],
          [field]: value
        }
      }
    }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const addToArray = (section, field, value) => {
    if (!value || config[section][field].includes(value)) return
    
    const newArray = [...config[section][field], value]
    handleInputChange(section, field, newArray)
  }

  const removeFromArray = (section, field, index) => {
    const newArray = config[section][field].filter((_, i) => i !== index)
    handleInputChange(section, field, newArray)
  }

  const addAddressPool = () => {
    if (!newAddressPool.name || !newAddressPool.subnet) return
    
    const poolsField = newAddressPool.type === 'ipv6' ? 'ipv6_pools' : 'ipv4_pools'
    const newPools = [...config.address_pools[poolsField], { ...newAddressPool }]
    
    const newConfig = {
      ...config,
      address_pools: {
        ...config.address_pools,
        [poolsField]: newPools
      }
    }
    setConfig(newConfig)
    onUpdate(newConfig)
    setNewAddressPool({ name: '', subnet: '', start: '', end: '', type: 'ipv4' })
  }

  const removeAddressPool = (type, index) => {
    const poolsField = type === 'ipv6' ? 'ipv6_pools' : 'ipv4_pools'
    const newPools = config.address_pools[poolsField].filter((_, i) => i !== index)
    
    const newConfig = {
      ...config,
      address_pools: {
        ...config.address_pools,
        [poolsField]: newPools
      }
    }
    setConfig(newConfig)
    onUpdate(newConfig)
  }

  const runtimeOptions = ['docker', 'podman', 'containerd', 'cri-o']
  const machineTypes = ['standard', 'high-memory', 'high-cpu', 'gpu-enabled', 'arm64']
  const architectures = ['x86_64', 'arm64', 'armv7l']
  const securityLevels = ['permissive', 'restricted', 'strict']
  const commonCapabilities = [
    'NET_ADMIN', 'SYS_ADMIN', 'NET_RAW', 'NET_BIND_SERVICE', 
    'SYS_TIME', 'SYS_PTRACE', 'IPC_LOCK', 'MKNOD'
  ]
  const commonSysctls = [
    'net.ipv4.ip_forward', 'net.ipv6.conf.all.forwarding',
    'net.bridge.bridge-nf-call-iptables', 'net.ipv4.conf.all.rp_filter'
  ]

  return (
    <div className="environment-settings-panel">
      <div className="settings-header">
        <h3>🌍 Environment Settings</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="settings-tabs">
        <button 
          className={`tab ${activeTab === 'management' ? 'active' : ''}`}
          onClick={() => setActiveTab('management')}
        >
          Management
        </button>
        <button 
          className={`tab ${activeTab === 'deployment' ? 'active' : ''}`}
          onClick={() => setActiveTab('deployment')}
        >
          Deployment
        </button>
        <button 
          className={`tab ${activeTab === 'networking' ? 'active' : ''}`}
          onClick={() => setActiveTab('networking')}
        >
          Networking
        </button>
        <button 
          className={`tab ${activeTab === 'services' ? 'active' : ''}`}
          onClick={() => setActiveTab('services')}
        >
          Services
        </button>
        <button 
          className={`tab ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          Security
        </button>
      </div>
      
      <div className="settings-content">
        {activeTab === 'management' && (
          <div className="tab-content">
            <h4>Management Network Configuration</h4>
            
            <div className="form-group">
              <label>Management Network Name</label>
              <input
                type="text"
                value={config.mgmt.network}
                onChange={(e) => handleInputChange('mgmt', 'network', e.target.value)}
                placeholder="mgmt"
              />
              <small>Name of the management network bridge</small>
            </div>
            
            <div className="form-group">
              <label>IPv4 Subnet</label>
              <input
                type="text"
                value={config.mgmt.ipv4_subnet}
                onChange={(e) => handleInputChange('mgmt', 'ipv4_subnet', e.target.value)}
                placeholder="172.20.20.0/24"
              />
            </div>
            
            <div className="form-group">
              <label>IPv6 Subnet (Optional)</label>
              <input
                type="text"
                value={config.mgmt.ipv6_subnet}
                onChange={(e) => handleInputChange('mgmt', 'ipv6_subnet', e.target.value)}
                placeholder="2001:db8::/64"
              />
            </div>
            
            <div className="form-group">
              <label>Bridge Name</label>
              <input
                type="text"
                value={config.mgmt.bridge}
                onChange={(e) => handleInputChange('mgmt', 'bridge', e.target.value)}
                placeholder="br-mgmt"
              />
            </div>
            
            <div className="form-group">
              <label>MTU Size</label>
              <input
                type="number"
                value={config.mgmt.mtu}
                onChange={(e) => handleInputChange('mgmt', 'mtu', parseInt(e.target.value))}
                min="1280"
                max="9000"
              />
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.mgmt.external_access}
                  onChange={(e) => handleInputChange('mgmt', 'external_access', e.target.checked)}
                />
                <span>Enable External Access</span>
              </label>
              <small>Allow management network access from outside the lab host</small>
            </div>
          </div>
        )}
        
        {activeTab === 'deployment' && (
          <div className="tab-content">
            <h4>Deployment Configuration</h4>
            
            <div className="form-group">
              <label>Container Runtime</label>
              <select
                value={config.deployment.runtime}
                onChange={(e) => handleInputChange('deployment', 'runtime', e.target.value)}
              >
                {runtimeOptions.map(runtime => (
                  <option key={runtime} value={runtime}>{runtime}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Machine Type</label>
              <select
                value={config.deployment.machine_type}
                onChange={(e) => handleInputChange('deployment', 'machine_type', e.target.value)}
              >
                {machineTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <h4>Host Requirements</h4>
            
            <div className="form-group">
              <label>Minimum Memory</label>
              <input
                type="text"
                value={config.deployment.host_requirements.min_memory}
                onChange={(e) => handleNestedInputChange('deployment', 'host_requirements', 'min_memory', e.target.value)}
                placeholder="4GB"
              />
            </div>
            
            <div className="form-group">
              <label>Minimum CPU Cores</label>
              <input
                type="text"
                value={config.deployment.host_requirements.min_cpu}
                onChange={(e) => handleNestedInputChange('deployment', 'host_requirements', 'min_cpu', e.target.value)}
                placeholder="2"
              />
            </div>
            
            <div className="form-group">
              <label>Minimum Disk Space</label>
              <input
                type="text"
                value={config.deployment.host_requirements.min_disk}
                onChange={(e) => handleNestedInputChange('deployment', 'host_requirements', 'min_disk', e.target.value)}
                placeholder="10GB"
              />
            </div>
            
            <div className="form-group">
              <label>Architecture</label>
              <select
                value={config.deployment.host_requirements.architecture}
                onChange={(e) => handleNestedInputChange('deployment', 'host_requirements', 'architecture', e.target.value)}
              >
                {architectures.map(arch => (
                  <option key={arch} value={arch}>{arch}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.deployment.auto_remove}
                  onChange={(e) => handleInputChange('deployment', 'auto_remove', e.target.checked)}
                />
                <span>Auto-remove containers on stop</span>
              </label>
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.deployment.debug}
                  onChange={(e) => handleInputChange('deployment', 'debug', e.target.checked)}
                />
                <span>Enable debug mode</span>
              </label>
            </div>
          </div>
        )}
        
        {activeTab === 'networking' && (
          <div className="tab-content">
            <h4>Address Pools</h4>
            
            <div className="form-group">
              <label>Add New Address Pool</label>
              <div className="address-pool-inputs">
                <input
                  type="text"
                  value={newAddressPool.name}
                  onChange={(e) => setNewAddressPool({...newAddressPool, name: e.target.value})}
                  placeholder="Pool name"
                />
                <select
                  value={newAddressPool.type}
                  onChange={(e) => setNewAddressPool({...newAddressPool, type: e.target.value})}
                >
                  <option value="ipv4">IPv4</option>
                  <option value="ipv6">IPv6</option>
                </select>
                <input
                  type="text"
                  value={newAddressPool.subnet}
                  onChange={(e) => setNewAddressPool({...newAddressPool, subnet: e.target.value})}
                  placeholder="Subnet (e.g., 192.168.1.0/24)"
                />
                <input
                  type="text"
                  value={newAddressPool.start}
                  onChange={(e) => setNewAddressPool({...newAddressPool, start: e.target.value})}
                  placeholder="Start IP"
                />
                <input
                  type="text"
                  value={newAddressPool.end}
                  onChange={(e) => setNewAddressPool({...newAddressPool, end: e.target.value})}
                  placeholder="End IP"
                />
                <button onClick={addAddressPool}>Add Pool</button>
              </div>
            </div>
            
            <div className="address-pools-list">
              <h5>IPv4 Pools</h5>
              {config.address_pools.ipv4_pools.map((pool, index) => (
                <div key={index} className="pool-item">
                  <span><strong>{pool.name}</strong>: {pool.subnet} ({pool.start} - {pool.end})</span>
                  <button onClick={() => removeAddressPool('ipv4', index)}>Remove</button>
                </div>
              ))}
              
              <h5>IPv6 Pools</h5>
              {config.address_pools.ipv6_pools.map((pool, index) => (
                <div key={index} className="pool-item">
                  <span><strong>{pool.name}</strong>: {pool.subnet} ({pool.start} - {pool.end})</span>
                  <button onClick={() => removeAddressPool('ipv6', index)}>Remove</button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {activeTab === 'services' && (
          <div className="tab-content">
            <h4>DNS Configuration</h4>
            
            <div className="form-group">
              <label>DNS Servers</label>
              <div className="list-input">
                <div className="input-with-button">
                  <input
                    type="text"
                    value={newDnsServer}
                    onChange={(e) => setNewDnsServer(e.target.value)}
                    placeholder="DNS server IP"
                  />
                  <button onClick={() => {
                    addToArray('dns', 'servers', newDnsServer)
                    setNewDnsServer('')
                  }}>Add</button>
                </div>
                <div className="list-items">
                  {config.dns.servers.map((server, index) => (
                    <div key={index} className="list-item">
                      <span>{server}</span>
                      <button onClick={() => removeFromArray('dns', 'servers', index)}>Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="form-group">
              <label>Search Domains</label>
              <div className="list-input">
                <div className="input-with-button">
                  <input
                    type="text"
                    value={newSearchDomain}
                    onChange={(e) => setNewSearchDomain(e.target.value)}
                    placeholder="Search domain"
                  />
                  <button onClick={() => {
                    addToArray('dns', 'search_domains', newSearchDomain)
                    setNewSearchDomain('')
                  }}>Add</button>
                </div>
                <div className="list-items">
                  {config.dns.search_domains.map((domain, index) => (
                    <div key={index} className="list-item">
                      <span>{domain}</span>
                      <button onClick={() => removeFromArray('dns', 'search_domains', index)}>Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <h4>NTP Configuration</h4>
            
            <div className="form-group">
              <label>NTP Servers</label>
              <div className="list-input">
                <div className="input-with-button">
                  <input
                    type="text"
                    value={newNtpServer}
                    onChange={(e) => setNewNtpServer(e.target.value)}
                    placeholder="NTP server"
                  />
                  <button onClick={() => {
                    addToArray('ntp', 'servers', newNtpServer)
                    setNewNtpServer('')
                  }}>Add</button>
                </div>
                <div className="list-items">
                  {config.ntp.servers.map((server, index) => (
                    <div key={index} className="list-item">
                      <span>{server}</span>
                      <button onClick={() => removeFromArray('ntp', 'servers', index)}>Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="form-group">
              <label>Timezone</label>
              <input
                type="text"
                value={config.ntp.timezone}
                onChange={(e) => handleInputChange('ntp', 'timezone', e.target.value)}
                placeholder="UTC"
              />
            </div>
            
            <h4>Secrets Management</h4>
            
            <div className="form-group">
              <label>Environment File</label>
              <input
                type="text"
                value={config.secrets.env_file}
                onChange={(e) => handleInputChange('secrets', 'env_file', e.target.value)}
                placeholder="Path to .env file"
              />
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.secrets.vault_integration}
                  onChange={(e) => handleInputChange('secrets', 'vault_integration', e.target.checked)}
                />
                <span>Enable HashiCorp Vault integration</span>
              </label>
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.secrets.auto_generate_passwords}
                  onChange={(e) => handleInputChange('secrets', 'auto_generate_passwords', e.target.checked)}
                />
                <span>Auto-generate passwords for network devices</span>
              </label>
            </div>
          </div>
        )}
        
        {activeTab === 'security' && (
          <div className="tab-content">
            <h4>Container Security</h4>
            
            <div className="form-group">
              <label>Security Level</label>
              <select
                value={config.security.container_security}
                onChange={(e) => handleInputChange('security', 'container_security', e.target.value)}
              >
                {securityLevels.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
              <small>
                permissive: Allow most capabilities and sysctls<br/>
                restricted: Only allow essential capabilities<br/>
                strict: Minimal capabilities, enhanced isolation
              </small>
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.security.network_isolation}
                  onChange={(e) => handleInputChange('security', 'network_isolation', e.target.checked)}
                />
                <span>Enable network isolation between containers</span>
              </label>
            </div>
            
            <div className="form-group">
              <label className="checkbox-option">
                <input
                  type="checkbox"
                  checked={config.security.privileged_allowed}
                  onChange={(e) => handleInputChange('security', 'privileged_allowed', e.target.checked)}
                />
                <span>Allow privileged containers</span>
              </label>
              <small>Some network OS containers require privileged mode</small>
            </div>
            
            <div className="form-group">
              <label>Allowed Capabilities</label>
              <div className="capabilities-selector">
                <div className="common-capabilities">
                  {commonCapabilities.map(cap => (
                    <button
                      key={cap}
                      className={`capability-btn ${config.security.capabilities_allowed.includes(cap) ? 'selected' : ''}`}
                      onClick={() => {
                        const newCaps = config.security.capabilities_allowed.includes(cap)
                          ? config.security.capabilities_allowed.filter(c => c !== cap)
                          : [...config.security.capabilities_allowed, cap]
                        handleInputChange('security', 'capabilities_allowed', newCaps)
                      }}
                    >
                      {cap}
                    </button>
                  ))}
                </div>
                <div className="custom-capability">
                  <input
                    type="text"
                    value={newCapability}
                    onChange={(e) => setNewCapability(e.target.value)}
                    placeholder="Custom capability"
                  />
                  <button onClick={() => {
                    if (newCapability && !config.security.capabilities_allowed.includes(newCapability)) {
                      handleInputChange('security', 'capabilities_allowed', [...config.security.capabilities_allowed, newCapability])
                      setNewCapability('')
                    }
                  }}>Add</button>
                </div>
              </div>
            </div>
            
            <div className="form-group">
              <label>Allowed Sysctls</label>
              <div className="sysctls-selector">
                <div className="common-sysctls">
                  {commonSysctls.map(sysctl => (
                    <button
                      key={sysctl}
                      className={`sysctl-btn ${config.security.sysctls_allowed.includes(sysctl) ? 'selected' : ''}`}
                      onClick={() => {
                        const newSysctls = config.security.sysctls_allowed.includes(sysctl)
                          ? config.security.sysctls_allowed.filter(s => s !== sysctl)
                          : [...config.security.sysctls_allowed, sysctl]
                        handleInputChange('security', 'sysctls_allowed', newSysctls)
                      }}
                    >
                      {sysctl}
                    </button>
                  ))}
                </div>
                <div className="custom-sysctl">
                  <input
                    type="text"
                    value={newSysctl}
                    onChange={(e) => setNewSysctl(e.target.value)}
                    placeholder="Custom sysctl"
                  />
                  <button onClick={() => {
                    if (newSysctl && !config.security.sysctls_allowed.includes(newSysctl)) {
                      handleInputChange('security', 'sysctls_allowed', [...config.security.sysctls_allowed, newSysctl])
                      setNewSysctl('')
                    }
                  }}>Add</button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="settings-footer">
        <button onClick={onClose} className="btn-secondary">Close</button>
        <button 
          onClick={() => console.log('Environment settings:', config)}
          className="btn-primary"
        >
          Apply Settings
        </button>
      </div>
    </div>
  )
}

export default EnvironmentSettingsPanel