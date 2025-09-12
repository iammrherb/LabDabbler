"""
Secrets management utilities for LabDabbler production
"""
import os
import base64
import secrets
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """Secure secrets management"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        # Try to get from environment
        master_key = os.getenv('LABDABBLER_MASTER_KEY')
        if master_key:
            try:
                return base64.urlsafe_b64decode(master_key.encode())
            except Exception as e:
                logger.warning(f"Invalid master key in environment: {e}")
        
        # Generate new key
        logger.warning("Generating new master key. Existing encrypted data will be inaccessible.")
        return Fernet.generate_key()
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret"""
        try:
            encrypted = self.cipher.encrypt(secret.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt secret: {e}")
            raise
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_secret.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            raise
    
    def generate_api_key(self, length: int = 32) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(length)
    
    def generate_jwt_secret(self, length: int = 32) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(length)

class EnvironmentSecrets:
    """Environment-based secrets management"""
    
    def __init__(self):
        self.secrets_cache: Dict[str, Any] = {}
        self.load_secrets()
    
    def load_secrets(self):
        """Load secrets from environment variables"""
        secret_mappings = {
            'database_password': 'DATABASE_PASSWORD',
            'redis_password': 'REDIS_PASSWORD',
            'secret_key': 'SECRET_KEY',
            'jwt_secret': 'JWT_SECRET',
            'grafana_password': 'GRAFANA_PASSWORD',
        }
        
        for key, env_var in secret_mappings.items():
            value = os.getenv(env_var)
            if not value:
                logger.warning(f"Secret '{key}' not found in environment variable '{env_var}'")
                # Generate a default value for development
                value = secrets.token_urlsafe(32)
                logger.info(f"Generated temporary secret for '{key}' - set {env_var} in production")
            
            self.secrets_cache[key] = value
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret by key"""
        return self.secrets_cache.get(key)
    
    def get_database_url(self) -> str:
        """Get complete database URL with password"""
        base_url = os.getenv('DATABASE_URL', 'postgresql://labdabbler_user:{}@postgres:5432/labdabbler_production')
        password = self.get_secret('database_password')
        return base_url.format(password)
    
    def get_redis_url(self) -> str:
        """Get complete Redis URL with password"""
        base_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        
        # If the URL already includes password (redis://:password@host:port/db), return as is
        if '@' in base_url and ':' in base_url.split('@')[0]:
            return base_url
        
        # Otherwise, construct URL with password from environment
        redis_password = self.get_secret('redis_password')
        if redis_password and not base_url.startswith('redis://:'):
            # Parse the base URL and inject password
            if base_url.startswith('redis://'):
                # Replace redis:// with redis://:password@
                return base_url.replace('redis://', f'redis://:{redis_password}@')
        
        return base_url

# Global instance
secrets_manager = SecretsManager()
env_secrets = EnvironmentSecrets()

def get_secret(key: str) -> Optional[str]:
    """Convenience function to get a secret"""
    return env_secrets.get_secret(key)

def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename for uploads"""
    # Remove path components
    basename = os.path.basename(original_filename)
    
    # Get file extension
    name, ext = os.path.splitext(basename)
    
    # Generate secure prefix
    secure_prefix = secrets.token_hex(16)
    
    # Create secure filename
    return f"{secure_prefix}_{name[:50]}{ext}"

def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not input_string:
        return ""
    
    # Remove null bytes
    sanitized = input_string.replace('\x00', '')
    
    # Limit length
    sanitized = sanitized[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\r', '\n']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()