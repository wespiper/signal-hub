#!/usr/bin/env python3
"""Demo of Signal Hub's plugin architecture and edition features.

This example shows how Signal Hub Basic works and how Pro features
can be enabled during early access.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from signal_hub import get_version_string
from signal_hub.core import (
    get_feature_flags,
    is_feature_enabled,
    Feature,
    Edition,
)
from signal_hub.plugins import PluginManager, BasicModelRouter, BasicAnalytics


def demonstrate_basic_edition():
    """Demonstrate Signal Hub Basic functionality."""
    print(f"\n{'='*60}")
    print(f"Running: {get_version_string()}")
    print(f"{'='*60}\n")
    
    # Check available features
    flags = get_feature_flags()
    print("Available Features:")
    print("-" * 40)
    
    basic_features = [
        Feature.MCP_SERVER,
        Feature.CODEBASE_INDEXING,
        Feature.SEMANTIC_SEARCH,
        Feature.BASIC_RAG,
        Feature.SIMPLE_ROUTING,
        Feature.SEMANTIC_CACHING,
    ]
    
    pro_features = [
        Feature.ML_ROUTING,
        Feature.LEARNING_ALGORITHMS,
        Feature.ADVANCED_ANALYTICS,
        Feature.COST_OPTIMIZATION,
    ]
    
    print("\nBasic Features:")
    for feature in basic_features:
        enabled = is_feature_enabled(feature)
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature.value}")
    
    print("\nPro Features:")
    for feature in pro_features:
        enabled = is_feature_enabled(feature)
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature.value}")
    
    # Initialize plugin manager
    print("\n" + "="*60)
    print("Initializing Plugin System")
    print("="*60)
    
    config = {
        "pro_features_enabled": flags.edition != Edition.BASIC
    }
    
    plugin_manager = PluginManager(config)
    
    # Register basic plugins
    basic_router = BasicModelRouter()
    basic_analytics = BasicAnalytics()
    
    plugin_manager.register(basic_router)
    plugin_manager.register(basic_analytics)
    
    print("\nRegistered Plugins:")
    for plugin_info in plugin_manager.list_plugins():
        print(f"  - {plugin_info.name} v{plugin_info.version}: {plugin_info.description}")
    
    # Demonstrate routing
    print("\n" + "="*60)
    print("Model Routing Demo")
    print("="*60)
    
    test_queries = [
        ("What is this function?", {"retrieved_chunks": "def hello(): pass"}),
        ("Explain this complex algorithm in detail", {"retrieved_chunks": "a" * 3000}),
        ("Generate a comprehensive test suite for this module", {"retrieved_chunks": "b" * 8000}),
    ]
    
    for query, context in test_queries:
        model = basic_router.route_query(query, context)
        print(f"\nQuery: {query[:50]}...")
        print(f"Context size: {len(str(context['retrieved_chunks']))} chars")
        print(f"Selected model: {model}")
        
        # Track in analytics
        cost = {"haiku": 0.01, "sonnet": 0.05, "opus": 0.15}.get(model.split("-")[2], 0.10)
        basic_analytics.track_query(query, model, cost)
    
    # Show analytics
    print("\n" + "="*60)
    print("Cost Analytics")
    print("="*60)
    
    savings = basic_analytics.get_cost_savings()
    print(f"Total cost: ${savings['total_cost']:.2f}")
    print(f"If using Opus only: ${savings['opus_cost']:.2f}")
    print(f"Savings: ${savings['savings']:.2f} ({savings['savings_percentage']:.1f}%)")


def demonstrate_early_access():
    """Demonstrate early access mode with all features."""
    # Enable early access
    os.environ["SIGNAL_HUB_EARLY_ACCESS"] = "true"
    
    # Re-import to pick up early access mode
    from signal_hub.plugins.pro_example import MLModelRouter, AdvancedAnalytics
    
    print("\n" + "="*70)
    print("EARLY ACCESS MODE - All Pro Features Enabled!")
    print("="*70)
    
    # Initialize with pro plugins
    config = {"pro_features_enabled": True}
    plugin_manager = PluginManager(config)
    
    # Register all plugins
    plugin_manager.register(BasicModelRouter())
    plugin_manager.register(BasicAnalytics())
    plugin_manager.register(MLModelRouter())
    plugin_manager.register(AdvancedAnalytics())
    
    print("\nRegistered Plugins (including Pro):")
    for plugin_info in plugin_manager.list_plugins():
        pro_tag = " [PRO]" if plugin_info.requires_pro else ""
        print(f"  - {plugin_info.name} v{plugin_info.version}: {plugin_info.description}{pro_tag}")
    
    # Use ML router
    ml_router = plugin_manager.get_plugin("ml_router")
    analytics = plugin_manager.get_plugin("advanced_analytics")
    
    print("\n" + "="*70)
    print("ML-Powered Routing Demo")
    print("="*70)
    
    test_queries = [
        "What does this function do?",
        "Fix this error in my code: TypeError on line 42",
        "Analyze the performance implications of this algorithm and suggest optimizations",
    ]
    
    for query in test_queries:
        context = {"retrieved_chunks": "sample code context", "files": ["main.py"]}
        model = ml_router.route_query(query, context)
        print(f"\nQuery: {query}")
        print(f"ML Router selected: {model}")
        
        # Track with advanced analytics
        cost = {"haiku": 0.01, "sonnet": 0.05, "opus": 0.15}.get(model.split("-")[2], 0.10)
        analytics.track_query(query, model, cost)
    
    # Show advanced analytics
    print("\n" + "="*70)
    print("Advanced Analytics Report")
    print("="*70)
    
    report = analytics.get_cost_savings("7d")
    print("\nSummary:")
    for key, value in report["summary"].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if report["recommendations"]:
        print("\nOptimization Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")


if __name__ == "__main__":
    # First demonstrate basic edition
    demonstrate_basic_edition()
    
    # Ask if user wants to see early access features
    print("\n" + "="*70)
    response = input("Would you like to enable Early Access mode to see Pro features? (y/n): ")
    
    if response.lower() == 'y':
        demonstrate_early_access()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("\nTo learn more about Signal Hub editions:")
    print("  - Read: docs/EDITIONS.md")
    print("  - Visit: https://github.com/wespiper/signal-hub")
    print("  - Join: https://discord.gg/signalhub")
    print("="*70)