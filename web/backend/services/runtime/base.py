from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class RuntimeProvider(ABC):
    """Abstract base class for containerlab runtime providers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = config.get("name", "unknown")
        self.type = config.get("type", "unknown")
    
    @abstractmethod
    async def check_health(self) -> Dict:
        """Check if the runtime environment is healthy
        
        Returns:
            Dict with 'healthy' bool, 'docker_available' bool, 'containerlab_available' bool,
            and optional 'error' message
        """
        pass
    
    @abstractmethod
    async def execute_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Execute a command on the runtime environment
        
        Args:
            command: List of command parts (e.g., ['docker', 'info'])
            cwd: Working directory for command execution
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        pass
    
    @abstractmethod
    async def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to the runtime environment
        
        Args:
            local_path: Path to local file
            remote_path: Path on remote system
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    async def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from the runtime environment
        
        Args:
            remote_path: Path on remote system
            local_path: Path to save locally
            
        Returns:
            bool: True if successful
        """
        pass
    
    async def check_containerlab(self) -> bool:
        """Check if containerlab is available on this runtime"""
        try:
            return_code, stdout, stderr = await self.execute_command(["containerlab", "version"])
            return return_code == 0
        except Exception:
            return False
    
    async def check_docker(self) -> bool:
        """Check if Docker is available on this runtime"""
        try:
            return_code, stdout, stderr = await self.execute_command(["docker", "info"])
            return return_code == 0
        except Exception:
            return False

    async def close_connection(self) -> None:
        """Close connection to runtime provider (optional, for cleanup)"""
        # Default implementation does nothing - SSH providers can override
        pass