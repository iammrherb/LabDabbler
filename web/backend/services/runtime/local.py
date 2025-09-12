import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from .base import RuntimeProvider

logger = logging.getLogger(__name__)

class LocalRuntimeProvider(RuntimeProvider):
    """Local runtime provider for containerlab execution"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.type = "local"
    
    async def check_health(self) -> Dict:
        """Check if the local runtime environment is healthy"""
        try:
            docker_available = await self.check_docker()
            containerlab_available = await self.check_containerlab()
            
            healthy = docker_available and containerlab_available
            
            result = {
                "healthy": healthy,
                "docker_available": docker_available,
                "containerlab_available": containerlab_available,
                "runtime_type": "local",
                "name": self.name
            }
            
            if not healthy:
                errors = []
                if not docker_available:
                    errors.append("Docker not available")
                if not containerlab_available:
                    errors.append("Containerlab not available")
                result["error"] = "; ".join(errors)
            
            return result
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "docker_available": False,
                "containerlab_available": False,
                "runtime_type": "local",
                "name": self.name,
                "error": str(e)
            }
    
    async def execute_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Execute a command locally"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return (
                process.returncode or 0,
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore')
            )
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return 1, "", str(e)
    
    async def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload file locally (copy operation)"""
        try:
            # For local provider, this is just a copy operation
            import shutil
            shutil.copy2(local_path, remote_path)
            return True
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return False
    
    async def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download file locally (copy operation)"""
        try:
            # For local provider, this is just a copy operation
            import shutil
            shutil.copy2(remote_path, local_path)
            return True
        except Exception as e:
            logger.error(f"File download failed: {e}")
            return False