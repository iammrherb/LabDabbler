import { useState } from 'react'
import './CodespacesDeployment.css'

function CodespacesDeployment({ labData }) {
  const [deploymentStatus, setDeploymentStatus] = useState('')
  const [isDeploying, setIsDeploying] = useState(false)

  // Helper function to get API base URL
  const getApiBase = () => {
    let apiBase = 'http://localhost:8000'
    if (window.location.hostname.includes('replit.dev')) {
      apiBase = `${window.location.protocol}//${window.location.hostname.replace(/^[^.]+/, '8f663c4f-989d-42d5-9d87-278576336cb7-8000-2ajxcvg621drk')}`
    }
    return apiBase
  }

  const deployToCodespaces = async () => {
    setIsDeploying(true)
    setDeploymentStatus('Preparing deployment to GitHub Codespaces...')
    
    try {
      const apiBase = getApiBase()
      const response = await fetch(`${apiBase}/api/github/deploy-codespaces`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          lab_data: labData,
          deployment_type: 'codespaces'
        })
      })

      const result = await response.json()
      
      if (result.success) {
        setDeploymentStatus('✅ Deployment successful! Opening GitHub Codespaces...')
        // Open the Codespaces URL
        if (result.codespaces_url) {
          window.open(result.codespaces_url, '_blank')
        }
      } else {
        setDeploymentStatus(`❌ Deployment failed: ${result.message}`)
      }
    } catch (error) {
      console.error('Codespaces deployment error:', error)
      setDeploymentStatus('❌ Deployment failed: Unable to connect to deployment service')
    } finally {
      setIsDeploying(false)
    }
  }

  const exportToGitHub = async () => {
    setIsDeploying(true)
    setDeploymentStatus('Creating GitHub repository...')
    
    try {
      const apiBase = getApiBase()
      const response = await fetch(`${apiBase}/api/github/export-repo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          lab_data: labData,
          export_type: 'repository'
        })
      })

      const result = await response.json()
      
      if (result.success) {
        setDeploymentStatus('✅ Repository created successfully!')
        // Open the GitHub repository
        if (result.github_url) {
          window.open(result.github_url, '_blank')
        }
      } else {
        setDeploymentStatus(`❌ Export failed: ${result.message}`)
      }
    } catch (error) {
      console.error('GitHub export error:', error)
      setDeploymentStatus('❌ Export failed: Unable to connect to GitHub service')
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

      {deploymentStatus && (
        <div className={`deployment-status ${deploymentStatus.startsWith('✅') ? 'success' : deploymentStatus.startsWith('❌') ? 'error' : 'info'}`}>
          {deploymentStatus}
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