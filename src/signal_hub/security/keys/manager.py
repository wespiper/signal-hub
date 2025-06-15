"""Secure API key management with encryption."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet
from pydantic import SecretStr

from signal_hub.utils.logging import get_logger
from .models import APIKey, KeyProvider


logger = get_logger(__name__)


class SecureKeyManager:
    """Manages API keys with encryption."""
    
    def __init__(
        self,
        key_file: Optional[Path] = None,
        master_key_file: Optional[Path] = None,
        rotation_days: int = 90
    ):
        """
        Initialize secure key manager.
        
        Args:
            key_file: Path to encrypted keys file
            master_key_file: Path to master encryption key
            rotation_days: Days before key rotation reminder
        """
        self.key_file = key_file or self._get_default_key_file()
        self.master_key_file = master_key_file or self._get_default_master_key_file()
        self.rotation_days = rotation_days
        self.cipher = Fernet(self._get_or_create_master_key())
        self._keys: Dict[KeyProvider, APIKey] = {}
        self._load_keys()
    
    def _get_default_key_file(self) -> Path:
        """Get default key file path."""
        home = Path.home()
        signal_hub_dir = home / ".signal-hub"
        signal_hub_dir.mkdir(exist_ok=True)
        return signal_hub_dir / "keys.enc"
    
    def _get_default_master_key_file(self) -> Path:
        """Get default master key file path."""
        home = Path.home()
        signal_hub_dir = home / ".signal-hub"
        return signal_hub_dir / ".master_key"
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key."""
        # Check environment variable first
        if master_key := os.environ.get("SIGNAL_HUB_MASTER_KEY"):
            return master_key.encode()
        
        # Check file
        if self.master_key_file.exists():
            with open(self.master_key_file, "rb") as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save to file with restricted permissions
        self.master_key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.master_key_file, "wb") as f:
            f.write(key)
        
        # Set restrictive permissions (owner read only)
        os.chmod(self.master_key_file, 0o400)
        
        logger.info(f"Generated new master key at {self.master_key_file}")
        return key
    
    def _load_keys(self) -> None:
        """Load keys from encrypted file."""
        if not self.key_file.exists():
            return
        
        try:
            with open(self.key_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            keys_data = json.loads(decrypted_data)
            
            for provider_str, key_data in keys_data.items():
                provider = KeyProvider(provider_str)
                self._keys[provider] = APIKey(**key_data)
            
            logger.info(f"Loaded {len(self._keys)} API keys")
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
    
    def _save_keys(self) -> None:
        """Save keys to encrypted file."""
        try:
            # Convert keys to dict
            keys_data = {}
            for provider, api_key in self._keys.items():
                # Get the secret value for serialization
                key_dict = api_key.dict()
                key_dict["key"] = api_key.key.get_secret_value()
                keys_data[provider.value] = key_dict
            
            # Encrypt and save
            json_data = json.dumps(keys_data, default=str)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Save with restricted permissions
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, "wb") as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            
            logger.debug(f"Saved {len(self._keys)} API keys")
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
    
    def set_key(self, provider: KeyProvider, key: str) -> None:
        """
        Set or update an API key.
        
        Args:
            provider: API provider
            key: The API key to store
        """
        api_key = APIKey(
            provider=provider,
            key=SecretStr(key),
            created_at=datetime.utcnow(),
            rotation_date=datetime.utcnow() + timedelta(days=self.rotation_days)
        )
        
        self._keys[provider] = api_key
        self._save_keys()
        
        logger.info(f"Set API key for {provider}")
    
    def get_key(self, provider: KeyProvider) -> Optional[str]:
        """
        Get an API key.
        
        Args:
            provider: API provider
            
        Returns:
            The API key or None if not found
        """
        # Check environment variable first
        env_var = f"{provider.value.upper()}_API_KEY"
        if env_key := os.environ.get(env_var):
            return env_key
        
        # Check stored keys
        if api_key := self._keys.get(provider):
            # Update last used
            api_key.last_used = datetime.utcnow()
            self._save_keys()
            
            # Check rotation
            if api_key.rotation_date and datetime.utcnow() > api_key.rotation_date:
                logger.warning(f"API key for {provider} is due for rotation")
            
            return api_key.key.get_secret_value()
        
        return None
    
    def remove_key(self, provider: KeyProvider) -> bool:
        """
        Remove an API key.
        
        Args:
            provider: API provider
            
        Returns:
            True if key was removed
        """
        if provider in self._keys:
            del self._keys[provider]
            self._save_keys()
            logger.info(f"Removed API key for {provider}")
            return True
        return False
    
    def list_providers(self) -> list[KeyProvider]:
        """List providers with stored keys."""
        return list(self._keys.keys())
    
    def check_rotation(self) -> Dict[KeyProvider, datetime]:
        """
        Check which keys need rotation.
        
        Returns:
            Dict of providers and their rotation dates
        """
        needs_rotation = {}
        
        for provider, api_key in self._keys.items():
            if api_key.rotation_date and datetime.utcnow() > api_key.rotation_date:
                needs_rotation[provider] = api_key.rotation_date
        
        return needs_rotation
    
    def rotate_key(self, provider: KeyProvider, new_key: str) -> None:
        """
        Rotate an API key.
        
        Args:
            provider: API provider
            new_key: New API key
        """
        self.set_key(provider, new_key)
        logger.info(f"Rotated API key for {provider}")
    
    def export_public_info(self) -> Dict[str, Dict[str, str]]:
        """
        Export public information about keys (no secrets).
        
        Returns:
            Dict with key metadata
        """
        info = {}
        
        for provider, api_key in self._keys.items():
            info[provider.value] = {
                "created_at": api_key.created_at.isoformat(),
                "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                "rotation_date": api_key.rotation_date.isoformat() if api_key.rotation_date else None,
                "needs_rotation": bool(
                    api_key.rotation_date and datetime.utcnow() > api_key.rotation_date
                )
            }
        
        return info