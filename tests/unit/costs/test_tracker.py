"""Tests for cost tracking."""

import pytest
from datetime import datetime, timedelta

from signal_hub.routing.models import ModelType
from signal_hub.costs import CostTracker, CostCalculator, CostPeriod
from signal_hub.costs.storage.sqlite import SQLiteCostStorage


class TestCostTracker:
    """Test cost tracking functionality."""
    
    @pytest.fixture
    async def tracker(self, tmp_path):
        """Create test cost tracker."""
        storage = SQLiteCostStorage(str(tmp_path / "test_costs.db"))
        tracker = CostTracker(storage)
        await tracker.initialize()
        return tracker
        
    @pytest.mark.asyncio
    async def test_track_usage(self, tracker):
        """Test tracking model usage."""
        usage = await tracker.track_usage(
            model=ModelType.HAIKU,
            input_tokens=1000,
            output_tokens=500,
            routing_reason="Short query",
            cache_hit=False,
            latency_ms=250,
            tool_name="search_code"
        )
        
        assert usage.model == ModelType.HAIKU
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 500
        assert usage.cost > 0
        assert usage.cache_hit is False
        
    @pytest.mark.asyncio
    async def test_cache_hit_zero_cost(self, tracker):
        """Test cache hits have zero cost."""
        usage = await tracker.track_usage(
            model=ModelType.OPUS,
            input_tokens=1000,
            output_tokens=500,
            routing_reason="Cached response",
            cache_hit=True,
            latency_ms=50
        )
        
        assert usage.cost == 0.0
        assert usage.input_tokens == 0  # No tokens for cache hit
        assert usage.output_tokens == 0
        
    @pytest.mark.asyncio
    async def test_cost_summary(self, tracker):
        """Test cost summary calculation."""
        # Track some usage
        await tracker.track_usage(
            ModelType.HAIKU, 1000, 500, "Test", False, 100
        )
        await tracker.track_usage(
            ModelType.SONNET, 2000, 1000, "Test", False, 200
        )
        await tracker.track_usage(
            ModelType.OPUS, 1500, 750, "Test", True, 50  # Cache hit
        )
        
        # Get daily summary
        summary = await tracker.get_summary(CostPeriod.DAILY)
        
        assert summary.total_requests == 3
        assert summary.cache_hits == 1
        assert summary.cache_hit_rate == pytest.approx(33.33, rel=0.1)
        assert summary.total_cost > 0
        assert summary.cache_savings > 0  # From cache hit
        
    @pytest.mark.asyncio
    async def test_cost_trends(self, tracker):
        """Test cost trend tracking."""
        # Track usage over time
        base_time = datetime.utcnow()
        
        # Manually add historical data
        for i in range(3):
            usage_time = base_time - timedelta(hours=i)
            await tracker.track_usage(
                ModelType.HAIKU, 1000, 500, "Test", False, 100
            )
            
        trends = await tracker.get_cost_trends(CostPeriod.HOURLY, num_periods=3)
        
        assert len(trends) == 3
        assert all(t["period"] == "hourly" for t in trends)
        
    @pytest.mark.asyncio
    async def test_model_distribution(self, tracker):
        """Test tracking model distribution."""
        # Track different models
        models = [ModelType.HAIKU, ModelType.HAIKU, ModelType.SONNET, ModelType.OPUS]
        
        for model in models:
            await tracker.track_usage(
                model, 1000, 500, "Test", False, 100
            )
            
        summary = await tracker.get_summary(CostPeriod.DAILY)
        
        assert summary.model_distribution[ModelType.HAIKU] == 2
        assert summary.model_distribution[ModelType.SONNET] == 1
        assert summary.model_distribution[ModelType.OPUS] == 1
        
    @pytest.mark.asyncio
    async def test_cleanup_old_records(self, tracker):
        """Test cleaning up old records."""
        # Add old record
        old_usage = await tracker.track_usage(
            ModelType.OPUS, 1000, 500, "Old", False, 100
        )
        
        # Manually set timestamp to old date
        old_usage.timestamp = datetime.utcnow() - timedelta(days=100)
        await tracker.storage.add_usage(old_usage)
        
        # Add recent record
        await tracker.track_usage(
            ModelType.HAIKU, 1000, 500, "Recent", False, 100
        )
        
        # Cleanup records older than 90 days
        deleted = await tracker.cleanup_old_records(days_to_keep=90)
        
        assert deleted >= 1  # At least the old record
        
        # Verify recent record still exists
        recent = await tracker.get_recent_usage(limit=10)
        assert len(recent) >= 1