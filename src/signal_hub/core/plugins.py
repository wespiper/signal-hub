"""Plugin system for Signal Hub extensibility.

This module provides the infrastructure for extending Signal Hub with
additional features, particularly for Pro/Enterprise editions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for Signal Hub plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return ""
    
    @property
    def requires_pro(self) -> bool:
        """Whether this plugin requires Signal Hub Pro."""
        return False
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass
    
    def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass


class ModelRouter(Protocol):
    """Protocol for model routing plugins."""
    
    def route_query(self, query: str, context: Dict[str, Any]) -> str:
        """Route a query to the appropriate model."""
        ...
    
    def record_feedback(self, query_id: str, feedback: Dict[str, Any]) -> None:
        """Record user feedback for routing improvement."""
        ...


class CacheStrategy(Protocol):
    """Protocol for caching strategy plugins."""
    
    def should_cache(self, query: str, response: str) -> bool:
        """Determine if a response should be cached."""
        ...
    
    def get_cache_key(self, query: str, context: Dict[str, Any]) -> str:
        """Generate cache key for a query."""
        ...


class AnalyticsProvider(Protocol):
    """Protocol for analytics plugins."""
    
    def track_query(self, query: str, model: str, cost: float) -> None:
        """Track a query for analytics."""
        ...
    
    def get_cost_savings(self, time_range: str) -> Dict[str, Any]:
        """Get cost savings report."""
        ...


@dataclass
class PluginInfo:
    """Information about a loaded plugin."""
    name: str
    version: str
    description: str
    instance: Plugin
    enabled: bool = True
    requires_pro: bool = False


class PluginManager:
    """Manages Signal Hub plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._plugins: Dict[str, PluginInfo] = {}
        self._model_routers: List[ModelRouter] = []
        self._cache_strategies: List[CacheStrategy] = []
        self._analytics_providers: List[AnalyticsProvider] = []
    
    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        if plugin.name in self._plugins:
            logger.warning(f"Plugin {plugin.name} already registered, replacing")
        
        # Check if plugin requires pro and if pro features are enabled
        if plugin.requires_pro and not self.config.get("pro_features_enabled", False):
            logger.info(f"Skipping pro plugin {plugin.name} (pro features not enabled)")
            return
        
        # Initialize plugin
        plugin_config = self.config.get("plugins", {}).get(plugin.name, {})
        plugin.initialize(plugin_config)
        
        # Store plugin info
        info = PluginInfo(
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            instance=plugin,
            requires_pro=plugin.requires_pro
        )
        self._plugins[plugin.name] = info
        
        # Register plugin interfaces
        if isinstance(plugin, ModelRouter):
            self._model_routers.append(plugin)
        if isinstance(plugin, CacheStrategy):
            self._cache_strategies.append(plugin)
        if isinstance(plugin, AnalyticsProvider):
            self._analytics_providers.append(plugin)
        
        logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        if plugin_name not in self._plugins:
            return
        
        info = self._plugins[plugin_name]
        plugin = info.instance
        
        # Remove from interface lists
        if isinstance(plugin, ModelRouter) and plugin in self._model_routers:
            self._model_routers.remove(plugin)
        if isinstance(plugin, CacheStrategy) and plugin in self._cache_strategies:
            self._cache_strategies.remove(plugin)
        if isinstance(plugin, AnalyticsProvider) and plugin in self._analytics_providers:
            self._analytics_providers.remove(plugin)
        
        # Shutdown and remove
        plugin.shutdown()
        del self._plugins[plugin_name]
        
        logger.info(f"Unregistered plugin: {plugin_name}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        info = self._plugins.get(name)
        return info.instance if info else None
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all registered plugins."""
        return list(self._plugins.values())
    
    def get_model_routers(self) -> List[ModelRouter]:
        """Get all model router plugins."""
        return self._model_routers
    
    def get_cache_strategies(self) -> List[CacheStrategy]:
        """Get all cache strategy plugins."""
        return self._cache_strategies
    
    def get_analytics_providers(self) -> List[AnalyticsProvider]:
        """Get all analytics provider plugins."""
        return self._analytics_providers
    
    def shutdown(self) -> None:
        """Shutdown all plugins."""
        for info in self._plugins.values():
            try:
                info.instance.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin {info.name}: {e}")
        self._plugins.clear()
        self._model_routers.clear()
        self._cache_strategies.clear()
        self._analytics_providers.clear()


# Built-in plugins for Signal Hub Basic

class BasicModelRouter(Plugin):
    """Basic rule-based model router for Signal Hub Basic."""
    
    name = "basic_router"
    version = "1.0.0"
    description = "Simple rule-based model routing"
    
    def __init__(self):
        self.thresholds = {
            "query_length": 100,
            "context_size": 5000,
        }
    
    def route_query(self, query: str, context: Dict[str, Any]) -> str:
        """Route based on simple rules."""
        query_length = len(query.split())
        context_size = len(str(context.get("retrieved_chunks", "")))
        
        # Simple rules
        if query_length < 20 and context_size < 1000:
            return "claude-3-haiku-20240307"
        elif query_length < 50 and context_size < 5000:
            return "claude-3-sonnet-20240229"
        else:
            return "claude-3-opus-20240229"
    
    def record_feedback(self, query_id: str, feedback: Dict[str, Any]) -> None:
        """Basic router doesn't learn from feedback."""
        pass


class BasicCacheStrategy(Plugin):
    """Basic semantic caching for Signal Hub Basic."""
    
    name = "basic_cache"
    version = "1.0.0"
    description = "Simple semantic caching strategy"
    
    def should_cache(self, query: str, response: str) -> bool:
        """Cache all successful responses."""
        return len(response) > 0
    
    def get_cache_key(self, query: str, context: Dict[str, Any]) -> str:
        """Simple cache key generation."""
        import hashlib
        key_content = f"{query}:{sorted(context.items())}"
        return hashlib.sha256(key_content.encode()).hexdigest()


class BasicAnalytics(Plugin):
    """Basic analytics for Signal Hub Basic."""
    
    name = "basic_analytics"
    version = "1.0.0"
    description = "Simple cost tracking and reporting"
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
    
    def track_query(self, query: str, model: str, cost: float) -> None:
        """Track basic query information."""
        self.queries.append({
            "query": query[:100],  # Truncate for privacy
            "model": model,
            "cost": cost,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })
    
    def get_cost_savings(self, time_range: str = "all") -> Dict[str, Any]:
        """Calculate basic cost savings."""
        if not self.queries:
            return {"total_cost": 0, "potential_savings": 0}
        
        total_cost = sum(q["cost"] for q in self.queries)
        # Assume all queries using Opus
        opus_cost = len(self.queries) * 0.075  # Approximate cost
        
        return {
            "total_cost": total_cost,
            "opus_cost": opus_cost,
            "savings": opus_cost - total_cost,
            "savings_percentage": ((opus_cost - total_cost) / opus_cost * 100) if opus_cost > 0 else 0
        }