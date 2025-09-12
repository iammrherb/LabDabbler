import { useState } from 'react'
import './CodespacesDeployment.css'
import { getApiBase, api } from '../utils/api'

function CodespacesDeployment({ labData }) {
  const [deploymentStatus, setDeploymentStatus] = useState('')
  const [isDeploying, setIsDeploying] = useState(false)
  const [deploymentProgress, setDeploymentProgress] = useState('')
  const [resultUrls, setResultUrls] = useState({})

  const deployToCodespaces = async () => {
    setIsDeploying(true)
    setDeploymentStatus('')
    setResultUrls({})
    setDeploymentProgress('🔄 Preparing lab for GitHub Codespaces deployment...')
    
    try {
      // Validate lab data
      if (!labData || !labData.name) {
        throw new Error('Lab data is missing or invalid')
      }

      setDeploymentProgress('🔧 Creating GitHub repository...')
      
      const result = await api.post('/api/github/deploy-codespaces', {
        lab_config: labData,
        deployment_type: 'codespaces'
      })
      
      if (result.success) {
        setDeploymentProgress('📦 Configuring containerlab devcontainer...')
        
        // Store the URLs for later use
        setResultUrls({
          github: result.github_url,
          codespaces: result.codespaces_url
        })
        
        setDeploymentStatus(`✅ Lab deployed successfully! Repository: ${result.github_url?.split('/').pop()}`)
        setDeploymentProgress('🚀 Ready to launch in Codespaces!')
        
        // Optionally auto-open Codespaces
        setTimeout(() => {
          if (result.codespaces_url) {
            setDeploymentProgress('🌟 Opening GitHub Codespaces...')
            window.open(result.codespaces_url, '_blank')
          }
        }, 1500)
        
      } else {
        setDeploymentStatus(`❌ Deployment failed: ${result.error || result.message}`)
        setDeploymentProgress('')
      }
    } catch (error) {
      console.error('Codespaces deployment error:', error)
      setDeploymentStatus(`❌ Deployment failed: ${error.message || 'Unable to connect to deployment service'}`)
      setDeploymentProgress('')
    } finally {
      setIsDeploying(false)
    }
  }

  const exportToGitHub = async () => {
    setIsDeploying(true)
    setDeploymentStatus('')
    setResultUrls({})
    setDeploymentProgress('🔄 Preparing lab export to GitHub...')
    
    try {
      // Validate lab data
      if (!labData || !labData.name) {
        throw new Error('Lab data is missing or invalid')
      }

      setDeploymentProgress('🔧 Creating GitHub repository...')
      
      const result = await api.post('/api/github/export-repo', {
        lab_config: labData,
        export_type: 'repository'
      })
      
      if (result.success) {
        setDeploymentProgress('📄 Generating lab documentation...')
        
        // Store the URLs for later use
        setResultUrls({
          github: result.github_url,
          codespaces: result.codespaces_url
        })
        
        setDeploymentStatus(`✅ Repository created successfully! ${result.github_url?.split('/').pop()}`)
        setDeploymentProgress('📂 Ready to view on GitHub!')
        
        // Auto-open GitHub repository
        setTimeout(() => {
          if (result.github_url) {
            window.open(result.github_url, '_blank')
          }
        }, 1500)
        
      } else {
        setDeploymentStatus(`❌ Export failed: ${result.error || result.message}`)
        setDeploymentProgress('')
      }
    } catch (error) {
      console.error('GitHub export error:', error)
      setDeploymentStatus(`❌ Export failed: ${error.message || 'Unable to connect to GitHub service'}`)
      setDeploymentProgress('')
    } finally {
      setIsDeploying(false)
    }
  }

  const quickDeployToCodespaces = (repoUrl) => {
    // Direct Codespaces URL for any GitHub repository
    const codespacesUrl = `https://codespaces.new/${repoUrl.replace('https://github.com/', '')}`
    window.open(codespacesUrl, '_blank')
  }

  return (
    <div className="codespaces-deployment">
      <div className="deployment-header">
        <h2>🚀 Deploy to Cloud</h2>
        <p>Launch your network labs in GitHub Codespaces or export to your own repository</p>
      </div>

      <div className="deployment-actions">
        <div className="deployment-option">
          <div className="option-header">
            <img 
              src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
              alt="GitHub" 
              className="provider-logo"
            />
            <h3>GitHub Codespaces</h3>
          </div>
          <p>Launch a fully-configured development environment in the cloud</p>
          <div className="button-group">
            <button 
              className="deploy-button codespaces-primary"
              onClick={deployToCodespaces}
              disabled={isDeploying}
            >
              {isDeploying ? '⏳ Deploying...' : '🚀 Deploy to Codespaces'}
            </button>
            
            <button 
              className="deploy-button github-secondary"
              onClick={exportToGitHub}
              disabled={isDeploying}
            >
              {isDeploying ? '⏳ Creating...' : '📦 Export to GitHub'}
            </button>
          </div>
        </div>

        <div className="deployment-option">
          <div className="option-header">
            <span className="provider-icon">⚡</span>
            <h3>Quick Deploy</h3>
          </div>
          <p>Deploy popular lab repositories directly</p>
          <div className="quick-deploy-buttons">
            <button 
              className="quick-deploy-button"
              onClick={() => quickDeployToCodespaces('srl-labs/containerlab')}
            >
              📊 SR Linux Labs
            </button>
            <button 
              className="quick-deploy-button"
              onClick={() => quickDeployToCodespaces('hellt/clabs')}
            >
              🌐 Community Labs
            </button>
            <button 
              className="quick-deploy-button"
              onClick={() => quickDeployToCodespaces('PacketAnglers/clab-topos')}
            >
              🎯 PacketAnglers Labs
            </button>
          </div>
        </div>
      </div>

      {deploymentProgress && (
        <div className="deployment-progress">
          <div className="progress-text">{deploymentProgress}</div>
          {isDeploying && (
            <div className="progress-bar">
              <div className="progress-bar-inner"></div>
            </div>
          )}
        </div>
      )}

      {deploymentStatus && (
        <div className={`deployment-status ${deploymentStatus.startsWith('✅') ? 'success' : deploymentStatus.startsWith('❌') ? 'error' : 'info'}`}>
          {deploymentStatus}
        </div>
      )}

      {resultUrls.github && (
        <div className="deployment-results">
          <h4>🎉 Deployment Complete!</h4>
          <div className="result-buttons">
            <button 
              className="result-button github-button"
              onClick={() => window.open(resultUrls.github, '_blank')}
            >
              📂 View Repository
            </button>
            {resultUrls.codespaces && (
              <button 
                className="result-button codespaces-button"
                onClick={() => window.open(resultUrls.codespaces, '_blank')}
              >
                🚀 Launch Codespaces
              </button>
            )}
          </div>
          <div className="quick-start-info">
            <p>Your lab has been exported with:</p>
            <ul>
              <li>✅ Official containerlab devcontainer</li>
              <li>✅ Pre-configured VS Code workspace</li>
              <li>✅ Network automation extensions</li>
              <li>✅ Lab topology and documentation</li>
            </ul>
          </div>
        </div>
      )}

      <div className="deployment-info">
        <h4>💡 What you get with Codespaces deployment:</h4>
        <ul>
          <li>✅ Pre-configured containerlab environment</li>
          <li>✅ All network device containers ready to use</li>
          <li>✅ VS Code with network automation extensions</li>
          <li>✅ Built-in terminal and file management</li>
          <li>✅ 2-4 core machine with 8GB RAM (free tier)</li>
          <li>✅ Persistent storage and port forwarding</li>
        </ul>
      </div>

      <div className="deployment-requirements">
        <h4>📋 Requirements:</h4>
        <p>• GitHub account (free tier includes 120 hours/month)</p>
        <p>• Docker containers will be pulled automatically</p>
        <p>• Network device images may require separate licensing</p>
      </div>
    </div>
  )
}

export default CodespacesDeployment