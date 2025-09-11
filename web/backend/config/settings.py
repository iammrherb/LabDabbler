"""
Production settings for LabDabbler backend
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

class ProductionSettings:
    """Production configuration settings"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / "production.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    @property
    def app_config(self) -> Dict[str, Any]:
        """Application configuration"""
        return self.config.get('app', {})
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """Server configuration"""
        return self.config.get('server', {})
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Database configuration"""
        return self.config.get('database', {})
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Security configuration"""
        return self.config.get('security', {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Logging configuration"""
        return self.config.get('logging', {})
    
    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Monitoring configuration"""
        return self.config.get('monitoring', {})
    
    @property
    def cache_config(self) -> Dict[str, Any]:
        """Cache configuration"""
        return self.config.get('cache', {})
    
    @property
    def performance_config(self) -> Dict[str, Any]:
        """Performance configuration"""
        return self.config.get('performance', {})

# Environment variables with defaults
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://labdabbler_user:password@localhost:5432/labdabbler')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
JWT_SECRET = os.getenv('JWT_SECRET', 'your-jwt-secret-here')

# Load production settings
settings = ProductionSettings()