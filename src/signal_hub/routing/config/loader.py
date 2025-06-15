"""Configuration loader for routing system."""

import os
from pathlib import Path
from typing import Dict, Optional

import yaml

from signal_hub.utils.logging import get_logger
from .defaults import get_default_config
from .merger import ConfigMerger
from .schema import RoutingConfig
from .validator import ConfigValidator


logger = get_logger(__name__)


class RoutingConfigLoader:
    """Loads and manages routing configuration."""
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        auto_reload: bool = False
    ):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to user configuration file
            auto_reload: Whether to watch for config changes
        """
        self.config_path = config_path or self._get_default_config_path()
        self.auto_reload = auto_reload
        self.merger = ConfigMerger()
        self.validator = ConfigValidator()
        self._cached_config: Optional[RoutingConfig] = None
        self._last_modified: Optional[float] = None
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path."""
        # Check common locations
        locations = [
            Path("config/routing.yaml"),
            Path.home() / ".signal-hub" / "routing.yaml",
            Path("/etc/signal-hub/routing.yaml"),
        ]
        
        for location in locations:
            if location.exists():
                return location
        
        # Default to first location
        return locations[0]
    
    def load(self) -> RoutingConfig:
        """
        Load configuration from all sources.
        
        Returns:
            Merged and validated configuration
        """
        # Check cache and auto-reload
        if self._cached_config and not self._should_reload():
            return self._cached_config
        
        # 1. Start with defaults
        config = get_default_config()
        logger.debug("Loaded default configuration")
        
        # 2. Merge user configuration if exists
        if self.config_path.exists():
            user_config = self._load_user_config()
            if user_config:
                config = self.merger.merge(config, user_config)
                logger.info(f"Loaded user configuration from {self.config_path}")
        
        # 3. Apply environment overrides
        config = self.merger.merge_environment_vars(config, os.environ)
        logger.debug("Applied environment variable overrides")
        
        # 4. Validate final configuration
        try:
            self.validator.assert_valid(config)
            logger.debug("Configuration validation passed")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            # Fall back to defaults on validation failure
            logger.warning("Falling back to default configuration")
            config = get_default_config()
        
        # Cache the configuration
        self._cached_config = config
        if self.config_path.exists():
            self._last_modified = self.config_path.stat().st_mtime
        
        return config
    
    def _should_reload(self) -> bool:
        """Check if configuration should be reloaded."""
        if not self.auto_reload:
            return False
        
        if not self.config_path.exists():
            return False
        
        current_mtime = self.config_path.stat().st_mtime
        return current_mtime != self._last_modified
    
    def _load_user_config(self) -> Optional[Dict]:
        """Load user configuration from file."""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load user configuration: {e}")
            return None
    
    def reload(self) -> RoutingConfig:
        """Force reload configuration."""
        self._cached_config = None
        self._last_modified = None
        return self.load()
    
    def save_example(self, path: Optional[Path] = None) -> None:
        """
        Save example configuration file.
        
        Args:
            path: Where to save (defaults to config_path)
        """
        path = path or self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get default config and convert to dict
        config = get_default_config()
        config_dict = config.dict()
        
        # Add helpful comments
        config_with_comments = f"""# Signal Hub Routing Configuration
# This file configures how queries are routed to different models

# Model-specific settings
models:
  haiku:
    max_tokens: {config_dict['models']['haiku']['max_tokens']}
    max_complexity: {config_dict['models']['haiku']['max_complexity']}
    preferred_tasks: {config_dict['models']['haiku']['preferred_tasks']}
    
  sonnet:
    max_tokens: {config_dict['models']['sonnet']['max_tokens']}
    max_complexity: {config_dict['models']['sonnet']['max_complexity']}
    preferred_tasks: {config_dict['models']['sonnet']['preferred_tasks']}
    
  opus:
    max_tokens: {config_dict['models']['opus']['max_tokens'] or 'null'}
    max_complexity: {config_dict['models']['opus']['max_complexity']}
    preferred_tasks: {config_dict['models']['opus']['preferred_tasks']}

# Routing rules (evaluated in priority order)
rules:
  - name: length_based
    enabled: true
    priority: 1
    thresholds:
      haiku: {config_dict['rules'][0]['thresholds']['haiku']}
      sonnet: {config_dict['rules'][0]['thresholds']['sonnet']}
      
  - name: complexity_based
    enabled: true
    priority: 2
    indicators:
      simple: ["what", "when", "where", "list", "find"]
      moderate: ["how", "why", "explain", "describe"]
      complex: ["analyze", "design", "optimize", "refactor"]
      
  - name: task_type
    enabled: true
    priority: 3
    mappings:
      search_code: haiku
      explain_code: sonnet
      analyze_architecture: opus

# Pattern-based overrides (always take precedence)
overrides:
  - pattern: "security|vulnerability"
    model: opus
    reason: "Security requires careful analysis"

# Global settings
default_model: {config_dict['default_model']}
cache_similarity_threshold: {config_dict['cache_similarity_threshold']}
enable_escalation: {str(config_dict['enable_escalation']).lower()}
"""
        
        with open(path, "w") as f:
            f.write(config_with_comments)
        
        logger.info(f"Saved example configuration to {path}")