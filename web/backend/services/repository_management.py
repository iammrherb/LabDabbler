import asyncio
import aiohttp
import aiofiles
import json
import yaml
import subprocess
import os
import shutil
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class RepositoryManagementService:
    """
    Comprehensive repository management service for LabDabbler.
    Handles cloning, syncing, and managing containerlab repositories from various sources.
    """
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # Directory structure for repository management
        self.repositories_dir = self.data_dir / "repositories"
        self.repositories_dir.mkdir(exist_ok=True)
        
        # Metadata files
        self.repositories_config_file = self.data_dir / "repositories_config.json"
        self.repositories_metadata_file = self.data_dir / "repositories_metadata.json"
        self.sync_status_file = self.data_dir / "sync_status.json"
        
        # GitHub token for authenticated requests
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # Background scheduler for automated sync
        self.scheduler = None
        self._scheduler_started = False
        
        # Default repository sources - can be extended via configuration
        self.default_sources = {
            "core_repositories": [
                {
                    "name": "containerlab-official",
                    "url": "https://github.com/srl-labs/containerlab.git",
                    "branch": "main",
                    "category": "official",
                    "description": "Official containerlab examples and documentation",
                    "lab_paths": ["lab-examples/"],
                    "auto_sync": True,
                    "sync_frequency": 86400  # 24 hours
                },
                {
                    "name": "hellt-clabs", 
                    "url": "https://github.com/hellt/clabs.git",
                    "branch": "main",
                    "category": "community",
                    "description": "Community containerlab topologies by hellt",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 86400
                },
                {
                    "name": "packetanglers-topos",
                    "url": "https://github.com/PacketAnglers/clab-topos.git", 
                    "branch": "main",
                    "category": "community",
                    "description": "PacketAnglers containerlab topologies collection",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 86400
                },
                {
                    "name": "learn-srlinux",
                    "url": "https://github.com/srl-labs/learn-srlinux.git",
                    "branch": "main", 
                    "category": "educational",
                    "description": "SR Linux learning labs and tutorials",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 86400
                }
            ],
            "additional_sources": [
                {
                    "name": "clab-config-demo",
                    "url": "https://github.com/hellt/clab-config-demo.git",
                    "branch": "main",
                    "category": "demo",
                    "description": "Containerlab configuration demonstration",
                    "lab_paths": ["./"],
                    "auto_sync": False,
                    "sync_frequency": 604800  # 7 days
                },
                {
                    "name": "instruqt-clab-topologies",
                    "url": "https://github.com/ttafsir/instruqt-clab-topologies.git",
                    "branch": "main",
                    "category": "educational", 
                    "description": "Instruqt-based containerlab topologies",
                    "lab_paths": ["./"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                }
            ]
        }
        
    async def initialize_repositories(self) -> Dict:
        """Initialize the repository management system"""
        try:
            logger.info("Initializing repository management system...")
            
            # Load or create configuration
            config = await self.load_or_create_config()
            
            # Initialize core repositories
            results = []
            for repo_config in config["core_repositories"]:
                result = await self.clone_or_update_repository(repo_config)
                results.append(result)
            
            # Update metadata
            await self.update_repositories_metadata()
            
            return {
                "success": True,
                "message": "Repository management system initialized",
                "results": results,
                "total_repositories": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error initializing repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initialize repository management system"
            }
    
    async def load_or_create_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default configuration"""
        try:
            if self.repositories_config_file.exists():
                async with aiofiles.open(self.repositories_config_file, 'r') as f:
                    content = await f.read()
                    config = json.loads(content)
                logger.info("Loaded existing repository configuration")
            else:
                config: Dict[str, Any] = self.default_sources.copy()
                config["last_updated"] = datetime.now().isoformat()
                config["version"] = "1.0.0"
                
                async with aiofiles.open(self.repositories_config_file, 'w') as f:
                    await f.write(json.dumps(config, indent=2))
                    
                logger.info("Created default repository configuration")
                
            return config
            
        except Exception as e:
            logger.error(f"Error loading/creating config: {e}")
            return self.default_sources.copy()
    
    async def clone_or_update_repository(self, repo_config: Dict) -> Dict:
        """Clone a new repository or update an existing one"""
        repo_name = repo_config["name"]
        repo_url = repo_config["url"]
        branch = repo_config.get("branch", "main")
        repo_path = self.repositories_dir / repo_name
        
        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                # Repository exists, update it
                logger.info(f"Updating repository: {repo_name}")
                
                # Fetch latest changes
                process = await asyncio.create_subprocess_exec(
                    "git", "fetch", "origin", branch,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "repository": repo_name,
                        "action": "update",
                        "error": f"Git fetch failed: {stderr.decode()}"
                    }
                
                # Reset to latest origin
                process = await asyncio.create_subprocess_exec(
                    "git", "reset", "--hard", f"origin/{branch}",
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "repository": repo_name,
                        "action": "update", 
                        "error": f"Git reset failed: {stderr.decode()}"
                    }
                    
                action = "updated"
                
            else:
                # Clone new repository
                logger.info(f"Cloning repository: {repo_name}")
                
                # Remove directory if it exists but is not a git repo
                if repo_path.exists():
                    shutil.rmtree(repo_path)
                
                process = await asyncio.create_subprocess_exec(
                    "git", "clone", "-b", branch, repo_url, str(repo_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "repository": repo_name,
                        "action": "clone",
                        "error": f"Git clone failed: {stderr.decode()}"
                    }
                    
                action = "cloned"
            
            # Scan for labs in this repository
            labs = await self.scan_repository_labs(repo_path, repo_config)
            
            return {
                "success": True,
                "repository": repo_name,
                "action": action,
                "path": str(repo_path),
                "labs_found": len(labs),
                "labs": labs,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error with repository {repo_name}: {e}")
            return {
                "success": False,
                "repository": repo_name,
                "action": "error",
                "error": str(e)
            }
    
    async def scan_repository_labs(self, repo_path: Path, repo_config: Dict) -> List[Dict]:
        """Scan a repository for containerlab topology files"""
        labs = []
        lab_paths = repo_config.get("lab_paths", ["./"])
        
        try:
            for lab_path in lab_paths:
                search_path = repo_path / lab_path.lstrip("./")
                if not search_path.exists():
                    continue
                    
                # Find all .clab.yml files
                for lab_file in search_path.rglob("*.clab.yml"):
                    try:
                        # Parse lab file
                        with open(lab_file, 'r') as f:
                            lab_config = yaml.safe_load(f)
                        
                        if not lab_config or "topology" not in lab_config:
                            continue
                            
                        lab_name = lab_config.get("name", lab_file.stem.replace(".clab", ""))
                        nodes = lab_config.get("topology", {}).get("nodes", {})
                        
                        # Handle empty or None nodes gracefully
                        if not nodes or not isinstance(nodes, dict):
                            nodes = {}
                        
                        # Filter out None values and empty nodes
                        valid_nodes = {k: v for k, v in nodes.items() if v is not None and isinstance(v, dict)}
                        node_count = len(valid_nodes)
                        
                        # Extract node kinds and vendors from valid nodes only
                        kinds = []
                        vendors = []
                        
                        for node_name, node_config in valid_nodes.items():
                            if isinstance(node_config, dict):
                                kinds.append(node_config.get("kind", "unknown"))
                                image = node_config.get("image", "")
                                if "nokia" in image or "srl" in image:
                                    vendors.append("nokia")
                                elif "arista" in image or "ceos" in image:
                                    vendors.append("arista")
                                elif "cisco" in image:
                                    vendors.append("cisco")
                                elif "juniper" in image:
                                    vendors.append("juniper")
                        
                        # Use defaults from topology if nodes don't specify kinds/images
                        topology_defaults = lab_config.get("topology", {}).get("defaults", {})
                        if not kinds and topology_defaults:
                            default_kind = topology_defaults.get("kind", "unknown")
                            kinds = [default_kind] * node_count if node_count > 0 else [default_kind]
                        
                        kinds = list(set(filter(None, kinds)))  # Remove None values and deduplicate
                        vendors = list(set(filter(None, vendors)))  # Remove None values and deduplicate
                        
                        # Get relative path from repository root
                        rel_path = lab_file.relative_to(repo_path)
                        
                        lab_info = {
                            "name": lab_name,
                            "file_path": str(lab_file),
                            "relative_path": str(rel_path),
                            "repository": repo_config["name"],
                            "category": repo_config.get("category", "unknown"),
                            "description": lab_config.get("description", f"{lab_name} containerlab topology"),
                            "nodes": node_count,
                            "kinds": kinds,
                            "vendors": vendors,
                            "source": "repository",
                            "topology": lab_config.get("topology", {})
                        }
                        
                        labs.append(lab_info)
                        logger.debug(f"Found lab: {lab_name} in {rel_path}")
                        
                    except Exception as e:
                        logger.warning(f"Error parsing lab file {lab_file}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scanning repository {repo_path}: {e}")
            
        return labs
    
    async def get_all_repositories(self) -> Dict:
        """Get information about all managed repositories"""
        try:
            config = await self.load_or_create_config()
            metadata = await self.load_repositories_metadata()
            
            repositories = []
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo_config in config.get(repo_list_name, []):
                    repo_name = repo_config["name"]
                    repo_path = self.repositories_dir / repo_name
                    
                    repo_info = {
                        "name": repo_name,
                        "url": repo_config["url"],
                        "branch": repo_config.get("branch", "main"),
                        "category": repo_config.get("category", "unknown"),
                        "description": repo_config.get("description", ""),
                        "auto_sync": repo_config.get("auto_sync", False),
                        "sync_frequency": repo_config.get("sync_frequency", 86400),
                        "exists": repo_path.exists(),
                        "path": str(repo_path) if repo_path.exists() else None,
                        "metadata": metadata.get(repo_name, {})
                    }
                    
                    repositories.append(repo_info)
            
            return {
                "success": True,
                "repositories": repositories,
                "total_repositories": len(repositories),
                "config_path": str(self.repositories_config_file),
                "repositories_dir": str(self.repositories_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "repositories": []
            }
    
    async def get_all_labs_from_repositories(self) -> List[Dict]:
        """Get all labs from all managed repositories"""
        all_labs = []
        
        try:
            config = await self.load_or_create_config()
            
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo_config in config.get(repo_list_name, []):
                    repo_name = repo_config["name"]
                    repo_path = self.repositories_dir / repo_name
                    
                    if repo_path.exists():
                        labs = await self.scan_repository_labs(repo_path, repo_config)
                        all_labs.extend(labs)
            
            logger.info(f"Found {len(all_labs)} labs across all repositories")
            return all_labs
            
        except Exception as e:
            logger.error(f"Error getting labs from repositories: {e}")
            return []
    
    async def sync_repository(self, repo_name: str) -> Dict:
        """Sync a specific repository"""
        try:
            config = await self.load_or_create_config()
            
            # Find repository configuration
            repo_config = None
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo in config.get(repo_list_name, []):
                    if repo["name"] == repo_name:
                        repo_config = repo
                        break
                if repo_config:
                    break
            
            if not repo_config:
                return {
                    "success": False,
                    "error": "Repository not found in configuration",
                    "repository": repo_name
                }
            
            # Perform sync
            result = await self.clone_or_update_repository(repo_config)
            
            # Update sync status
            await self.update_sync_status(repo_name, result["success"])
            
            # Update metadata
            await self.update_repositories_metadata()
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing repository {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository": repo_name
            }
    
    async def sync_all_repositories(self) -> Dict:
        """Sync all configured repositories"""
        try:
            config = await self.load_or_create_config()
            results = []
            
            # Sync core repositories
            for repo_config in config.get("core_repositories", []):
                result = await self.clone_or_update_repository(repo_config)
                results.append(result)
                await self.update_sync_status(repo_config["name"], result["success"])
            
            # Sync additional sources
            for repo_config in config.get("additional_sources", []):
                result = await self.clone_or_update_repository(repo_config)
                results.append(result)
                await self.update_sync_status(repo_config["name"], result["success"])
            
            # Update metadata
            await self.update_repositories_metadata()
            
            successful = sum(1 for r in results if r["success"])
            total = len(results)
            
            return {
                "success": True,
                "message": f"Synced {successful}/{total} repositories",
                "results": results,
                "successful": successful,
                "total": total,
                "last_sync": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing all repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to sync repositories"
            }
    
    async def add_repository(self, repo_config: Dict) -> Dict:
        """Add a new repository to the configuration"""
        try:
            # Validate repository configuration
            required_fields = ["name", "url"]
            for field in required_fields:
                if field not in repo_config:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Load current configuration
            config = await self.load_or_create_config()
            
            # Check if repository already exists
            repo_name = repo_config["name"]
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for existing_repo in config.get(repo_list_name, []):
                    if existing_repo["name"] == repo_name:
                        return {
                            "success": False,
                            "error": f"Repository {repo_name} already exists"
                        }
            
            # Set defaults
            repo_config.setdefault("branch", "main")
            repo_config.setdefault("category", "custom")
            repo_config.setdefault("description", f"Custom repository: {repo_name}")
            repo_config.setdefault("lab_paths", ["./"])
            repo_config.setdefault("auto_sync", False)
            repo_config.setdefault("sync_frequency", 604800)  # 7 days
            
            # Add to additional sources
            if "additional_sources" not in config:
                config["additional_sources"] = []
            config["additional_sources"].append(repo_config)
            
            # Save configuration
            config["last_updated"] = datetime.now().isoformat()
            async with aiofiles.open(self.repositories_config_file, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            # Clone the repository
            result = await self.clone_or_update_repository(repo_config)
            
            return {
                "success": True,
                "message": f"Repository {repo_name} added successfully",
                "repository": repo_name,
                "clone_result": result
            }
            
        except Exception as e:
            logger.error(f"Error adding repository: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_repository(self, repo_name: str) -> Dict:
        """Remove a repository from the configuration and filesystem"""
        try:
            # Load current configuration
            config = await self.load_or_create_config()
            
            # Find and remove repository from configuration
            found = False
            for repo_list_name in ["core_repositories", "additional_sources"]:
                repo_list = config.get(repo_list_name, [])
                for i, repo in enumerate(repo_list):
                    if repo["name"] == repo_name:
                        del repo_list[i]
                        found = True
                        break
                if found:
                    break
            
            if not found:
                return {
                    "success": False,
                    "error": f"Repository {repo_name} not found in configuration"
                }
            
            # Save updated configuration
            config["last_updated"] = datetime.now().isoformat()
            async with aiofiles.open(self.repositories_config_file, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            # Remove repository directory
            repo_path = self.repositories_dir / repo_name
            if repo_path.exists():
                shutil.rmtree(repo_path)
                logger.info(f"Removed repository directory: {repo_path}")
            
            # Update metadata
            await self.update_repositories_metadata()
            
            return {
                "success": True,
                "message": f"Repository {repo_name} removed successfully",
                "repository": repo_name
            }
            
        except Exception as e:
            logger.error(f"Error removing repository {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository": repo_name
            }
    
    async def get_repository_status(self, repo_name: str) -> Dict:
        """Get detailed status of a specific repository"""
        try:
            config = await self.load_or_create_config()
            repo_path = self.repositories_dir / repo_name
            
            # Find repository configuration
            repo_config = None
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo in config.get(repo_list_name, []):
                    if repo["name"] == repo_name:
                        repo_config = repo
                        break
                if repo_config:
                    break
            
            if not repo_config:
                return {
                    "success": False,
                    "error": f"Repository {repo_name} not found in configuration"
                }
            
            status = {
                "name": repo_name,
                "exists": repo_path.exists(),
                "path": str(repo_path),
                "config": repo_config
            }
            
            if repo_path.exists() and (repo_path / ".git").exists():
                # Get git information
                try:
                    # Get current branch
                    process = await asyncio.create_subprocess_exec(
                        "git", "branch", "--show-current",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        status["current_branch"] = stdout.decode().strip()
                    
                    # Get last commit info
                    process = await asyncio.create_subprocess_exec(
                        "git", "log", "-1", "--format=%H|%an|%ad|%s",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        commit_info = stdout.decode().strip().split("|", 3)
                        if len(commit_info) == 4:
                            status["last_commit"] = {
                                "hash": commit_info[0],
                                "author": commit_info[1],
                                "date": commit_info[2],
                                "message": commit_info[3]
                            }
                    
                    # Check if repository is up to date
                    process = await asyncio.create_subprocess_exec(
                        "git", "fetch", "origin",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    process = await asyncio.create_subprocess_exec(
                        "git", "status", "-uno",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        git_status = stdout.decode()
                        status["up_to_date"] = "up to date" in git_status
                        status["needs_pull"] = "behind" in git_status
                    
                except Exception as git_error:
                    logger.warning(f"Error getting git info for {repo_name}: {git_error}")
                    status["git_error"] = str(git_error)
                
                # Scan for labs
                labs = await self.scan_repository_labs(repo_path, repo_config)
                status["labs"] = labs
                status["lab_count"] = len(labs)
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting repository status {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_repositories_metadata(self) -> None:
        """Update metadata file with current repository information"""
        try:
            metadata = {}
            config = await self.load_or_create_config()
            
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo_config in config.get(repo_list_name, []):
                    repo_name = repo_config["name"]
                    repo_path = self.repositories_dir / repo_name
                    
                    if repo_path.exists():
                        labs = await self.scan_repository_labs(repo_path, repo_config)
                        metadata[repo_name] = {
                            "last_scanned": datetime.now().isoformat(),
                            "lab_count": len(labs),
                            "exists": True,
                            "path": str(repo_path)
                        }
                    else:
                        metadata[repo_name] = {
                            "last_scanned": datetime.now().isoformat(),
                            "lab_count": 0,
                            "exists": False,
                            "path": None
                        }
            
            async with aiofiles.open(self.repositories_metadata_file, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
                
            logger.info("Updated repositories metadata")
            
        except Exception as e:
            logger.error(f"Error updating repositories metadata: {e}")
    
    async def load_repositories_metadata(self) -> Dict:
        """Load repositories metadata"""
        try:
            if self.repositories_metadata_file.exists():
                async with aiofiles.open(self.repositories_metadata_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return {}
        except Exception as e:
            logger.error(f"Error loading repositories metadata: {e}")
            return {}
    
    async def update_sync_status(self, repo_name: str, success: bool) -> None:
        """Update sync status for a repository"""
        try:
            status = {}
            if self.sync_status_file.exists():
                async with aiofiles.open(self.sync_status_file, 'r') as f:
                    content = await f.read()
                    status = json.loads(content)
            
            status[repo_name] = {
                "last_sync": datetime.now().isoformat(),
                "success": success,
                "sync_count": status.get(repo_name, {}).get("sync_count", 0) + 1
            }
            
            async with aiofiles.open(self.sync_status_file, 'w') as f:
                await f.write(json.dumps(status, indent=2))
                
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    async def get_sync_status(self) -> Dict:
        """Get sync status for all repositories"""
        try:
            if self.sync_status_file.exists():
                async with aiofiles.open(self.sync_status_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return {}
        except Exception as e:
            logger.error(f"Error loading sync status: {e}")
            return {}
    
    async def auto_sync_repositories(self) -> Dict:
        """Perform automatic sync for repositories that have auto_sync enabled"""
        try:
            config = await self.load_or_create_config()
            sync_status = await self.get_sync_status()
            results = []
            
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo_config in config.get(repo_list_name, []):
                    if not repo_config.get("auto_sync", False):
                        continue
                    
                    repo_name = repo_config["name"]
                    sync_frequency = repo_config.get("sync_frequency", 86400)  # Default 24 hours
                    
                    # Check if sync is needed
                    last_sync = sync_status.get(repo_name, {}).get("last_sync")
                    if last_sync:
                        last_sync_time = datetime.fromisoformat(last_sync)
                        if datetime.now() - last_sync_time < timedelta(seconds=sync_frequency):
                            continue  # Too soon to sync
                    
                    # Perform sync
                    logger.info(f"Auto-syncing repository: {repo_name}")
                    result = await self.sync_repository(repo_name)
                    results.append(result)
            
            return {
                "success": True,
                "message": f"Auto-sync completed for {len(results)} repositories",
                "results": results,
                "synced_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in auto-sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Auto-sync failed"
            }
    
    async def start_background_sync(self):
        """Start the background sync scheduler"""
        if self._scheduler_started:
            logger.info("Background sync scheduler already started")
            return
        
        try:
            self.scheduler = AsyncIOScheduler()
            
            # Schedule auto-sync to run every 5 minutes to check if any repositories need syncing
            self.scheduler.add_job(
                self._background_sync_check,
                IntervalTrigger(minutes=5),
                id='auto_sync_check',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            
            self.scheduler.start()
            self._scheduler_started = True
            logger.info("Background sync scheduler started - will check for sync needs every 5 minutes")
            
        except Exception as e:
            logger.error(f"Error starting background sync scheduler: {e}")
    
    async def stop_background_sync(self):
        """Stop the background sync scheduler"""
        if self.scheduler and self._scheduler_started:
            try:
                self.scheduler.shutdown()
                self._scheduler_started = False
                logger.info("Background sync scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping background sync scheduler: {e}")
    
    async def _background_sync_check(self):
        """Background task that checks if repositories need syncing based on their auto_sync and sync_frequency settings"""
        try:
            logger.debug("Running background sync check...")
            result = await self.auto_sync_repositories()
            
            if result["success"] and result.get("synced_count", 0) > 0:
                logger.info(f"Background sync completed: {result['synced_count']} repositories synced")
            elif not result["success"]:
                logger.error(f"Background sync failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in background sync check: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """Get the current status of the background sync scheduler"""
        next_sync_check = None
        if self.scheduler:
            try:
                job = self.scheduler.get_job('auto_sync_check')
                if job and job.next_run_time:
                    next_sync_check = job.next_run_time.isoformat()
            except Exception:
                next_sync_check = None
                
        return {
            "scheduler_running": self._scheduler_started,
            "scheduler_active": self.scheduler is not None and self.scheduler.running if self.scheduler else False,
            "next_sync_check": next_sync_check
        }