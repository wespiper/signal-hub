"""Tests for length-based routing rule."""

import pytest

from signal_hub.routing.models import Query, ModelType
from signal_hub.routing.rules.length import LengthBasedRule


class TestLengthBasedRule:
    """Test length-based routing rule."""
    
    def test_initialization(self):
        """Test rule initialization."""
        rule = LengthBasedRule(
            haiku_threshold=600,
            sonnet_threshold=2500,
            priority=15
        )
        
        assert rule.haiku_threshold == 600
        assert rule.sonnet_threshold == 2500
        assert rule.priority == 15
        assert rule.enabled is True
        assert rule.name == "length_based"
        
    def test_short_query(self):
        """Test routing short query to Haiku."""
        rule = LengthBasedRule()
        query = Query(text="What is Python?")
        
        decision = rule.evaluate(query)
        
        assert decision is not None
        assert decision.model == ModelType.HAIKU
        assert "Short query" in decision.reason
        assert decision.confidence == 0.9
        assert "length_based" in decision.rules_applied
        
    def test_medium_query(self):
        """Test routing medium query to Sonnet."""
        rule = LengthBasedRule()
        query = Query(text="x" * 1000)  # 1000 chars
        
        decision = rule.evaluate(query)
        
        assert decision.model == ModelType.SONNET
        assert "Medium query" in decision.reason
        assert decision.confidence == 0.85
        
    def test_long_query(self):
        """Test routing long query to Opus."""
        rule = LengthBasedRule()
        query = Query(text="x" * 3000)  # 3000 chars
        
        decision = rule.evaluate(query)
        
        assert decision.model == ModelType.OPUS
        assert "Long query" in decision.reason
        assert decision.confidence == 0.8
        
    def test_exact_thresholds(self):
        """Test behavior at exact thresholds."""
        rule = LengthBasedRule(
            haiku_threshold=500,
            sonnet_threshold=2000
        )
        
        # Exactly at Haiku threshold
        query = Query(text="x" * 500)
        decision = rule.evaluate(query)
        assert decision.model == ModelType.HAIKU
        
        # Just over Haiku threshold
        query = Query(text="x" * 501)
        decision = rule.evaluate(query)
        assert decision.model == ModelType.SONNET
        
        # Exactly at Sonnet threshold
        query = Query(text="x" * 2000)
        decision = rule.evaluate(query)
        assert decision.model == ModelType.SONNET
        
        # Just over Sonnet threshold
        query = Query(text="x" * 2001)
        decision = rule.evaluate(query)
        assert decision.model == ModelType.OPUS
        
    def test_disabled_rule(self):
        """Test disabled rule returns None."""
        rule = LengthBasedRule(enabled=False)
        query = Query(text="Test query")
        
        decision = rule.evaluate(query)
        assert decision is None
        
    def test_metadata(self):
        """Test metadata is included in decision."""
        rule = LengthBasedRule()
        query = Query(text="x" * 100)
        
        decision = rule.evaluate(query)
        
        assert "query_length" in decision.metadata
        assert decision.metadata["query_length"] == 100
        assert "haiku_threshold" in decision.metadata
        assert "sonnet_threshold" in decision.metadata
        
    def test_to_dict(self):
        """Test serialization to dict."""
        rule = LengthBasedRule(
            haiku_threshold=600,
            sonnet_threshold=2500,
            priority=15,
            enabled=False
        )
        
        config = rule.to_dict()
        
        assert config["name"] == "length_based"
        assert config["enabled"] is False
        assert config["priority"] == 15
        assert config["haiku_threshold"] == 600
        assert config["sonnet_threshold"] == 2500