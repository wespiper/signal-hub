"""Tests for secure key management."""

import tempfile
from pathlib import Path

import pytest

from signal_hub.security.keys import SecureKeyManager, KeyProvider


class TestSecureKeyManager:
    """Test secure key management."""
    
    @pytest.fixture
    def key_manager(self):
        """Create test key manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_file = Path(tmpdir) / "keys.enc"
            master_key_file = Path(tmpdir) / ".master_key"
            
            manager = SecureKeyManager(
                key_file=key_file,
                master_key_file=master_key_file
            )
            yield manager
    
    def test_set_and_get_key(self, key_manager):
        """Test setting and retrieving API key."""
        # Set key
        key_manager.set_key(KeyProvider.OPENAI, "sk-test-key-123")
        
        # Get key
        retrieved = key_manager.get_key(KeyProvider.OPENAI)
        assert retrieved == "sk-test-key-123"
        
    def test_key_encryption(self, key_manager):
        """Test keys are encrypted on disk."""
        # Set key
        key_manager.set_key(KeyProvider.ANTHROPIC, "secret-key")
        
        # Read raw file
        with open(key_manager.key_file, "rb") as f:
            raw_content = f.read()
        
        # Should not contain plain text key
        assert b"secret-key" not in raw_content
        
    def test_remove_key(self, key_manager):
        """Test removing keys."""
        # Set key
        key_manager.set_key(KeyProvider.OPENAI, "test-key")
        
        # Remove key
        removed = key_manager.remove_key(KeyProvider.OPENAI)
        assert removed is True
        
        # Try to get removed key
        assert key_manager.get_key(KeyProvider.OPENAI) is None
        
    def test_list_providers(self, key_manager):
        """Test listing providers with keys."""
        # Set multiple keys
        key_manager.set_key(KeyProvider.OPENAI, "key1")
        key_manager.set_key(KeyProvider.ANTHROPIC, "key2")
        
        providers = key_manager.list_providers()
        assert KeyProvider.OPENAI in providers
        assert KeyProvider.ANTHROPIC in providers
        assert len(providers) == 2
        
    def test_rotation_tracking(self, key_manager):
        """Test key rotation tracking."""
        # Set key
        key_manager.set_key(KeyProvider.OPENAI, "old-key")
        
        # Get key info
        info = key_manager.export_public_info()
        assert KeyProvider.OPENAI.value in info
        assert "rotation_date" in info[KeyProvider.OPENAI.value]
        
    def test_environment_override(self, key_manager, monkeypatch):
        """Test environment variable override."""
        # Set environment variable
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        
        # Environment key should take precedence
        key = key_manager.get_key(KeyProvider.OPENAI)
        assert key == "env-key"
        
    def test_persistence(self):
        """Test keys persist across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_file = Path(tmpdir) / "keys.enc"
            master_key_file = Path(tmpdir) / ".master_key"
            
            # First instance - set key
            manager1 = SecureKeyManager(key_file, master_key_file)
            manager1.set_key(KeyProvider.OPENAI, "persistent-key")
            
            # Second instance - get key
            manager2 = SecureKeyManager(key_file, master_key_file)
            retrieved = manager2.get_key(KeyProvider.OPENAI)
            
            assert retrieved == "persistent-key"