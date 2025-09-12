import asyncio
import json
import yaml
import subprocess
import aiohttp
import os
from typing import Dict, List, Optional, cast
from pathlib import Path
import logging
import uuid
import shutil
import tempfile

from .runtime import RuntimeProviderFactory, RuntimeProvider

logger = logging.getLogger(__name__)

class LabLauncherService:
    """Service to launch and manage containerlab topologies"""
    
    def __init__(self, data_dir: Path = Path("./data"), runtime_provider: Optional[RuntimeProvider] = None):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.active_labs_file = self.data_dir / "active_labs.json"
        self.lab_configs_dir = self.data_dir / "lab_configs"
        self.lab_configs_dir.mkdir(exist_ok=True)
        
        # Initialize runtime provider
        if runtime_provider:
            self.runtime_provider: RuntimeProvider = runtime_provider
        else:
            self.runtime_factory = RuntimeProviderFactory(data_dir)
            provider = self.runtime_factory.get_default_provider()
            if not provider:
                raise RuntimeError("No runtime provider available")
            self.runtime_provider: RuntimeProvider = provider
        
    async def launch_lab(self, lab_file_path: str) -> Dict:
        """Launch a containerlab topology from an existing .clab.yml file or URL"""
        try:
            # Check if lab_file_path is a URL
            if lab_file_path.startswith(('http://', 'https://')):
                lab_file, lab_config = await self.download_and_parse_lab_file(lab_file_path)
                if not lab_file or lab_config is None:
                    return {
                        "success": False,
                        "error": "Failed to download lab file",
                        "message": f"Could not download or parse lab file from {lab_file_path}"
                    }
            else:
                # Handle local file path
                lab_file = Path(lab_file_path)
                
                # Verify the lab file exists
                if not lab_file.exists():
                    return {
                        "success": False,
                        "error": "Lab file not found",
                        "message": f"Lab file {lab_file} does not exist"
                    }
                
                # Load and parse the lab configuration
                try:
                    with open(lab_file, 'r') as f:
                        lab_config = yaml.safe_load(f)
                    
                    # Check if yaml.safe_load returned None (empty or invalid file)
                    if lab_config is None:
                        return {
                            "success": False,
                            "error": "Invalid lab file",
                            "message": f"Lab file {lab_file} is empty or contains invalid YAML"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse lab file: {e}",
                        "message": "Lab file is not valid YAML"
                    }
            
            # Ensure lab_config is a dictionary
            if not isinstance(lab_config, dict):
                return {
                    "success": False,
                    "error": "Invalid lab configuration",
                    "message": "Lab file must contain a valid YAML dictionary"
                }
            
            # Get lab name from config - this ensures consistency
            lab_name = lab_config.get("name", lab_file.stem.replace(".clab", ""))
            lab_id = str(uuid.uuid4())[:8]
            
            logger.info(f"Launching lab: {lab_name} (ID: {lab_id}) from {lab_file}")
            
            # Check if containerlab is available
            assert self.runtime_provider is not None, "Runtime provider should be initialized"
            if not await self.runtime_provider.check_containerlab():
                return {
                    "success": False,
                    "error": "containerlab is not installed or not available",
                    "message": "Please install containerlab on the runtime provider"
                }
            
            # Upload lab file to runtime if needed (for remote providers)
            remote_lab_file = str(lab_file)
            assert self.runtime_provider is not None, "Runtime provider should be initialized"
            if self.runtime_provider.type != "local":
                # For remote providers, upload the file
                remote_lab_file = f"/tmp/{lab_file.name}"
                upload_success = await self.runtime_provider.upload_file(lab_file, remote_lab_file)
                if not upload_success:
                    return {
                        "success": False,
                        "error": "Failed to upload lab file to runtime provider",
                        "message": f"Could not upload {lab_file} to remote host"
                    }
            
            # Launch the lab using the runtime provider
            result = await self.execute_containerlab_deploy(lab_name, remote_lab_file)
            
            if result["success"]:
                # Store lab information
                await self.store_active_lab(lab_id, {
                    "name": lab_name,
                    "original_file": lab_file_path,
                    "status": "running",
                    "created_at": str(asyncio.get_event_loop().time()),
                    "config": lab_config
                })
                
                return {
                    "success": True,
                    "lab_id": lab_id,
                    "lab_name": lab_name,
                    "message": f"Lab {lab_name} launched successfully",
                    "details": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Failed to launch lab {lab_name}"
                }
                
        except Exception as e:
            logger.error(f"Error launching lab: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Internal error while launching lab"
            }
    
    async def download_and_parse_lab_file(self, url: str) -> tuple[Optional[Path], Optional[Dict]]:
        """Download a lab file from URL and parse it"""
        try:
            # Prepare headers with GitHub authentication if downloading from GitHub
            headers = {}
            if 'github' in url.lower():
                github_token = os.getenv("GITHUB_TOKEN")
                if github_token:
                    headers['Authorization'] = f'token {github_token}'
                    logger.info("Using GitHub token for authenticated download")
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse YAML content
                        try:
                            lab_config = yaml.safe_load(content)
                            # Check if yaml.safe_load returned None
                            if lab_config is None:
                                logger.error(f"Downloaded file from {url} is empty or contains no valid YAML")
                                return None, None
                            # Ensure it's a dictionary
                            if not isinstance(lab_config, dict):
                                logger.error(f"Downloaded file from {url} does not contain a valid YAML dictionary")
                                return None, None
                        except yaml.YAMLError as e:
                            logger.error(f"Failed to parse YAML from {url}: {e}")
                            return None, None
                        
                        # Create a temporary file with proper handling
                        with tempfile.NamedTemporaryFile(
                            mode='w', 
                            suffix='.clab.yml', 
                            dir=self.lab_configs_dir, 
                            delete=False
                        ) as temp_file_obj:
                            temp_file_obj.write(content)
                            temp_file = Path(temp_file_obj.name)
                        
                        logger.info(f"Downloaded lab file from {url} to {temp_file}")
                        return temp_file, lab_config
                    else:
                        logger.error(f"Failed to download lab file from {url}: HTTP {response.status}")
                        return None, None
        except Exception as e:
            logger.error(f"Error downloading lab file from {url}: {e}")
            return None, None
    
    async def stop_lab(self, lab_id: str) -> Dict:
        """Stop a running lab"""
        try:
            active_labs = await self.load_active_labs()
            
            if lab_id not in active_labs:
                return {
                    "success": False,
                    "error": "Lab not found",
                    "message": f"Lab {lab_id} is not active"
                }
            
            lab_info = active_labs[lab_id]
            lab_name = lab_info["name"]
            
            # Use the original lab file if available, otherwise try to find it
            lab_file_path = lab_info.get("original_file")
            if lab_file_path and Path(lab_file_path).exists():
                lab_file = Path(lab_file_path)
            else:
                # Fallback: try to find the lab file based on name
                return {
                    "success": False,
                    "error": "Original lab file not found",
                    "message": f"Cannot stop lab {lab_name} - original topology file is missing"
                }
            
            # For remote providers, we may need to re-upload the file or use the cached path
            remote_lab_file = str(lab_file)
            assert self.runtime_provider is not None, "Runtime provider should be initialized"
            if self.runtime_provider.type != "local":
                remote_lab_file = f"/tmp/{lab_file.name}"
                # Try to upload the file for destroy (if it exists locally)
                if lab_file.exists():
                    await self.runtime_provider.upload_file(lab_file, remote_lab_file)
                
            result = await self.execute_containerlab_destroy(lab_name, remote_lab_file)
            
            # Always clean up from our tracking, even if destroy had issues
            del active_labs[lab_id]
            await self.save_active_labs(active_labs)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Lab {lab_name} stopped successfully"
                }
            else:
                # Still return success if we cleaned up our tracking
                return {
                    "success": True,
                    "message": f"Lab {lab_name} cleanup completed (destroy command had issues: {result.get('error', 'unknown')})",
                    "warning": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error stopping lab {lab_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Internal error while stopping lab"
            }
    
    async def get_lab_status(self, lab_id: str) -> Dict:
        """Get the status of a specific lab"""
        try:
            active_labs = await self.load_active_labs()
            
            if lab_id not in active_labs:
                return {
                    "success": False,
                    "error": "Lab not found",
                    "status": "not_found"
                }
            
            lab_info = active_labs[lab_id]
            lab_name = lab_info["name"]
            
            # Check if lab is actually running by querying containerlab with the lab name
            status = await self.check_lab_running_status(lab_name)
            
            return {
                "success": True,
                "lab_id": lab_id,
                "name": lab_name,
                "status": status,
                "created_at": lab_info.get("created_at"),
                "original_file": lab_info.get("original_file"),
                "config": lab_info.get("config", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting lab status {lab_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def list_active_labs(self) -> List[Dict]:
        """List all active labs"""
        try:
            active_labs = await self.load_active_labs()
            labs = []
            
            for lab_id, lab_info in active_labs.items():
                lab_name = lab_info["name"]
                status = await self.check_lab_running_status(lab_name)
                labs.append({
                    "lab_id": lab_id,
                    "name": lab_name,
                    "status": status,
                    "created_at": lab_info.get("created_at"),
                    "original_file": lab_info.get("original_file"),
                    "node_count": len(lab_info.get("config", {}).get("topology", {}).get("nodes", {}))
                })
            
            return labs
            
        except Exception as e:
            logger.error(f"Error listing active labs: {e}")
            return []
    
    # Removed check_containerlab method - now delegated to runtime provider
    
    async def execute_containerlab_deploy(self, lab_name: str, lab_file: str) -> Dict:
        """Execute containerlab deploy command using runtime provider"""
        try:
            cmd = ["containerlab", "deploy", "-t", lab_file]
            
            # Get working directory (parent of lab file)
            assert self.runtime_provider is not None, "Runtime provider should be initialized"
            cwd = str(Path(lab_file).parent) if self.runtime_provider.type == "local" else "/tmp"
            
            return_code, stdout, stderr = await self.runtime_provider.execute_command(cmd, cwd)
            
            if return_code == 0:
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr
                }
            else:
                return {
                    "success": False,
                    "error": stderr or f"Deploy failed with return code {return_code}",
                    "stdout": stdout
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_containerlab_destroy(self, lab_name: str, lab_file: str) -> Dict:
        """Execute containerlab destroy command using runtime provider"""
        try:
            cmd = ["containerlab", "destroy", "-t", lab_file]
            
            # Get working directory (parent of lab file)
            assert self.runtime_provider is not None, "Runtime provider should be initialized"
            cwd = str(Path(lab_file).parent) if self.runtime_provider.type == "local" else "/tmp"
            
            return_code, stdout, stderr = await self.runtime_provider.execute_command(cmd, cwd)
            
            # Check return code for destroy operation
            if return_code == 0:
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr
                }
            else:
                return {
                    "success": False,
                    "error": stderr or f"Destroy failed with return code {return_code}",
                    "stdout": stdout
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_lab_running_status(self, lab_name: str) -> str:
        """Check if a lab is actually running using the lab name"""
        try:
            # Use containerlab inspect to check status with the actual lab name
            cmd = ["containerlab", "inspect", "--name", lab_name]
            
            assert self.runtime_provider is not None, "Runtime provider should be initialized"
            return_code, stdout, stderr = await self.runtime_provider.execute_command(cmd)
            
            if return_code == 0:
                return "running"
            else:
                return "stopped"
                
        except Exception:
            return "unknown"
    
    async def load_active_labs(self) -> Dict:
        """Load active labs from storage"""
        if self.active_labs_file.exists():
            with open(self.active_labs_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def save_active_labs(self, labs: Dict):
        """Save active labs to storage"""
        with open(self.active_labs_file, 'w') as f:
            json.dump(labs, f, indent=2)
    
    async def store_active_lab(self, lab_id: str, lab_info: Dict):
        """Store information about an active lab"""
        active_labs = await self.load_active_labs()
        active_labs[lab_id] = lab_info
        await self.save_active_labs(active_labs)