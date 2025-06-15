"""Tests for routing configuration system."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from signal_hub.routing.config import (
    RoutingConfigLoader,
    RoutingConfig,
    ConfigValidator,
)
from signal_hub.routing.config.defaults import get_default_config
from signal_hub.routing.config.merger import ConfigMerger
from signal_hub.routing.models import ModelType


class TestRoutingConfig:
    """Test routing configuration schema."""
    
    def test_default_config_valid(self):
        """Test default configuration is valid."""
        config = get_default_config()
        validator = ConfigValidator()
        
        issues = validator.validate(config)
        assert len(issues) == 0
        
    def test_rule_priority_ordering(self):
        """Test rules are sorted by priority."""
        config = get_default_config()
        
        enabled_rules = config.get_enabled_rules()
        priorities = [r.priority for r in enabled_rules]
        
        assert priorities == sorted(priorities)
        
    def test_get_rule_by_name(self):
        """Test retrieving rule by name."""
        config = get_default_config()
        
        rule = config.get_rule("length_based")
        assert rule is not None
        assert rule.name == "length_based"
        
        missing = config.get_rule("nonexistent")
        assert missing is None


class TestConfigValidator:
    """Test configuration validation."""
    
    def test_validate_duplicate_rule_names(self):
        """Test detection of duplicate rule names."""
        config = get_default_config()
        
        # Add duplicate rule
        config.rules.append(config.rules[0].copy())
        
        validator = ConfigValidator()
        issues = validator.validate(config)
        
        assert any("Duplicate rule names" in issue for issue in issues)
        
    def test_validate_invalid_regex(self):
        """Test detection of invalid regex patterns."""
        config = get_default_config()
        
        # Add invalid regex
        from signal_hub.routing.config.schema import RuleOverride
        config.overrides.append(
            RuleOverride(
                pattern="[invalid(regex",
                model=ModelType.OPUS,
                reason="Test"
            )
        )
        
        validator = ConfigValidator()
        issues = validator.validate(config)
        
        assert any("Invalid regex" in issue for issue in issues)
        
    def test_validate_threshold_ordering(self):
        """Test threshold ordering validation."""
        config = get_default_config()
        
        # Set invalid thresholds
        length_rule = config.get_rule("length_based")
        length_rule.thresholds.haiku = 3000
        length_rule.thresholds.sonnet = 1000
        
        validator = ConfigValidator()
        issues = validator.validate(config)
        
        assert any("haiku threshold must be less than sonnet" in issue for issue in issues)


class TestConfigMerger:
    """Test configuration merging."""
    
    def test_merge_basic(self):
        """Test basic configuration merge."""
        base = get_default_config()
        merger = ConfigMerger()
        
        override = {
            "default_model": "sonnet",
            "cache_similarity_threshold": 0.9
        }
        
        merged = merger.merge(base, override)
        
        assert merged.default_model == ModelType.SONNET
        assert merged.cache_similarity_threshold == 0.9
        
    def test_merge_nested(self):
        """Test merging nested structures."""
        base = get_default_config()
        merger = ConfigMerger()
        
        override = {
            "models": {
                "haiku": {
                    "max_tokens": 750
                }
            }
        }
        
        merged = merger.merge(base, override)
        
        assert merged.models[ModelType.HAIKU].max_tokens == 750
        # Other model settings preserved
        assert merged.models[ModelType.SONNET].max_tokens == 4000
        
    def test_merge_environment_vars(self):
        """Test environment variable merging."""
        config = get_default_config()
        merger = ConfigMerger()
        
        env_vars = {
            "SIGNAL_HUB_ROUTING_DEFAULT_MODEL": "opus",
            "SIGNAL_HUB_ROUTING_CACHE_SIMILARITY_THRESHOLD": "0.95",
            "OTHER_VAR": "ignored"
        }
        
        merged = merger.merge_environment_vars(config, env_vars)
        
        assert merged.default_model == ModelType.OPUS
        assert merged.cache_similarity_threshold == 0.95


class TestConfigLoader:
    """Test configuration loading."""
    
    def test_load_defaults(self):
        """Test loading default configuration."""
        loader = RoutingConfigLoader()
        config = loader.load()
        
        assert isinstance(config, RoutingConfig)
        assert config.default_model == ModelType.HAIKU
        
    def test_load_user_config(self):
        """Test loading user configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "routing.yaml"
            
            # Write user config
            user_config = {
                "default_model": "sonnet",
                "rules": [
                    {
                        "name": "length_based",
                        "enabled": False,
                        "priority": 1
                    }
                ]
            }
            
            with open(config_path, "w") as f:
                yaml.dump(user_config, f)
            
            # Load with user config
            loader = RoutingConfigLoader(config_path=config_path)
            config = loader.load()
            
            assert config.default_model == ModelType.SONNET
            # Length rule should be replaced (not merged)
            assert len([r for r in config.rules if r.name == "length_based"]) == 1
            assert not config.get_rule("length_based").enabled
            
    def test_save_example(self):
        """Test saving example configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "example.yaml"
            
            loader = RoutingConfigLoader()
            loader.save_example(config_path)
            
            assert config_path.exists()
            
            # Load and validate saved config
            with open(config_path) as f:
                content = f.read()
                assert "Signal Hub Routing Configuration" in content
                assert "models:" in content
                assert "rules:" in content
            
    def test_environment_override(self):
        """Test environment variable overrides."""
        # Set environment variables
        os.environ["SIGNAL_HUB_ROUTING_DEFAULT_MODEL"] = "opus"
        
        try:
            loader = RoutingConfigLoader()
            config = loader.load()
            
            assert config.default_model == ModelType.OPUS
        finally:
            # Clean up
            del os.environ["SIGNAL_HUB_ROUTING_DEFAULT_MODEL"]