"""
GitHub Integration Service for LabDabbler

Handles GitHub repository operations, GitHub CLI integration, 
and GitHub Codespaces deployment preparation.
"""

import os
import json
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import tempfile
import yaml
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.github_data_dir = data_dir / "github"
        self.github_data_dir.mkdir(parents=True, exist_ok=True)
        
        # GitHub access token will be retrieved from connection
        self.access_token = None
        self.github_api_base = "https://api.github.com"
        
    async def get_access_token(self) -> str:
        """Get GitHub access token from Replit connection"""
        if self.access_token and hasattr(self, '_token_expires_at'):
            if datetime.now() < self._token_expires_at:
                return self.access_token
                
        try:
            hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
            x_replit_token = (
                f"repl {os.environ.get('REPL_IDENTITY')}" 
                if os.environ.get('REPL_IDENTITY') 
                else f"depl {os.environ.get('WEB_REPL_RENEWAL')}"
                if os.environ.get('WEB_REPL_RENEWAL')
                else None
            )
            
            if not x_replit_token or not hostname:
                raise ValueError("GitHub connection not properly configured")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{hostname}/api/v2/connection",
                    params={"include_secrets": "true", "connector_names": "github"},
                    headers={"Accept": "application/json", "X_REPLIT_TOKEN": x_replit_token}
                ) as response:
                    data = await response.json()
                    connection_settings = data.get("items", [{}])[0]
                    
                    self.access_token = (
                        connection_settings.get("settings", {}).get("access_token") or
                        connection_settings.get("settings", {}).get("oauth", {}).get("credentials", {}).get("access_token")
                    )
                    
                    if not self.access_token:
                        raise ValueError("GitHub access token not found in connection")
                    
                    # Set token expiration (assume 1 hour for safety)
                    self._token_expires_at = datetime.now() + timedelta(hours=1)
                    return self.access_token
                    
        except Exception as e:
            logger.error(f"Failed to get GitHub access token: {e}")
            raise
    
    async def get_authenticated_headers(self) -> Dict[str, str]:
        """Get headers with authentication for GitHub API"""
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LabDabbler/1.0"
        }
    
    async def list_user_repositories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List user's GitHub repositories"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                repos = []
                page = 1
                
                while len(repos) < limit:
                    async with session.get(
                        f"{self.github_api_base}/user/repos",
                        headers=headers,
                        params={"page": page, "per_page": min(100, limit - len(repos))}
                    ) as response:
                        if response.status != 200:
                            break
                            
                        page_repos = await response.json()
                        if not page_repos:
                            break
                            
                        repos.extend(page_repos)
                        page += 1
                
                return repos[:limit]
                
        except Exception as e:
            logger.error(f"Failed to list user repositories: {e}")
            return []
    
    async def get_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict[str, Any]]:
        """Get contents of a repository path"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.github_api_base}/repos/{owner}/{repo}/contents/{path}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get repository contents for {owner}/{repo}: {e}")
            return []
    
    async def search_containerlab_files(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Search for .clab.yml files in a repository"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                # Search for .clab.yml files
                url = f"{self.github_api_base}/search/code"
                params = {
                    "q": f"filename:.clab.yml repo:{owner}/{repo}",
                    "per_page": 100
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to search containerlab files in {owner}/{repo}: {e}")
            return []
    
    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Get content of a specific file"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.github_api_base}/repos/{owner}/{repo}/contents/{path}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("encoding") == "base64":
                            import base64
                            return base64.b64decode(data["content"]).decode("utf-8")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get file content for {owner}/{repo}/{path}: {e}")
            return None
    
    async def create_codespaces_config(self, lab_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate devcontainer configuration for GitHub Codespaces"""
        
        # Base devcontainer configuration optimized for containerlab
        devcontainer_config = {
            "name": f"Containerlab Environment - {lab_config.get('name', 'Lab')}",
            "image": "ghcr.io/srl-labs/clab-devcontainer:latest",
            "features": {
                "docker-in-docker": "latest",
                "python": "3.11",
                "node": "20"
            },
            "customizations": {
                "vscode": {
                    "extensions": [
                        "ms-vscode-remote.remote-containers",
                        "ms-python.python",
                        "ms-python.flake8",
                        "ms-python.pylint",
                        "redhat.vscode-yaml",
                        "ms-vscode.vscode-json",
                        "eamodio.gitlens",
                        "GitHub.copilot",
                        "GitHub.copilot-chat",
                        "ms-vscode.azure-repos",
                        "christian-kohler.path-intellisense",
                        "formulahendry.auto-rename-tag",
                        "bradlc.vscode-tailwindcss",
                        "esbenp.prettier-vscode"
                    ],
                    "settings": {
                        "terminal.integrated.defaultProfile.linux": "bash",
                        "python.defaultInterpreterPath": "/usr/local/bin/python",
                        "python.linting.enabled": True,
                        "python.linting.pylintEnabled": True,
                        "editor.formatOnSave": True,
                        "editor.codeActionsOnSave": {
                            "source.organizeImports": True
                        }
                    }
                }
            },
            "postCreateCommand": [
                "bash",
                "-c", 
                "pip install netlab streamlit jinja2 && " +
                "netlab install containerlab && " +
                "git clone https://github.com/vrnetlab/vrnetlab.git /vrnetlab && " +
                "chmod +x /vrnetlab/*/Makefile && " +
                "echo 'Containerlab environment setup complete!'"
            ],
            "forwardPorts": [5000, 8000, 8080],
            "portsAttributes": {
                "5000": {
                    "label": "LabDabbler Frontend",
                    "onAutoForward": "openPreview"
                },
                "8000": {
                    "label": "LabDabbler Backend API",
                    "onAutoForward": "ignore"
                },
                "8080": {
                    "label": "Lab Web Interface",
                    "onAutoForward": "openPreview"
                }
            },
            "remoteEnv": {
                "CONTAINERLAB_VERSION": "latest",
                "NETLAB_VERSION": "latest"
            },
            "mounts": [
                "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
            ]
        }
        
        return devcontainer_config
    
    async def generate_github_workflow(self, lab_config: Dict[str, Any]) -> Dict[str, str]:
        """Generate GitHub Actions workflow for lab automation"""
        
        workflow_name = f"containerlab-{lab_config.get('name', 'lab')}"
        
        workflow_yaml = {
            "name": f"Containerlab Lab - {lab_config.get('name', 'Lab')}",
            "on": {
                "push": {
                    "branches": ["main", "master"]
                },
                "pull_request": {
                    "branches": ["main", "master"]
                },
                "workflow_dispatch": {
                    "inputs": {
                        "action": {
                            "description": "Action to perform",
                            "required": True,
                            "default": "validate",
                            "type": "choice",
                            "options": ["validate", "deploy", "destroy"]
                        }
                    }
                }
            },
            "jobs": {
                "containerlab": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Set up Docker",
                            "uses": "docker/setup-buildx-action@v3"
                        },
                        {
                            "name": "Install Containerlab",
                            "run": "bash -c \"$(curl -sL https://get.containerlab.dev)\""
                        },
                        {
                            "name": "Install Netlab",
                            "run": "pip install netlab"
                        },
                        {
                            "name": "Validate Lab Configuration",
                            "run": f"containerlab inspect --topo {lab_config.get('name', 'lab')}.clab.yml"
                        },
                        {
                            "name": "Deploy Lab (if requested)",
                            "if": "github.event.inputs.action == 'deploy'",
                            "run": f"containerlab deploy --topo {lab_config.get('name', 'lab')}.clab.yml"
                        },
                        {
                            "name": "Run Lab Tests",
                            "if": "github.event.inputs.action == 'deploy'",
                            "run": "echo 'Lab tests would run here'"
                        },
                        {
                            "name": "Destroy Lab",
                            "if": "always() && github.event.inputs.action == 'destroy'",
                            "run": f"containerlab destroy --topo {lab_config.get('name', 'lab')}.clab.yml"
                        }
                    ]
                }
            }
        }
        
        return {
            f".github/workflows/{workflow_name}.yml": yaml.dump(workflow_yaml, default_flow_style=False)
        }
    
    async def create_lab_package(self, lab_config: Dict[str, Any], lab_files: Dict[str, str]) -> Dict[str, Any]:
        """Create a complete lab package for GitHub Codespaces deployment"""
        try:
            # Generate devcontainer config
            devcontainer_config = await self.create_codespaces_config(lab_config)
            
            # Generate GitHub workflow
            github_workflows = await self.generate_github_workflow(lab_config)
            
            # Create README for the lab
            readme_content = f"""# {lab_config.get('name', 'Containerlab Lab')}

{lab_config.get('description', 'A containerlab topology for network simulation and testing.')}

## Quick Start with GitHub Codespaces

1. Click the green "Code" button above
2. Select "Create codespace on main"
3. Wait for the environment to initialize (2-3 minutes)
4. Run the lab:
   ```bash
   containerlab deploy --topo {lab_config.get('name', 'lab')}.clab.yml
   ```

## Lab Overview

- **Nodes**: {len(lab_config.get('topology', {}).get('nodes', {}))}
- **Links**: {len(lab_config.get('topology', {}).get('links', []))}
- **Topology**: {lab_config.get('name', 'lab')}.clab.yml

## Available Tools

- **Containerlab**: Network topology deployment
- **Netlab**: Topology generation and configuration
- **VRNetlab**: Virtual router container builder
- **LabDabbler**: Web-based lab management interface

## Usage

### Deploy the lab
```bash
containerlab deploy --topo {lab_config.get('name', 'lab')}.clab.yml
```

### Check lab status
```bash
containerlab inspect --topo {lab_config.get('name', 'lab')}.clab.yml
```

### Access lab nodes
```bash
containerlab exec --topo {lab_config.get('name', 'lab')}.clab.yml
```

### Destroy the lab
```bash
containerlab destroy --topo {lab_config.get('name', 'lab')}.clab.yml
```

## LabDabbler Web Interface

The lab includes a web-based management interface accessible at http://localhost:5000 after starting:

```bash
cd web/frontend && npm run dev &
cd web/backend && python app.py &
```

---

*This lab was generated by LabDabbler - Master Lab Repository*
"""
            
            # Create package structure
            package = {
                "devcontainer_config": {
                    ".devcontainer/devcontainer.json": json.dumps(devcontainer_config, indent=2)
                },
                "github_workflows": github_workflows,
                "lab_files": lab_files,
                "documentation": {
                    "README.md": readme_content
                },
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "lab_name": lab_config.get("name"),
                    "generator": "LabDabbler",
                    "version": "1.0.0"
                }
            }
            
            return {
                "success": True,
                "package": package,
                "message": f"Lab package created for {lab_config.get('name')}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create lab package: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create lab package"
            }
    
    async def push_lab_to_github(self, repo_owner: str, repo_name: str, lab_package: Dict[str, Any]) -> Dict[str, Any]:
        """Push a lab package to a GitHub repository"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                # Get repository information
                repo_url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}"
                async with session.get(repo_url, headers=headers) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Repository {repo_owner}/{repo_name} not found or inaccessible"
                        }
                
                # Create/update files in the repository
                files_created = []
                for category, files in lab_package["package"].items():
                    if category == "metadata":
                        continue
                        
                    for file_path, content in files.items():
                        # Create or update file via GitHub API
                        file_url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
                        
                        # Check if file exists
                        async with session.get(file_url, headers=headers) as response:
                            file_data = {}
                            if response.status == 200:
                                existing_file = await response.json()
                                file_data["sha"] = existing_file["sha"]
                        
                        # Create/update the file
                        import base64
                        file_data.update({
                            "message": f"Update {file_path} via LabDabbler",
                            "content": base64.b64encode(content.encode()).decode(),
                            "branch": "main"
                        })
                        
                        async with session.put(file_url, headers=headers, json=file_data) as response:
                            if response.status in [200, 201]:
                                files_created.append(file_path)
                            else:
                                logger.error(f"Failed to create/update {file_path}: {response.status}")
                
                return {
                    "success": True,
                    "files_created": files_created,
                    "repository_url": f"https://github.com/{repo_owner}/{repo_name}",
                    "codespaces_url": f"https://github.com/codespaces/new?repo={repo_owner}/{repo_name}",
                    "message": f"Lab deployed to {repo_owner}/{repo_name}"
                }
                
        except Exception as e:
            logger.error(f"Failed to push lab to GitHub: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to deploy lab to GitHub"
            }
    
    async def get_codespaces_status(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Get status of GitHub Codespaces for a repository"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}/codespaces"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "codespaces": data.get("codespaces", []),
                            "total_count": data.get("total_count", 0)
                        }
                    return {
                        "success": False,
                        "error": f"Failed to get Codespaces status: {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get Codespaces status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def deploy_to_codespaces(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy lab data to GitHub Codespaces"""
        try:
            # Extract topology information
            topology = lab_data.get("topology", {})
            repo_owner = lab_data.get("repo_owner", "")
            repo_name = lab_data.get("repo_name", "")
            
            if not repo_owner or not repo_name:
                return {
                    "success": False,
                    "error": "Repository owner and name are required"
                }
            
            # Create lab package with Codespaces configuration
            lab_package = await self.create_lab_package(topology, {})
            if not lab_package["success"]:
                return lab_package
                
            # Push to GitHub repository
            result = await self.push_lab_to_github(repo_owner, repo_name, lab_package)
            
            if result["success"]:
                result["codespaces_url"] = f"https://github.com/codespaces/new?repo={repo_owner}/{repo_name}"
                result["message"] = f"Lab deployed to GitHub Codespaces: {repo_owner}/{repo_name}"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to deploy to Codespaces: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to deploy lab to GitHub Codespaces"
            }
    
    async def export_to_github_repo(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export lab data to a GitHub repository"""
        try:
            # Extract topology information
            topology = lab_data.get("topology", {})
            repo_owner = lab_data.get("repo_owner", "")
            repo_name = lab_data.get("repo_name", "")
            
            if not repo_owner or not repo_name:
                return {
                    "success": False,
                    "error": "Repository owner and name are required"
                }
            
            # Create lab package
            lab_package = await self.create_lab_package(topology, {})
            if not lab_package["success"]:
                return lab_package
                
            # Push to GitHub repository
            result = await self.push_lab_to_github(repo_owner, repo_name, lab_package)
            
            if result["success"]:
                result["message"] = f"Lab exported to GitHub repository: {repo_owner}/{repo_name}"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to export to GitHub repo: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to export lab to GitHub repository"
            }
    
    def get_popular_lab_repositories(self) -> List[Dict[str, Any]]:
        """Get list of popular containerlab repositories for quick deployment"""
        try:
            # Popular containerlab repositories for learning and templates
            popular_repos = [
                {
                    "name": "srl-labs/containerlab",
                    "description": "Official Containerlab repository with examples and documentation",
                    "url": "https://github.com/srl-labs/containerlab",
                    "stars": "2.8k",
                    "category": "Official",
                    "tags": ["containerlab", "networking", "labs"]
                },
                {
                    "name": "hellt/containerlab-labs",
                    "description": "Collection of containerlab topologies and examples",
                    "url": "https://github.com/hellt/containerlab-labs",
                    "stars": "300+",
                    "category": "Community",
                    "tags": ["labs", "examples", "networking"]
                },
                {
                    "name": "learn-srlinux/learn-srlinux",
                    "description": "Nokia SR Linux learning labs using containerlab",
                    "url": "https://github.com/learn-srlinux/learn-srlinux",
                    "stars": "200+",
                    "category": "Vendor",
                    "tags": ["srlinux", "nokia", "tutorials"]
                },
                {
                    "name": "packetanglers/containerlab-topologies",
                    "description": "Various network topologies for containerlab",
                    "url": "https://github.com/packetanglers/containerlab-topologies",
                    "stars": "150+",
                    "category": "Community",
                    "tags": ["topologies", "network-design", "labs"]
                },
                {
                    "name": "aristanetworks/avd-containerlab",
                    "description": "Arista AVD with containerlab integration",
                    "url": "https://github.com/aristanetworks/avd-containerlab",
                    "stars": "100+",
                    "category": "Vendor",
                    "tags": ["arista", "avd", "automation"]
                }
            ]
            
            return popular_repos
            
        except Exception as e:
            logger.error(f"Failed to get popular repositories: {e}")
            return []
    
    async def get_repository_info(self, repo_full_name: str) -> Dict[str, Any]:
        """Get information about a specific GitHub repository"""
        try:
            headers = await self.get_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                # Get repository information
                repo_url = f"{self.github_api_base}/repos/{repo_full_name}"
                async with session.get(repo_url, headers=headers) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Repository {repo_full_name} not found or inaccessible"
                        }
                    
                    repo_data = await response.json()
                
                # Search for containerlab files
                owner, name = repo_full_name.split("/", 1)
                lab_files = await self.search_containerlab_files(owner, name)
                
                # Get contents of root directory
                contents = await self.get_repository_contents(owner, name)
                
                return {
                    "success": True,
                    "repository": {
                        "name": repo_data.get("name"),
                        "full_name": repo_data.get("full_name"),
                        "description": repo_data.get("description"),
                        "html_url": repo_data.get("html_url"),
                        "clone_url": repo_data.get("clone_url"),
                        "ssh_url": repo_data.get("ssh_url"),
                        "stars": repo_data.get("stargazers_count", 0),
                        "forks": repo_data.get("forks_count", 0),
                        "language": repo_data.get("language"),
                        "created_at": repo_data.get("created_at"),
                        "updated_at": repo_data.get("updated_at"),
                        "private": repo_data.get("private", False),
                        "archived": repo_data.get("archived", False)
                    },
                    "lab_files": lab_files,
                    "contents": contents,
                    "lab_count": len(lab_files),
                    "has_containerlab": len(lab_files) > 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get repository info for {repo_full_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get information for repository {repo_full_name}"
            }