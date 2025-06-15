"""Tests for routing engine."""

import pytest
from unittest.mock import Mock, AsyncMock

from signal_hub.routing import (
    RoutingEngine,
    ModelType,
    Query,
    RoutingMetrics,
    LengthBasedRule,
    ComplexityBasedRule,
    TaskTypeRule
)
from signal_hub.routing.providers.base import ModelProvider


class MockProvider(ModelProvider):
    """Mock provider for testing."""
    
    @property
    def name(self) -> str:
        return "mock"
        
    async def complete(self, model, messages, **kwargs):
        return {"content": "test", "model": model.value}
        
    async def count_tokens(self, text, model):
        return len(text) // 4
        
    def get_model_info(self, model):
        return {"max_tokens": 100000}
        
    def is_available(self, model):
        return True
        
    def calculate_cost(self, model, input_tokens, output_tokens):
        costs = {
            ModelType.HAIKU: 0.001,
            ModelType.SONNET: 0.01,
            ModelType.OPUS: 0.05
        }
        return costs.get(model, 0.01) * (input_tokens + output_tokens) / 1000


class TestRoutingEngine:
    """Test routing engine functionality."""
    
    def test_initialization(self):
        """Test engine initialization."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        assert engine.provider == provider
        assert len(engine.rules) == 3  # Default rules
        assert engine.default_model == ModelType.OPUS
        assert isinstance(engine.metrics, RoutingMetrics)
        
    def test_default_rules_order(self):
        """Test default rules are ordered by priority."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        # Check priority order (highest first)
        priorities = [rule.priority for rule in engine.rules]
        assert priorities == sorted(priorities, reverse=True)
        
        # Check rule types
        assert isinstance(engine.rules[0], TaskTypeRule)
        assert isinstance(engine.rules[1], ComplexityBasedRule)
        assert isinstance(engine.rules[2], LengthBasedRule)
        
    def test_route_with_preferred_model(self):
        """Test routing with user preference."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        query = Query(
            text="Simple query",
            preferred_model=ModelType.OPUS
        )
        
        selection = engine.route(query)
        
        assert selection.model == ModelType.OPUS
        assert selection.overridden is True
        assert selection.override_reason == "User preference"
        
    def test_route_short_query(self):
        """Test routing short query to Haiku."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        query = Query(text="What is Python?")
        selection = engine.route(query)
        
        assert selection.model == ModelType.HAIKU
        assert "Short query" in selection.routing_decision.reason
        
    def test_route_medium_query(self):
        """Test routing medium query to Sonnet."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        query = Query(text="Explain " + "x" * 1000)  # Medium length
        selection = engine.route(query)
        
        assert selection.model == ModelType.SONNET
        
    def test_route_long_query(self):
        """Test routing long query to Opus."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        query = Query(text="Analyze " + "x" * 3000)  # Long query
        selection = engine.route(query)
        
        assert selection.model == ModelType.OPUS
        assert "Long query" in selection.routing_decision.reason
        
    def test_route_by_complexity(self):
        """Test routing by complexity indicators."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        # Simple query
        query = Query(text="List all files in the directory")
        selection = engine.route(query)
        assert selection.model == ModelType.HAIKU
        
        # Complex query
        query = Query(text="Analyze and refactor this architecture")
        selection = engine.route(query)
        assert selection.model == ModelType.OPUS
        
    def test_route_by_task_type(self):
        """Test routing by task type."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        query = Query(
            text="Find similar code",
            tool_name="search_code"
        )
        selection = engine.route(query)
        
        assert selection.model == ModelType.HAIKU
        assert "Task 'search_code'" in selection.routing_decision.reason
        
    def test_metrics_recording(self):
        """Test metrics are recorded correctly."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        # Route several queries
        queries = [
            Query(text="Short"),
            Query(text="Medium " * 100),
            Query(text="Complex analysis and refactoring required"),
        ]
        
        for query in queries:
            engine.route(query)
            
        metrics = engine.get_metrics()
        
        assert metrics["total_queries"] == 3
        assert len(metrics["model_distribution"]) > 0
        assert sum(metrics["model_distribution"].values()) == 100.0
        
    def test_add_remove_rules(self):
        """Test adding and removing rules."""
        provider = MockProvider()
        engine = RoutingEngine(provider, rules=[])
        
        assert len(engine.rules) == 0
        
        # Add rule
        rule = LengthBasedRule()
        engine.add_rule(rule)
        assert len(engine.rules) == 1
        
        # Remove rule
        engine.remove_rule("length_based")
        assert len(engine.rules) == 0
        
    def test_cost_savings_estimation(self):
        """Test cost savings calculation."""
        provider = MockProvider()
        engine = RoutingEngine(provider)
        
        # Route queries to different models
        engine.route(Query(text="Short"))  # Haiku
        engine.route(Query(text="Medium " * 100))  # Sonnet
        engine.route(Query(text="Long " * 1000))  # Opus
        
        savings = engine.estimate_cost_savings()
        
        assert "total_savings" in savings
        assert "savings_percentage" in savings
        assert savings["total_savings"] > 0  # Should have some savings
        assert 0 <= savings["savings_percentage"] <= 100
        
    def test_unavailable_model_fallback(self):
        """Test fallback when model is unavailable."""
        provider = MockProvider()
        # Mock unavailable model
        provider.is_available = Mock(side_effect=lambda m: m != ModelType.HAIKU)
        
        engine = RoutingEngine(provider)
        
        query = Query(text="Short query")
        selection = engine.route(query)
        
        # Should fall back to default (Opus)
        assert selection.model == ModelType.OPUS
        assert "unavailable" in selection.routing_decision.reason