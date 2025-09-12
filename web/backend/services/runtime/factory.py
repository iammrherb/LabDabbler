import json
import logging
from typing import Dict, List, Optional, Union, cast
from pathlib import Path

from .base import RuntimeProvider
from .local import LocalRuntimeProvider
from .ssh import SSHRuntimeProvider

logger = logging.getLogger(__name__)

class RuntimeProviderFactory:
    """Factory class for creating and managing runtime providers"""
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.config_file = self.data_dir / "runtime_config.json"
        self.providers: Dict[str, RuntimeProvider] = {}
        self.default_provider_name: Optional[str] = None
        
        # Initialize with default local provider if no config exists
        if not self.config_file.exists():
            self._create_default_config()
        
        # Load configuration
        self._load_config()
    
    def _create_default_config(self):
        """Create default configuration with local runtime provider"""
        default_config = {
            "default_provider": "local",
            "providers": {
                "local": {
                    "name": "local",
                    "type": "local",
                    "description": "Local containerlab runtime",
                    "enabled": True
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info("Created default runtime configuration")
    
    def _load_config(self):
        """Load runtime provider configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.default_provider_name = config.get("default_provider", "local")
            
            # Clear existing providers
            self.providers = {}
            
            # Create provider instances
            for provider_name, provider_config in config.get("providers", {}).items():
                if provider_config.get("enabled", True):
                    provider = self._create_provider(provider_config)
                    if provider:
                        self.providers[provider_name] = provider
            
            logger.info(f"Loaded {len(self.providers)} runtime providers")
            
        except Exception as e:
            logger.error(f"Failed to load runtime configuration: {e}")
            # Fallback to local provider only
            self.providers = {
                "local": LocalRuntimeProvider({"name": "local", "type": "local"})
            }
            self.default_provider_name = "local"
    
    def _create_provider(self, config: Dict) -> Optional[RuntimeProvider]:
        """Create a runtime provider instance from configuration"""
        try:
            provider_type = config.get("type")
            
            if provider_type == "local":
                return LocalRuntimeProvider(config)
            elif provider_type == "ssh":
                return SSHRuntimeProvider(config)
            else:
                logger.warning(f"Unknown provider type: {provider_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create provider {config.get('name', 'unknown')}: {e}")
            return None
    
    def get_provider(self, name: Optional[str] = None) -> Optional[RuntimeProvider]:
        """Get a runtime provider by name, or the default provider"""
        if name is None:
            name = self.default_provider_name
        
        # Handle None name case properly
        if name is None:
            return None
        return self.providers.get(name)
    
    def get_default_provider(self) -> Optional[RuntimeProvider]:
        """Get the default runtime provider"""
        return self.get_provider()
    
    def list_providers(self) -> List[Dict]:
        """List all available runtime providers"""
        providers = []
        for name, provider in self.providers.items():
            providers.append({
                "name": name,
                "type": provider.type,
                "is_default": name == self.default_provider_name,
                "config": provider.config
            })
        return providers
    
    def add_provider(self, config: Dict) -> bool:
        """Add a new runtime provider"""
        try:
            provider_name = config.get("name")
            if not provider_name:
                logger.error("Provider name is required")
                return False
            
            if provider_name in self.providers:
                logger.error(f"Provider {provider_name} already exists")
                return False
            
            # Create provider instance
            provider = self._create_provider(config)
            if not provider:
                return False
            
            # Add to providers
            self.providers[provider_name] = provider
            
            # Save configuration
            self._save_config()
            
            logger.info(f"Added runtime provider: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add provider: {e}")
            return False
    
    def remove_provider(self, name: str) -> bool:
        """Remove a runtime provider"""
        try:
            if name not in self.providers:
                logger.error(f"Provider {name} not found")
                return False
            
            if name == self.default_provider_name:
                logger.error(f"Cannot remove default provider {name}")
                return False
            
            # Close SSH connections if applicable
            provider = self.providers[name]
            if hasattr(provider, 'close_connection') and callable(getattr(provider, 'close_connection')):
                import asyncio
                asyncio.create_task(provider.close_connection())
            
            # Remove provider
            del self.providers[name]
            
            # Save configuration
            self._save_config()
            
            logger.info(f"Removed runtime provider: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove provider: {e}")
            return False
    
    def set_default_provider(self, name: str) -> bool:
        """Set the default runtime provider"""
        try:
            if name not in self.providers:
                logger.error(f"Provider {name} not found")
                return False
            
            self.default_provider_name = name
            self._save_config()
            
            logger.info(f"Set default runtime provider to: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set default provider: {e}")
            return False
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config = {
                "default_provider": self.default_provider_name,
                "providers": {}
            }
            
            for name, provider in self.providers.items():
                config["providers"][name] = provider.config.copy()
                config["providers"][name]["enabled"] = True
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save runtime configuration: {e}")
    
    async def check_all_providers_health(self) -> Dict:
        """Check health of all providers"""
        results = {}
        for name, provider in self.providers.items():
            try:
                health = await provider.check_health()
                health["provider_name"] = name
                results[name] = health
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "provider_name": name
                }
        return results