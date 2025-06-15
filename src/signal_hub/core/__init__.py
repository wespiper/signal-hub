"""Signal Hub core functionality."""

from signal_hub.core.features import (
    Edition,
    Feature,
    FeatureFlags,
    get_feature_flags,
    is_feature_enabled,
    require_feature,
    get_edition,
    requires_feature,
    requires_edition,
)

from signal_hub.core.plugins import (
    Plugin,
    PluginManager,
    ModelRouter,
    CacheStrategy,
    AnalyticsProvider,
)

__all__ = [
    # Features
    "Edition",
    "Feature",
    "FeatureFlags",
    "get_feature_flags",
    "is_feature_enabled",
    "require_feature",
    "get_edition",
    "requires_feature",
    "requires_edition",
    # Plugins
    "Plugin",
    "PluginManager",
    "ModelRouter",
    "CacheStrategy",
    "AnalyticsProvider",
]