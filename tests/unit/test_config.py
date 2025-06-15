"""Unit tests for configuration system."""

import pytest
import os
from pathlib import Path
import tempfile
import yaml

from signal_hub.config.settings import (
    Settings, ServerSettings, LoggingSettings, VectorStoreSettings,
    EmbeddingSettings, CacheSettings, ModelSettings, Edition, VectorStoreType
)
from signal_hub.config.loader import (
    load_yaml_config, merge_configs, load_config, validate_config
)


class TestSettings:
    """Test Settings model."""
    
    def test_default_settings(self):
        """Test default settings creation."""
        settings = Settings()
        
        assert settings.edition == Edition.BASIC
        assert settings.early_access is False
        assert settings.env == "development"
        assert settings.debug is False
        assert settings.server.port == 3333
        assert settings.logging.level == "INFO"
    
    def test_settings_from_dict(self):
        """Test creating settings from dictionary."""
        config = {
            "edition": "pro",
            "early_access": True,
            "server": {
                "host": "0.0.0.0",
                "port": 4444
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        settings = Settings(**config)
        
        assert settings.edition == Edition.PRO
        assert settings.early_access is True
        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 4444
        assert settings.logging.level == "DEBUG"
    
    def test_edition_parsing(self):
        """Test edition string parsing."""
        settings = Settings(edition="enterprise")
        assert settings.edition == Edition.ENTERPRISE
        
        settings = Settings(edition=Edition.PRO)
        assert settings.edition == Edition.PRO
    
    def test_bool_parsing(self):
        """Test boolean string parsing."""
        settings = Settings(early_access="true")
        assert settings.early_access is True
        
        settings = Settings(early_access="false")
        assert settings.early_access is False
        
        settings = Settings(early_access="yes")
        assert settings.early_access is True
        
        settings = Settings(early_access="0")
        assert settings.early_access is False
    
    def test_get_server_name(self):
        """Test server name generation."""
        settings = Settings(edition="basic")
        assert settings.get_server_name() == "Signal Hub Basic"
        
        settings = Settings(edition="pro")
        assert settings.get_server_name() == "Signal Hub Pro"
        
        settings = Settings(edition="enterprise")
        assert settings.get_server_name() == "Signal Hub Enterprise"
        
        settings = Settings(early_access=True)
        assert settings.get_server_name() == "Signal Hub (Early Access)"


class TestSubSettings:
    """Test sub-settings models."""
    
    def test_server_settings(self):
        """Test ServerSettings."""
        settings = ServerSettings(
            host="127.0.0.1",
            port=5555,
            name="Test Server"
        )
        
        assert settings.host == "127.0.0.1"
        assert settings.port == 5555
        assert settings.name == "Test Server"
        assert settings.health_check_enabled is True
    
    def test_logging_settings_validation(self):
        """Test LoggingSettings validation."""
        # Valid level
        settings = LoggingSettings(level="debug")
        assert settings.level == "DEBUG"
        
        # Invalid level
        with pytest.raises(ValueError) as exc_info:
            LoggingSettings(level="invalid")
        assert "Invalid log level" in str(exc_info.value)
    
    def test_cache_settings_validation(self):
        """Test CacheSettings validation."""
        # Valid threshold
        settings = CacheSettings(similarity_threshold=0.85)
        assert settings.similarity_threshold == 0.85
        
        # Invalid threshold
        with pytest.raises(ValueError) as exc_info:
            CacheSettings(similarity_threshold=1.5)
        assert "between 0 and 1" in str(exc_info.value)
    
    def test_model_settings_validation(self):
        """Test ModelSettings validation."""
        # Valid thresholds
        settings = ModelSettings(
            haiku_threshold=0.3,
            sonnet_threshold=0.7
        )
        assert settings.haiku_threshold == 0.3
        assert settings.sonnet_threshold == 0.7
        
        # Invalid threshold
        with pytest.raises(ValueError) as exc_info:
            ModelSettings(haiku_threshold=1.5)
        assert "between 0 and 1" in str(exc_info.value)


class TestConfigLoader:
    """Test configuration loader functions."""
    
    def test_load_yaml_config(self):
        """Test loading YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "edition": "pro",
                "server": {
                    "port": 6666
                }
            }, f)
            temp_path = Path(f.name)
        
        try:
            config = load_yaml_config(temp_path)
            assert config["edition"] == "pro"
            assert config["server"]["port"] == 6666
        finally:
            temp_path.unlink()
    
    def test_load_yaml_config_not_found(self):
        """Test loading non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config(Path("/non/existent/file.yaml"))
    
    def test_merge_configs(self):
        """Test configuration merging."""
        base = {
            "edition": "basic",
            "server": {
                "host": "localhost",
                "port": 3333
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        override = {
            "edition": "pro",
            "server": {
                "port": 4444
            }
        }
        
        merged = merge_configs(base, override)
        
        assert merged["edition"] == "pro"
        assert merged["server"]["host"] == "localhost"  # Preserved
        assert merged["server"]["port"] == 4444  # Overridden
        assert merged["logging"]["level"] == "INFO"  # Preserved
    
    def test_load_config_with_file(self):
        """Test loading configuration from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "edition": "enterprise",
                "debug": True
            }, f)
            temp_path = Path(f.name)
        
        try:
            settings = load_config(temp_path)
            assert settings.edition == Edition.ENTERPRISE
            assert settings.debug is True
        finally:
            temp_path.unlink()
    
    def test_load_config_with_overrides(self):
        """Test loading configuration with overrides."""
        overrides = {
            "edition": "pro",
            "server": {
                "port": 7777
            }
        }
        
        settings = load_config(overrides=overrides)
        assert settings.edition == Edition.PRO
        assert settings.server.port == 7777
    
    def test_load_config_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("SIGNAL_HUB_EDITION", "enterprise")
        monkeypatch.setenv("SIGNAL_HUB_SERVER_PORT", "8888")
        
        settings = load_config()
        assert settings.edition == Edition.ENTERPRISE
        assert settings.server.port == 8888


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_missing_openai_key(self):
        """Test validation with missing OpenAI key."""
        settings = Settings(
            embeddings=EmbeddingSettings(
                provider="openai",
                openai_api_key=None
            )
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(settings)
        assert "OpenAI API key required" in str(exc_info.value)
    
    def test_validate_missing_anthropic_key(self):
        """Test validation with missing Anthropic key."""
        settings = Settings(
            models=ModelSettings(anthropic_api_key=None)
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(settings)
        assert "Anthropic API key required" in str(exc_info.value)
    
    def test_validate_pgvector_missing_url(self):
        """Test validation with pgvector but no database URL."""
        settings = Settings(
            vector_store=VectorStoreSettings(
                type=VectorStoreType.PGVECTOR,
                database_url=None
            )
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(settings)
        assert "Database URL required for pgvector" in str(exc_info.value)
    
    def test_validate_pro_missing_license(self):
        """Test validation with Pro edition but no license."""
        settings = Settings(
            edition=Edition.PRO,
            early_access=False,
            license_key=None
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(settings)
        assert "License key required for pro edition" in str(exc_info.value)
    
    def test_validate_pro_with_early_access(self):
        """Test Pro edition validation passes with early access."""
        settings = Settings(
            edition=Edition.PRO,
            early_access=True,
            license_key=None,
            embeddings=EmbeddingSettings(openai_api_key="test"),
            models=ModelSettings(anthropic_api_key="test")
        )
        
        # Should not raise
        validate_config(settings)
    
    def test_validate_threshold_order(self):
        """Test validation of model thresholds."""
        settings = Settings(
            models=ModelSettings(
                haiku_threshold=0.8,
                sonnet_threshold=0.3,
                anthropic_api_key="test"
            ),
            embeddings=EmbeddingSettings(openai_api_key="test")
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(settings)
        assert "Haiku threshold must be less than Sonnet threshold" in str(exc_info.value)