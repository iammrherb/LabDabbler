import asyncio
import json
import yaml
import subprocess
import aiohttp
import os
import shutil
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import uuid
import tempfile
from datetime import datetime
import aiofiles

logger = logging.getLogger(__name__)

class VRNetLabService:
    """Service for VM-to-container conversion using vrnetlab/hellt integration"""
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # Directory structure for vrnetlab operations
        self.vm_images_dir = self.data_dir / "vm_images"
        self.vrnetlab_builds_dir = self.data_dir / "vrnetlab_builds"
        self.vrnetlab_repo_dir = self.data_dir / "vrnetlab_repo"
        self.container_registry_dir = self.data_dir / "container_registry"
        
        # Create directories
        for directory in [self.vm_images_dir, self.vrnetlab_builds_dir, 
                         self.vrnetlab_repo_dir, self.container_registry_dir]:
            directory.mkdir(exist_ok=True)
        
        # Metadata files
        self.build_metadata_file = self.data_dir / "vrnetlab_builds.json"
        self.vm_images_metadata_file = self.data_dir / "vm_images.json"
        self.container_registry_file = self.data_dir / "vrnetlab_containers.json"
        
        # Supported VM image types and their vrnetlab mappings
        # Maps to actual vrnetlab repository structure: vendor/platform/
        self.supported_vendors = {
            "cisco": {
                "csr1000v": {"extensions": [".qcow2", ".vmdk", ".ova"], "vrnetlab_path": "cisco/csr1000v"},
                "xrv": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/xrv"},
                "xrv9k": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/xrv9k"},
                "n9kv": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/n9kv"},
                "nxos": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/nxos"},
                "asav": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/asav"},
                "vios": {"extensions": [".bin", ".tar"], "vrnetlab_path": "cisco/vios"},
                "viosl2": {"extensions": [".bin", ".tar"], "vrnetlab_path": "cisco/viosl2"},
                "c8000v": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/c8000v"},
                "cat9kv": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/cat9kv"},
                "ftdv": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "cisco/ftdv"},
                "iol": {"extensions": [".bin"], "vrnetlab_path": "cisco/iol"}
            },
            "juniper": {
                "vmx": {"extensions": [".qcow2", ".vmdk", ".tgz"], "vrnetlab_path": "juniper/vmx"},
                "vsrx": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "juniper/vsrx"},
                "vqfx": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "juniper/vqfx"},
                "vjunosevolved": {"extensions": [".qcow2"], "vrnetlab_path": "juniper/vjunosevolved"},
                "vjunosrouter": {"extensions": [".qcow2"], "vrnetlab_path": "juniper/vjunosrouter"},
                "vjunosswitch": {"extensions": [".qcow2"], "vrnetlab_path": "juniper/vjunosswitch"}
            },
            "nokia": {
                "sros": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "nokia/sros"}
            },
            "arista": {
                "veos": {"extensions": [".vmdk", ".qcow2"], "vrnetlab_path": "arista/veos"}
            },
            "fortinet": {
                "fortigate": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "fortinet/fortigate"}
            },
            "paloalto": {
                "pan": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "paloalto/pan"}
            },
            "mikrotik": {
                "routeros": {"extensions": [".qcow2", ".vmdk"], "vrnetlab_path": "mikrotik/routeros"}
            }
        }
    
    async def initialize_vrnetlab_repo(self) -> Dict:
        """Clone or update the hellt/vrnetlab repository"""
        try:
            vrnetlab_git_url = "https://github.com/hellt/vrnetlab.git"
            
            if not (self.vrnetlab_repo_dir / ".git").exists():
                logger.info("Cloning vrnetlab repository...")
                process = await asyncio.create_subprocess_exec(
                    "git", "clone", vrnetlab_git_url, str(self.vrnetlab_repo_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to clone vrnetlab repo: {stderr.decode()}"
                    }
            else:
                logger.info("Updating vrnetlab repository...")
                process = await asyncio.create_subprocess_exec(
                    "git", "pull", "origin", "master",
                    cwd=self.vrnetlab_repo_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.warning(f"Git pull failed: {stderr.decode()}")
            
            return {
                "success": True,
                "message": "VRNetlab repository ready",
                "repo_path": str(self.vrnetlab_repo_dir)
            }
            
        except Exception as e:
            logger.error(f"Error initializing vrnetlab repo: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_vm_image(self, file_data: bytes, filename: str, 
                            vendor: str, platform: str, version: str = "latest") -> Dict:
        """Upload and store a VM image for conversion"""
        try:
            # Validate vendor and platform
            if vendor not in self.supported_vendors:
                return {
                    "success": False,
                    "error": f"Unsupported vendor: {vendor}. Supported vendors: {list(self.supported_vendors.keys())}"
                }
            
            if platform not in self.supported_vendors[vendor]:
                return {
                    "success": False,
                    "error": f"Unsupported platform: {platform} for vendor: {vendor}. Supported platforms: {list(self.supported_vendors[vendor].keys())}"
                }
            
            # Validate file extension
            file_ext = Path(filename).suffix.lower()
            supported_extensions = self.supported_vendors[vendor][platform]["extensions"]
            if file_ext not in supported_extensions:
                return {
                    "success": False,
                    "error": f"Unsupported file extension: {file_ext}. Supported extensions for {vendor}/{platform}: {supported_extensions}"
                }
            
            # Generate unique image ID
            image_id = str(uuid.uuid4())
            
            # Create vendor/platform specific directory
            vendor_dir = self.vm_images_dir / vendor / platform
            vendor_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the image file
            image_file_path = vendor_dir / f"{image_id}_{filename}"
            
            async with aiofiles.open(image_file_path, 'wb') as f:
                await f.write(file_data)
            
            # Calculate file hash for integrity
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Store metadata
            image_metadata = {
                "id": image_id,
                "filename": filename,
                "vendor": vendor,
                "platform": platform,
                "version": version,
                "file_path": str(image_file_path),
                "file_size": len(file_data),
                "file_hash": file_hash,
                "uploaded_at": datetime.now().isoformat(),
                "status": "uploaded",
                "vrnetlab_path": self.supported_vendors[vendor][platform]["vrnetlab_path"]
            }
            
            await self.store_vm_image_metadata(image_id, image_metadata)
            
            logger.info(f"VM image uploaded: {vendor}/{platform} - {filename}")
            return {
                "success": True,
                "image_id": image_id,
                "message": f"VM image uploaded successfully: {filename}",
                "metadata": image_metadata
            }
            
        except Exception as e:
            logger.error(f"Error uploading VM image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def build_vrnetlab_container(self, image_id: str, 
                                     container_name: Optional[str] = None, 
                                     container_tag: str = "latest") -> Dict:
        """Build a vrnetlab container from uploaded VM image"""
        try:
            # Get image metadata
            vm_images = await self.load_vm_images_metadata()
            if image_id not in vm_images:
                return {
                    "success": False,
                    "error": f"VM image not found: {image_id}"
                }
            
            image_metadata = vm_images[image_id]
            vendor = image_metadata["vendor"]
            platform = image_metadata["platform"]
            vrnetlab_path = image_metadata["vrnetlab_path"]
            
            # Initialize vrnetlab repo
            repo_result = await self.initialize_vrnetlab_repo()
            if not repo_result["success"]:
                return repo_result
            
            # Generate build ID
            build_id = str(uuid.uuid4())[:8]
            
            # Auto-generate container name if not provided
            if not container_name:
                container_name = f"vr-{vendor}-{platform}-{build_id}"
            
            build_name = container_name
            
            # Create build directory
            build_dir = self.vrnetlab_builds_dir / build_id
            build_dir.mkdir(exist_ok=True)
            
            # Validate vrnetlab platform directory exists
            vrnetlab_platform_dir = self.vrnetlab_repo_dir / vrnetlab_path
            if not vrnetlab_platform_dir.exists():
                return {
                    "success": False,
                    "error": f"VRNetlab platform directory not found: {vrnetlab_platform_dir}"
                }
            
            # Validate Docker is available
            docker_check = await self._check_docker_availability()
            if not docker_check["available"]:
                return {
                    "success": False,
                    "error": f"Docker not available: {docker_check['error']}"
                }
            
            # Create platform-specific build directory
            platform_build_dir = build_dir / platform
            platform_build_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy platform files to build directory
            shutil.copytree(vrnetlab_platform_dir, platform_build_dir, dirs_exist_ok=True)
            
            # Copy VM image to platform root directory (not docker/ subdirectory)
            vm_image_path = Path(image_metadata["file_path"])
            target_image_path = platform_build_dir / vm_image_path.name
            shutil.copy2(vm_image_path, target_image_path)
            
            # Create build metadata
            build_metadata = {
                "build_id": build_id,
                "image_id": image_id,
                "container_name": build_name,
                "container_tag": container_tag,
                "vendor": vendor,
                "platform": platform,
                "vrnetlab_path": vrnetlab_path,
                "build_dir": str(build_dir),
                "vm_image_path": str(target_image_path),
                "status": "building",
                "started_at": datetime.now().isoformat(),
                "logs": []
            }
            
            await self.store_build_metadata(build_id, build_metadata)
            
            # Start the build process asynchronously
            asyncio.create_task(self._execute_vrnetlab_build(build_id, platform_build_dir, build_name, container_tag))
            
            logger.info(f"Started vrnetlab build: {build_name} (build_id: {build_id})")
            return {
                "success": True,
                "build_id": build_id,
                "container_name": build_name,
                "message": f"VRNetlab container build started: {build_name}",
                "metadata": build_metadata
            }
            
        except Exception as e:
            logger.error(f"Error starting vrnetlab build: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_vrnetlab_build(self, build_id: str, platform_build_dir: Path, 
                                    container_name: str, container_tag: str):
        """Execute the actual vrnetlab docker build process"""
        try:
            build_metadata = (await self.load_build_metadata())[build_id]
            
            # Docker build context is in the docker/ subdirectory
            docker_context_dir = platform_build_dir / "docker"
            if not docker_context_dir.exists():
                raise Exception(f"Docker context directory not found: {docker_context_dir}")
            
            # Copy the VM image to docker context directory for build
            vm_image_files = list(platform_build_dir.glob("*"))
            vm_image_files = [f for f in vm_image_files if f.is_file() and not f.name.startswith('.') and f.suffix in ['.qcow2', '.vmdk', '.bin', '.tar', '.tgz', '.ova']]
            
            if not vm_image_files:
                raise Exception("No VM image files found in platform directory")
            
            for vm_image_file in vm_image_files:
                target_image_path = docker_context_dir / vm_image_file.name
                if target_image_path.exists():
                    target_image_path.unlink()  # Remove if exists
                shutil.copy2(vm_image_file, target_image_path)
                logger.info(f"Copied VM image to Docker context: {vm_image_file.name}")
            
            # Copy launch.py and other necessary files from common directory
            common_dir = self.vrnetlab_repo_dir / "common"
            for common_file in ["healthcheck.py", "vrnetlab.py"]:
                common_file_path = common_dir / common_file
                if common_file_path.exists():
                    shutil.copy2(common_file_path, docker_context_dir / common_file)
            
            # Execute docker build from docker/ subdirectory
            docker_build_cmd = [
                "docker", "build", 
                "-t", f"{container_name}:{container_tag}",
                "."
            ]
            
            logger.info(f"Executing vrnetlab build in {docker_context_dir}: {' '.join(docker_build_cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *docker_build_cmd,
                cwd=docker_context_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Stream build output
            build_logs = []
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    log_line = line.decode().strip()
                    build_logs.append(log_line)
                    logger.info(f"Build {build_id}: {log_line}")
                    
                    # Update build metadata periodically
                    if len(build_logs) % 10 == 0:
                        build_metadata["logs"] = build_logs[-50:]  # Keep last 50 lines
                        await self.store_build_metadata(build_id, build_metadata)
            
            await process.wait()
            
            # Update final build status
            if process.returncode == 0:
                build_metadata["status"] = "completed"
                build_metadata["completed_at"] = datetime.now().isoformat()
                build_metadata["container_image"] = f"{container_name}:{container_tag}"
                
                # Register the container
                await self.register_built_container(build_id, container_name, container_tag, build_metadata)
                
                logger.info(f"VRNetlab build completed successfully: {container_name}:{container_tag}")
            else:
                build_metadata["status"] = "failed"
                build_metadata["failed_at"] = datetime.now().isoformat()
                build_metadata["error"] = f"Docker build failed with return code: {process.returncode}"
                
                logger.error(f"VRNetlab build failed: {container_name}:{container_tag}")
            
            build_metadata["logs"] = build_logs
            await self.store_build_metadata(build_id, build_metadata)
            
        except Exception as e:
            logger.error(f"Error executing vrnetlab build {build_id}: {e}")
            # Update build status to failed
            try:
                build_metadata = (await self.load_build_metadata())[build_id]
                build_metadata["status"] = "failed"
                build_metadata["failed_at"] = datetime.now().isoformat()
                build_metadata["error"] = str(e)
                await self.store_build_metadata(build_id, build_metadata)
            except:
                pass
    
    async def register_built_container(self, build_id: str, container_name: str, 
                                     container_tag: str, build_metadata: Dict):
        """Register a successfully built container in the registry"""
        try:
            container_registry = await self.load_container_registry()
            
            container_info = {
                "build_id": build_id,
                "name": container_name,
                "tag": container_tag,
                "image": f"{container_name}:{container_tag}",
                "vendor": build_metadata["vendor"],
                "platform": build_metadata["platform"],
                "vrnetlab_path": build_metadata["vrnetlab_path"],
                "description": f"{build_metadata['vendor'].title()} {build_metadata['platform'].upper()} - VRNetlab Container",
                "category": "vrnetlab_built",
                "kind": f"vr-{build_metadata['platform']}",
                "created_at": build_metadata.get("completed_at", datetime.now().isoformat()),
                "image_id": build_metadata["image_id"],
                "access": "local_build",
                "registry": "local"
            }
            
            container_registry[f"{container_name}:{container_tag}"] = container_info
            await self.store_container_registry(container_registry)
            
            logger.info(f"Registered built container: {container_name}:{container_tag}")
            
        except Exception as e:
            logger.error(f"Error registering built container: {e}")
    
    async def get_build_status(self, build_id: str) -> Dict:
        """Get the status of a vrnetlab build"""
        try:
            builds = await self.load_build_metadata()
            if build_id not in builds:
                return {
                    "success": False,
                    "error": f"Build not found: {build_id}"
                }
            
            return {
                "success": True,
                "build": builds[build_id]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_vm_images(self) -> Dict:
        """List all uploaded VM images"""
        try:
            vm_images = await self.load_vm_images_metadata()
            return {
                "success": True,
                "images": list(vm_images.values())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_builds(self) -> Dict:
        """List all vrnetlab builds"""
        try:
            builds = await self.load_build_metadata()
            return {
                "success": True,
                "builds": list(builds.values())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_built_containers(self) -> Dict:
        """List all built vrnetlab containers"""
        try:
            registry = await self.load_container_registry()
            return {
                "success": True,
                "containers": list(registry.values())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_vm_image(self, image_id: str) -> Dict:
        """Delete a VM image and its associated builds"""
        try:
            vm_images = await self.load_vm_images_metadata()
            if image_id not in vm_images:
                return {
                    "success": False,
                    "error": f"VM image not found: {image_id}"
                }
            
            image_metadata = vm_images[image_id]
            
            # Delete the image file
            if Path(image_metadata["file_path"]).exists():
                Path(image_metadata["file_path"]).unlink()
            
            # Remove from metadata
            del vm_images[image_id]
            await self.store_vm_images_metadata(vm_images)
            
            return {
                "success": True,
                "message": f"VM image deleted: {image_metadata['filename']}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Metadata management methods
    async def load_vm_images_metadata(self) -> Dict:
        """Load VM images metadata from file"""
        if self.vm_images_metadata_file.exists():
            with open(self.vm_images_metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def store_vm_image_metadata(self, image_id: str, metadata: Dict):
        """Store VM image metadata"""
        vm_images = await self.load_vm_images_metadata()
        vm_images[image_id] = metadata
        await self.store_vm_images_metadata(vm_images)
    
    async def store_vm_images_metadata(self, vm_images: Dict):
        """Store all VM images metadata to file"""
        with open(self.vm_images_metadata_file, 'w') as f:
            json.dump(vm_images, f, indent=2)
    
    async def load_build_metadata(self) -> Dict:
        """Load build metadata from file"""
        if self.build_metadata_file.exists():
            with open(self.build_metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def store_build_metadata(self, build_id: str, metadata: Dict):
        """Store build metadata"""
        builds = await self.load_build_metadata()
        builds[build_id] = metadata
        with open(self.build_metadata_file, 'w') as f:
            json.dump(builds, f, indent=2)
    
    async def load_container_registry(self) -> Dict:
        """Load container registry from file"""
        if self.container_registry_file.exists():
            with open(self.container_registry_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def store_container_registry(self, registry: Dict):
        """Store container registry to file"""
        with open(self.container_registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
    
    async def _check_docker_availability(self) -> Dict:
        """Check if Docker is available and running"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "available": True,
                    "version": stdout.decode().strip()
                }
            else:
                return {
                    "available": False,
                    "error": f"Docker command failed: {stderr.decode()}"
                }
                
        except FileNotFoundError:
            return {
                "available": False,
                "error": "Docker command not found. Please install Docker."
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking Docker availability: {str(e)}"
            }