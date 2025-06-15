"""Configuration validation for routing system."""

import re
from typing import List, Optional, Set

from pydantic import ValidationError

from .schema import RoutingConfig, RoutingRule, RuleOverride


class ValidationError(Exception):
    """Configuration validation error."""
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


class ConfigValidator:
    """Validates routing configuration."""
    
    def validate(self, config: RoutingConfig) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Validate rules
        issues.extend(self._validate_rules(config.rules))
        
        # Validate overrides
        issues.extend(self._validate_overrides(config.overrides))
        
        # Validate model configs
        issues.extend(self._validate_models(config))
        
        # Validate global settings
        issues.extend(self._validate_global(config))
        
        return issues
    
    def _validate_rules(self, rules: List[RoutingRule]) -> List[str]:
        """Validate routing rules."""
        issues = []
        
        # Check for duplicate names
        names = [r.name for r in rules]
        duplicates = set([n for n in names if names.count(n) > 1])
        if duplicates:
            issues.append(f"Duplicate rule names: {duplicates}")
        
        # Check for duplicate priorities among enabled rules
        enabled_priorities = [r.priority for r in rules if r.enabled]
        dup_priorities = set([p for p in enabled_priorities if enabled_priorities.count(p) > 1])
        if dup_priorities:
            issues.append(f"Duplicate priorities in enabled rules: {dup_priorities}")
        
        # Validate each rule
        for rule in rules:
            # Check rule has appropriate config
            if rule.name == "length_based" and not rule.thresholds:
                issues.append(f"Rule '{rule.name}' requires thresholds")
            elif rule.name == "complexity_based" and not rule.indicators:
                issues.append(f"Rule '{rule.name}' requires indicators")
            elif rule.name == "task_type" and not rule.mappings:
                issues.append(f"Rule '{rule.name}' requires mappings")
            
            # Validate thresholds are ordered
            if rule.thresholds:
                if rule.thresholds.haiku >= rule.thresholds.sonnet:
                    issues.append(
                        f"Rule '{rule.name}': haiku threshold must be less than sonnet"
                    )
        
        return issues
    
    def _validate_overrides(self, overrides: List[RuleOverride]) -> List[str]:
        """Validate pattern overrides."""
        issues = []
        
        for i, override in enumerate(overrides):
            # Validate regex pattern
            try:
                re.compile(override.pattern)
            except re.error as e:
                issues.append(
                    f"Override {i}: Invalid regex pattern '{override.pattern}': {e}"
                )
        
        return issues
    
    def _validate_models(self, config: RoutingConfig) -> List[str]:
        """Validate model configurations."""
        issues = []
        
        # Check all models are configured
        configured_models = set(config.models.keys())
        all_models = set(ModelType)
        
        missing = all_models - configured_models
        if missing:
            issues.append(f"Missing configuration for models: {missing}")
        
        # Validate token limits are sensible
        for model, model_config in config.models.items():
            if model_config.max_tokens is not None:
                if model_config.max_tokens <= 0:
                    issues.append(f"Model {model}: max_tokens must be positive")
                elif model_config.max_tokens > 100000:
                    issues.append(f"Model {model}: max_tokens seems too high")
        
        return issues
    
    def _validate_global(self, config: RoutingConfig) -> List[str]:
        """Validate global settings."""
        issues = []
        
        # Validate cache threshold
        if not 0 <= config.cache_similarity_threshold <= 1:
            issues.append("cache_similarity_threshold must be between 0 and 1")
        
        # Validate default model exists
        if config.default_model not in config.models:
            issues.append(f"default_model {config.default_model} not in configured models")
        
        return issues
    
    def assert_valid(self, config: RoutingConfig) -> None:
        """
        Assert configuration is valid, raising exception if not.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValidationError: If configuration is invalid
        """
        issues = self.validate(config)
        if issues:
            raise ValidationError(
                f"Configuration validation failed with {len(issues)} issues",
                errors=issues
            )