"""Configuration loader for Signal Hub."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from signal_hub.config.settings import Settings
from signal_hub.utils.logging import get_logger

logger = get_logger(__name__)


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    logger.debug(f"Loading configuration from {path}")
    
    with open(path, 'r') as f:
        try:
            config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {path}")
            return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        base: Base configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def load_config(
    config_path: Optional[Path] = None,
    overrides: Optional[Dict[str, Any]] = None
) -> Settings:
    """
    Load Signal Hub configuration from multiple sources.
    
    Priority order (highest to lowest):
    1. Command line overrides
    2. Environment variables
    3. Configuration file
    4. Default values
    
    Args:
        config_path: Optional path to configuration file
        overrides: Optional configuration overrides
        
    Returns:
        Loaded configuration settings
    """
    config_dict = {}
    
    # Load from config file if provided
    if config_path:
        try:
            config_dict = load_yaml_config(config_path)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}. Using defaults.")
    
    # Apply overrides
    if overrides:
        config_dict = merge_configs(config_dict, overrides)
    
    # Create settings instance (will also load from environment)
    settings = Settings(**config_dict)
    
    # Log configuration summary
    logger.info(f"Loaded configuration for {settings.get_server_name()}")
    logger.debug(f"Edition: {settings.edition.value}")
    logger.debug(f"Early Access: {settings.early_access}")
    logger.debug(f"Environment: {settings.env}")
    logger.debug(f"Server: {settings.server.host}:{settings.server.port}")
    
    return settings


def get_default_config_path() -> Path:
    """
    Get the default configuration file path.
    
    Returns:
        Default config path
    """
    # Check environment variable first
    env_path = os.getenv("SIGNAL_HUB_CONFIG")
    if env_path:
        return Path(env_path)
    
    # Check common locations
    possible_paths = [
        Path("config/dev.yaml"),
        Path("config/prod.yaml"),
        Path("config.yaml"),
        Path.home() / ".signal-hub" / "config.yaml",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Default to dev config
    return Path("config/dev.yaml")


def validate_config(settings: Settings) -> None:
    """
    Validate configuration settings.
    
    Args:
        settings: Configuration settings to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate API keys for required services
    if settings.embeddings.provider == "openai" and not settings.embeddings.openai_api_key:
        raise ValueError("OpenAI API key required for OpenAI embeddings")
    
    if not settings.models.anthropic_api_key:
        raise ValueError("Anthropic API key required for Claude models")
    
    # Validate vector store configuration
    if settings.vector_store.type == "pgvector" and not settings.vector_store.database_url:
        raise ValueError("Database URL required for pgvector")
    
    # Validate edition-specific requirements
    if settings.edition in ["pro", "enterprise"] and not settings.license_key:
        if not settings.early_access:
            raise ValueError(f"License key required for {settings.edition} edition")
    
    # Validate model thresholds
    if settings.models.haiku_threshold >= settings.models.sonnet_threshold:
        raise ValueError("Haiku threshold must be less than Sonnet threshold")
    
    logger.info("Configuration validation passed")