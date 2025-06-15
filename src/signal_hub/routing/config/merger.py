"""Configuration merging logic for layered configuration."""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from .schema import RoutingConfig, RoutingRule, RuleOverride


class ConfigMerger:
    """Merges configuration from multiple sources."""
    
    def merge(
        self,
        base: RoutingConfig,
        override: Dict[str, Any],
        deep: bool = True
    ) -> RoutingConfig:
        """
        Merge override configuration into base.
        
        Args:
            base: Base configuration
            override: Override values as dictionary
            deep: Whether to deep merge nested structures
            
        Returns:
            Merged configuration
        """
        # Create a copy to avoid modifying original
        result = base.copy(deep=True) if deep else base.copy()
        
        # Convert result to dict for merging
        result_dict = result.dict()
        
        # Merge the dictionaries
        merged_dict = self._merge_dicts(result_dict, override, deep=deep)
        
        # Create new config from merged dict
        return RoutingConfig(**merged_dict)
    
    def _merge_dicts(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
        deep: bool = True
    ) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            deep: Whether to deep merge
            
        Returns:
            Merged dictionary
        """
        result = base.copy() if not deep else deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self._merge_dicts(result[key], value, deep=deep)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Handle list merging based on key
                if key in ["rules", "overrides"]:
                    # Replace entire list for rules and overrides
                    result[key] = value
                else:
                    # Extend lists for other keys
                    result[key] = result[key] + value
            else:
                # Simple replacement
                result[key] = value
        
        return result
    
    def merge_environment_vars(
        self,
        config: RoutingConfig,
        env_vars: Dict[str, str]
    ) -> RoutingConfig:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables follow pattern:
        SIGNAL_HUB_ROUTING_<SECTION>_<KEY>
        
        Examples:
        - SIGNAL_HUB_ROUTING_DEFAULT_MODEL=sonnet
        - SIGNAL_HUB_ROUTING_CACHE_SIMILARITY_THRESHOLD=0.9
        - SIGNAL_HUB_ROUTING_RULES_LENGTH_BASED_ENABLED=false
        
        Args:
            config: Base configuration
            env_vars: Environment variables
            
        Returns:
            Configuration with env overrides applied
        """
        overrides = {}
        prefix = "SIGNAL_HUB_ROUTING_"
        
        for key, value in env_vars.items():
            if not key.startswith(prefix):
                continue
                
            # Remove prefix and lowercase
            path = key[len(prefix):].lower()
            parts = path.split("_")
            
            # Parse the value
            parsed_value = self._parse_env_value(value)
            
            # Build nested override dict
            current = overrides
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the final value
            current[parts[-1]] = parsed_value
        
        # Apply overrides if any
        if overrides:
            return self.merge(config, overrides)
        
        return config
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ["true", "false"]:
            return value.lower() == "true"
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # List (comma-separated)
        if "," in value:
            return [v.strip() for v in value.split(",")]
        
        # String (default)
        return value