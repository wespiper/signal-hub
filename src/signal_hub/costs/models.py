"""Data models for cost tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum

from signal_hub.routing.models import ModelType


class CostPeriod(str, Enum):
    """Cost reporting periods."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ModelUsage:
    """Record of a single model API call."""
    id: str
    timestamp: datetime
    model: ModelType
    input_tokens: int
    output_tokens: int
    cost: float
    routing_reason: str
    cache_hit: bool
    latency_ms: int
    tool_name: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.input_tokens + self.output_tokens
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model.value,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost,
            "routing_reason": self.routing_reason,
            "cache_hit": self.cache_hit,
            "latency_ms": self.latency_ms,
            "tool_name": self.tool_name,
            "user_id": self.user_id,
            "metadata": self.metadata
        }


@dataclass
class CostSummary:
    """Summary of costs for a period."""
    period: CostPeriod
    start_time: datetime
    end_time: datetime
    total_cost: float
    total_saved: float
    routing_savings: float
    cache_savings: float
    total_requests: int
    cache_hits: int
    model_distribution: Dict[ModelType, int]
    average_latency_ms: float
    
    @property
    def savings_percentage(self) -> float:
        """Calculate savings percentage."""
        baseline = self.total_cost + self.total_saved
        if baseline == 0:
            return 0.0
        return (self.total_saved / baseline) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary."""
        return {
            "period": self.period.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_cost": self.total_cost,
            "total_saved": self.total_saved,
            "savings_percentage": self.savings_percentage,
            "routing_savings": self.routing_savings,
            "cache_savings": self.cache_savings,
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hit_rate,
            "model_distribution": {
                model.value: count 
                for model, count in self.model_distribution.items()
            },
            "average_latency_ms": self.average_latency_ms
        }


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    model: ModelType
    input_cost_per_1m: float  # Cost per million input tokens
    output_cost_per_1m: float  # Cost per million output tokens
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token counts."""
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m
        return input_cost + output_cost


# Default Anthropic pricing (as of knowledge cutoff)
DEFAULT_PRICING = {
    ModelType.HAIKU: ModelPricing(
        model=ModelType.HAIKU,
        input_cost_per_1m=0.25,
        output_cost_per_1m=1.25
    ),
    ModelType.SONNET: ModelPricing(
        model=ModelType.SONNET,
        input_cost_per_1m=3.00,
        output_cost_per_1m=15.00
    ),
    ModelType.OPUS: ModelPricing(
        model=ModelType.OPUS,
        input_cost_per_1m=15.00,
        output_cost_per_1m=75.00
    )
}


@dataclass
class CostAlert:
    """Alert for cost thresholds."""
    id: str
    name: str
    threshold_type: str  # "daily_cost", "hourly_cost", "total_cost"
    threshold_value: float
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    
    def should_trigger(self, current_value: float) -> bool:
        """Check if alert should trigger."""
        return self.enabled and current_value >= self.threshold_value