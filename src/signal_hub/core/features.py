"""Feature flags for Signal Hub.

This module manages feature availability across Signal Hub editions.
Features can be enabled/disabled based on edition, configuration, or runtime flags.
"""

import os
from enum import Enum
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class Edition(Enum):
    """Signal Hub editions."""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    
    @classmethod
    def from_env(cls) -> "Edition":
        """Get edition from environment variable."""
        edition = os.getenv("SIGNAL_HUB_EDITION", "basic").lower()
        try:
            return cls(edition)
        except ValueError:
            logger.warning(f"Unknown edition: {edition}, defaulting to BASIC")
            return cls.BASIC


class Feature(Enum):
    """Available features in Signal Hub."""
    
    # Basic features (available in all editions)
    MCP_SERVER = "mcp_server"
    CODEBASE_INDEXING = "codebase_indexing"
    SEMANTIC_SEARCH = "semantic_search"
    BASIC_RAG = "basic_rag"
    SIMPLE_ROUTING = "simple_routing"
    SEMANTIC_CACHING = "semantic_caching"
    MANUAL_ESCALATION = "manual_escalation"
    BASIC_COST_TRACKING = "basic_cost_tracking"
    
    # Pro features
    ML_ROUTING = "ml_routing"
    LEARNING_ALGORITHMS = "learning_algorithms"
    ADVANCED_ANALYTICS = "advanced_analytics"
    COST_OPTIMIZATION = "cost_optimization"
    CUSTOM_MODELS = "custom_models"
    API_ACCESS = "api_access"
    PRIORITY_SUPPORT = "priority_support"
    
    # Enterprise features
    TEAM_MANAGEMENT = "team_management"
    SSO_INTEGRATION = "sso_integration"
    AUDIT_LOGGING = "audit_logging"
    CUSTOM_DEPLOYMENT = "custom_deployment"
    SLA_SUPPORT = "sla_support"
    ADVANCED_SECURITY = "advanced_security"
    USAGE_LIMITS = "usage_limits"


@dataclass
class FeatureConfig:
    """Configuration for a feature."""
    name: str
    description: str
    min_edition: Edition
    enabled_by_default: bool = True
    experimental: bool = False
    config_key: Optional[str] = None


# Feature definitions
FEATURE_CONFIGS: Dict[Feature, FeatureConfig] = {
    # Basic features
    Feature.MCP_SERVER: FeatureConfig(
        name="MCP Server",
        description="Core MCP server functionality",
        min_edition=Edition.BASIC
    ),
    Feature.CODEBASE_INDEXING: FeatureConfig(
        name="Codebase Indexing",
        description="Index and scan codebases",
        min_edition=Edition.BASIC
    ),
    Feature.SEMANTIC_SEARCH: FeatureConfig(
        name="Semantic Search",
        description="Search code using embeddings",
        min_edition=Edition.BASIC
    ),
    Feature.BASIC_RAG: FeatureConfig(
        name="Basic RAG",
        description="Retrieval-augmented generation",
        min_edition=Edition.BASIC
    ),
    Feature.SIMPLE_ROUTING: FeatureConfig(
        name="Simple Routing",
        description="Rule-based model routing",
        min_edition=Edition.BASIC
    ),
    Feature.SEMANTIC_CACHING: FeatureConfig(
        name="Semantic Caching",
        description="Cache similar queries",
        min_edition=Edition.BASIC
    ),
    Feature.MANUAL_ESCALATION: FeatureConfig(
        name="Manual Escalation",
        description="Manually escalate to better models",
        min_edition=Edition.BASIC
    ),
    Feature.BASIC_COST_TRACKING: FeatureConfig(
        name="Basic Cost Tracking",
        description="Track AI model costs",
        min_edition=Edition.BASIC
    ),
    
    # Pro features
    Feature.ML_ROUTING: FeatureConfig(
        name="ML-Powered Routing",
        description="Machine learning based model selection",
        min_edition=Edition.PRO,
        config_key="ml_routing_enabled"
    ),
    Feature.LEARNING_ALGORITHMS: FeatureConfig(
        name="Learning Algorithms",
        description="Improve routing through feedback",
        min_edition=Edition.PRO
    ),
    Feature.ADVANCED_ANALYTICS: FeatureConfig(
        name="Advanced Analytics",
        description="Detailed usage and cost analytics",
        min_edition=Edition.PRO
    ),
    Feature.COST_OPTIMIZATION: FeatureConfig(
        name="Cost Optimization",
        description="Advanced cost-saving strategies",
        min_edition=Edition.PRO
    ),
    Feature.CUSTOM_MODELS: FeatureConfig(
        name="Custom Models",
        description="Add custom AI models",
        min_edition=Edition.PRO,
        experimental=True
    ),
    Feature.API_ACCESS: FeatureConfig(
        name="API Access",
        description="REST API for integration",
        min_edition=Edition.PRO
    ),
    Feature.PRIORITY_SUPPORT: FeatureConfig(
        name="Priority Support",
        description="Priority customer support",
        min_edition=Edition.PRO
    ),
    
    # Enterprise features
    Feature.TEAM_MANAGEMENT: FeatureConfig(
        name="Team Management",
        description="Multi-user team features",
        min_edition=Edition.ENTERPRISE
    ),
    Feature.SSO_INTEGRATION: FeatureConfig(
        name="SSO Integration",
        description="Single sign-on support",
        min_edition=Edition.ENTERPRISE
    ),
    Feature.AUDIT_LOGGING: FeatureConfig(
        name="Audit Logging",
        description="Comprehensive audit trails",
        min_edition=Edition.ENTERPRISE
    ),
    Feature.CUSTOM_DEPLOYMENT: FeatureConfig(
        name="Custom Deployment",
        description="On-premise deployment options",
        min_edition=Edition.ENTERPRISE
    ),
    Feature.SLA_SUPPORT: FeatureConfig(
        name="SLA Support",
        description="Service level agreements",
        min_edition=Edition.ENTERPRISE
    ),
    Feature.ADVANCED_SECURITY: FeatureConfig(
        name="Advanced Security",
        description="Enhanced security features",
        min_edition=Edition.ENTERPRISE
    ),
    Feature.USAGE_LIMITS: FeatureConfig(
        name="Usage Limits",
        description="Configure usage limits",
        min_edition=Edition.ENTERPRISE
    ),
}


