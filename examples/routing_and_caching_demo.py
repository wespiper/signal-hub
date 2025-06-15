#!/usr/bin/env python3
"""Demo of routing and caching working together."""

import asyncio
import os
from datetime import datetime

from signal_hub.routing import (
    RoutingEngine,
    ModelType,
    Query,
    AnthropicProvider
)
from signal_hub.caching import SemanticCache, CacheConfig


async def demo_routing():
    """Demonstrate routing engine."""
    print("=" * 60)
    print("ROUTING ENGINE DEMO")
    print("=" * 60)
    
    # Create mock provider (for demo without API key)
    class MockProvider(AnthropicProvider):
        def __init__(self):
            self.api_key = "mock"
            
        async def complete(self, model, messages, **kwargs):
            return {
                "content": f"Mock response from {model.display_name}",
                "model": model.value,
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }
            
        def is_available(self, model):
            return True
    
    # Initialize routing engine
    provider = MockProvider()
    engine = RoutingEngine(provider)
    
    # Test queries
    test_queries = [
        # Short simple query -> Haiku
        Query(text="What is Python?"),
        
        # Tool-based query -> Haiku
        Query(text="Find all Python files", tool_name="search_code"),
        
        # Medium explanation -> Sonnet
        Query(text="Explain how Python decorators work with examples " * 20),
        
        # Complex analysis -> Opus
        Query(text="Analyze and refactor this complex architecture design"),
        
        # User preference -> Opus
        Query(text="Simple query", preferred_model=ModelType.OPUS),
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query.text[:50]}...")
        if query.tool_name:
            print(f"Tool: {query.tool_name}")
        if query.preferred_model:
            print(f"Preferred: {query.preferred_model.display_name}")
            
        selection = engine.route(query)
        print(f"→ Routed to: {selection.model.display_name}")
        print(f"  Reason: {selection.routing_decision.reason}")
        print(f"  Confidence: {selection.routing_decision.confidence:.2f}")
    
    # Show metrics
    print("\n" + "-" * 40)
    print("ROUTING METRICS:")
    metrics = engine.get_metrics()
    print(f"Total queries: {metrics['total_queries']}")
    print("Model distribution:")
    for model, percent in metrics['model_distribution'].items():
        print(f"  {model}: {percent:.1f}%")
        
    # Show cost savings
    savings = engine.estimate_cost_savings()
    print(f"\nEstimated savings: ${savings['total_savings']:.2f} ({savings['savings_percentage']:.1f}%)")


async def demo_caching():
    """Demonstrate semantic caching."""
    print("\n" + "=" * 60)
    print("SEMANTIC CACHE DEMO")
    print("=" * 60)
    
    # Initialize cache
    config = CacheConfig(
        similarity_threshold=0.85,
        ttl_hours=24,
        max_entries=1000
    )
    cache = SemanticCache(config=config)
    await cache.initialize()
    
    # Simulate queries
    queries_and_responses = [
        ("What is Python?", {"content": "Python is a high-level programming language"}),
        ("How do I read a file in Python?", {"content": "Use the open() function"}),
        ("Explain Python decorators", {"content": "Decorators are functions that modify other functions"}),
    ]
    
    print("\nPopulating cache...")
    for query, response in queries_and_responses:
        await cache.put(query, response, model="sonnet")
        print(f"  Cached: {query}")
    
    # Test cache hits and misses
    test_queries = [
        "What is Python?",  # Exact match - HIT
        "How to read files in Python?",  # Similar - might HIT
        "What is JavaScript?",  # Different - MISS
        "Explain decorators in Python",  # Similar - might HIT
    ]
    
    print("\nTesting cache retrieval...")
    for query in test_queries:
        start = datetime.utcnow()
        result = await cache.get(query)
        duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        
        if result:
            print(f"  ✓ HIT: {query} ({duration_ms:.1f}ms)")
        else:
            print(f"  ✗ MISS: {query} ({duration_ms:.1f}ms)")
    
    # Show cache stats
    print("\n" + "-" * 40)
    print("CACHE STATISTICS:")
    stats = await cache.get_stats()
    cache_stats = stats["cache_stats"]
    print(f"Total queries: {cache_stats['total_queries']}")
    print(f"Hit rate: {cache_stats['hit_rate']:.1f}%")
    print(f"Average response time: {cache_stats['average_response_time_ms']:.1f}ms")
    
    storage_stats = stats["storage_stats"]
    print(f"\nStorage: {storage_stats['active_entries']} active entries")
    print(f"Memory usage: ~{storage_stats['estimated_memory_mb']:.2f} MB")


async def demo_integration():
    """Demonstrate routing and caching working together."""
    print("\n" + "=" * 60)
    print("INTEGRATED ROUTING + CACHING DEMO")
    print("=" * 60)
    
    # In a real system, routing would check cache before calling model
    print("\nWorkflow:")
    print("1. Query arrives")
    print("2. Check semantic cache")
    print("3. If MISS: Route to appropriate model")
    print("4. Store response in cache")
    print("5. Return response")
    
    # Simulated integrated flow
    cache = SemanticCache()
    await cache.initialize()
    
    async def process_query(query_text: str) -> Dict[str, Any]:
        """Process query with caching and routing."""
        # Check cache first
        cached = await cache.get(query_text)
        if cached:
            return {"response": cached, "from_cache": True}
        
        # Route and generate response
        provider = MockProvider()  # Would use real provider
        engine = RoutingEngine(provider)
        
        query = Query(text=query_text)
        selection = engine.route(query)
        
        # Generate response (mock)
        response = {
            "content": f"Generated by {selection.model.display_name}",
            "model": selection.model.value
        }
        
        # Cache for next time
        await cache.put(query_text, response, model=selection.model.value)
        
        return {"response": response, "from_cache": False}
    
    # Test the integrated flow
    test_query = "How do I implement a REST API in Python?"
    
    print(f"\nFirst request: '{test_query}'")
    result1 = await process_query(test_query)
    print(f"From cache: {result1['from_cache']}")
    print(f"Response: {result1['response']['content']}")
    
    print(f"\nSecond request (same query):")
    result2 = await process_query(test_query)
    print(f"From cache: {result2['from_cache']}")
    print(f"Response: {result2['response']['content']}")


async def main():
    """Run all demos."""
    await demo_routing()
    await demo_caching()
    await demo_integration()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: This uses a mock provider. To use real Anthropic API:
    # 1. Set ANTHROPIC_API_KEY environment variable
    # 2. Use AnthropicProvider() instead of MockProvider()
    
    asyncio.run(main())