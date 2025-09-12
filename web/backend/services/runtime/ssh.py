import asyncio
import asyncssh
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from .base import RuntimeProvider

logger = logging.getLogger(__name__)

class SSHRuntimeProvider(RuntimeProvider):
    """SSH-based runtime provider for remote containerlab execution"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.type = "ssh"
        
        # SSH connection parameters
        self.host = config.get("host")
        self.port = config.get("port", 22)
        self.username = config.get("username")
        self.password = config.get("password")
        self.private_key_path = config.get("private_key_path")
        self.known_hosts = config.get("known_hosts", None)
        
        # Connection pool
        self._connection = None
        self._connection_lock = asyncio.Lock()
    
    async def _get_connection(self):
        """Get or create SSH connection"""
        async with self._connection_lock:
            # Check if connection exists and is usable
            connection_valid = False
            if self._connection is not None:
                try:
                    # Test if connection is still valid by checking its state
                    connection_valid = True  # Assume valid if it exists and doesn't raise exception
                except (AttributeError, Exception):
                    connection_valid = False
            
            if not connection_valid:
                try:
                    connect_kwargs = {
                        "host": self.host,
                        "port": self.port,
                        "username": self.username,
                        "known_hosts": self.known_hosts
                    }
                    
                    # Add authentication method
                    if self.private_key_path:
                        connect_kwargs["client_keys"] = [self.private_key_path]
                    elif self.password:
                        connect_kwargs["password"] = self.password
                    
                    self._connection = await asyncssh.connect(**connect_kwargs)
                    logger.info(f"SSH connection established to {self.host}:{self.port}")
                    
                except Exception as e:
                    logger.error(f"Failed to establish SSH connection to {self.host}:{self.port}: {e}")
                    raise
            
            return self._connection
    
    async def close_connection(self):
        """Close SSH connection"""
        async with self._connection_lock:
            connection_valid = False
            if self._connection is not None:
                try:
                    # Test connection validity before closing
                    connection_valid = hasattr(self._connection, 'close')
                except (AttributeError, Exception):
                    connection_valid = False
                    
            if self._connection and connection_valid:
                self._connection.close()
                await self._connection.wait_closed()
                self._connection = None
                logger.info(f"SSH connection closed to {self.host}:{self.port}")
    
    async def check_health(self) -> Dict:
        """Check if the remote runtime environment is healthy"""
        try:
            # Test SSH connection
            connection = await self._get_connection()
            
            # Check Docker
            docker_available = await self.check_docker()
            
            # Check Containerlab
            containerlab_available = await self.check_containerlab()
            
            healthy = docker_available and containerlab_available
            
            result = {
                "healthy": healthy,
                "docker_available": docker_available,
                "containerlab_available": containerlab_available,
                "runtime_type": "ssh",
                "name": self.name,
                "host": self.host,
                "port": self.port,
                "username": self.username
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
            logger.error(f"SSH health check failed for {self.host}: {e}")
            return {
                "healthy": False,
                "docker_available": False,
                "containerlab_available": False,
                "runtime_type": "ssh",
                "name": self.name,
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "error": str(e)
            }
    
    async def execute_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Execute a command on the remote host via SSH"""
        try:
            connection = await self._get_connection()
            if connection is None:
                raise RuntimeError("Failed to establish SSH connection")
            
            # Build command string
            cmd_str = " ".join(command)
            if cwd:
                cmd_str = f"cd {cwd} && {cmd_str}"
            
            # Execute command
            result = await connection.run(cmd_str, check=False)
            
            # Handle type conversions for asyncssh result
            exit_code = result.exit_status if result.exit_status is not None else 1
            
            # Convert stdout to string, handling various types
            if isinstance(result.stdout, (bytes, bytearray, memoryview)):
                stdout_str = bytes(result.stdout).decode('utf-8', errors='replace')
            else:
                stdout_str = str(result.stdout) if result.stdout is not None else ""
            
            # Convert stderr to string, handling various types
            if isinstance(result.stderr, (bytes, bytearray, memoryview)):
                stderr_str = bytes(result.stderr).decode('utf-8', errors='replace')
            else:
                stderr_str = str(result.stderr) if result.stderr is not None else ""
            
            return (exit_code, stdout_str, stderr_str)
            
        except Exception as e:
            logger.error(f"SSH command execution failed: {e}")
            return 1, "", str(e)
    
    async def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to the remote host via SFTP"""
        try:
            connection = await self._get_connection()
            if connection is None:
                raise RuntimeError("Failed to establish SSH connection")
            
            async with connection.start_sftp_client() as sftp:
                await sftp.put(str(local_path), remote_path)
                logger.info(f"Uploaded {local_path} to {self.host}:{remote_path}")
                return True
                
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return False
    
    async def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from the remote host via SFTP"""
        try:
            connection = await self._get_connection()
            if connection is None:
                raise RuntimeError("Failed to establish SSH connection")
            
            async with connection.start_sftp_client() as sftp:
                await sftp.get(remote_path, str(local_path))
                logger.info(f"Downloaded {self.host}:{remote_path} to {local_path}")
                return True
                
        except Exception as e:
            logger.error(f"File download failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup SSH connection on destruction"""
        if hasattr(self, '_connection') and self._connection is not None:
            try:
                # Schedule cleanup
                asyncio.create_task(self.close_connection())
            except Exception:
                pass  # Ignore cleanup errors during destruction