@dataclass
class FeatureFlags:
    """Manages feature availability."""
    
    edition: Edition = field(default_factory=Edition.from_env)
    config: Dict[str, bool] = field(default_factory=dict)
    overrides: Dict[Feature, bool] = field(default_factory=dict)
    _early_access: bool = field(default=False)
    
    def __post_init__(self):
        """Initialize feature flags."""
        # Check for early access mode
        self._early_access = os.getenv("SIGNAL_HUB_EARLY_ACCESS", "false").lower() == "true"
        if self._early_access:
            logger.info("Early access mode enabled - all features available")
    
    def is_enabled(self, feature: Feature) -> bool:
        """Check if a feature is enabled."""
        # Early access mode enables all features
        if self._early_access:
            return True
        
        # Check explicit overrides first
        if feature in self.overrides:
            return self.overrides[feature]
        
        # Get feature config
        feature_config = FEATURE_CONFIGS.get(feature)
        if not feature_config:
            logger.warning(f"Unknown feature: {feature}")
            return False
        
        # Check edition requirement
        if self.edition.value < feature_config.min_edition.value:
            return False
        
        # Check configuration override
        if feature_config.config_key and feature_config.config_key in self.config:
            return self.config[feature_config.config_key]
        
        # Return default
        return feature_config.enabled_by_default
    
    def enable(self, feature: Feature) -> None:
        """Enable a feature."""
        self.overrides[feature] = True
    
    def disable(self, feature: Feature) -> None:
        """Disable a feature."""
        self.overrides[feature] = False
    
    def get_enabled_features(self) -> Set[Feature]:
        """Get all enabled features."""
        return {f for f in Feature if self.is_enabled(f)}
    
    def get_edition_features(self, edition: Optional[Edition] = None) -> Set[Feature]:
        """Get features available for an edition."""
        target_edition = edition or self.edition
        return {
            f for f, config in FEATURE_CONFIGS.items()
            if config.min_edition.value <= target_edition.value
        }
    
    def require(self, feature: Feature) -> None:
        """Require a feature to be enabled, raise error if not."""
        if not self.is_enabled(feature):
            feature_config = FEATURE_CONFIGS.get(feature)
            if feature_config:
                raise FeatureNotAvailableError(
                    f"Feature '{feature_config.name}' requires Signal Hub {feature_config.min_edition.value.title()} edition"
                )
            else:
                raise FeatureNotAvailableError(f"Unknown feature: {feature}")
    
    def check_edition(self, min_edition: Edition) -> bool:
        """Check if current edition meets minimum requirement."""
        return self.edition.value >= min_edition.value


class FeatureNotAvailableError(Exception):
    """Raised when a required feature is not available."""
    pass


# Global feature flags instance
_feature_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_feature_enabled(feature: Feature) -> bool:
    """Check if a feature is enabled."""
    return get_feature_flags().is_enabled(feature)


def require_feature(feature: Feature) -> None:
    """Require a feature to be enabled."""
    get_feature_flags().require(feature)


def get_edition() -> Edition:
    """Get the current Signal Hub edition."""
    return get_feature_flags().edition


# Decorators for feature-gated functionality

def requires_feature(feature: Feature):
    """Decorator to require a feature for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            require_feature(feature)
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def requires_edition(min_edition: Edition):
    """Decorator to require a minimum edition."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not get_feature_flags().check_edition(min_edition):
                raise FeatureNotAvailableError(
                    f"This feature requires Signal Hub {min_edition.value.title()} edition"
                )
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator