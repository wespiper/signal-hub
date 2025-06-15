"""Data models for routing system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime


class ModelType(str, Enum):
    """Available AI models."""
    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-3-opus-20240229"
    
    @property
    def display_name(self) -> str:
        """Get display name for model."""
        return self.name.capitalize()
    
    @property
    def relative_cost(self) -> float:
        """Get relative cost factor (Haiku = 1.0)."""
        costs = {
            self.HAIKU: 1.0,
            self.SONNET: 12.0,  # ~12x more expensive than Haiku
            self.OPUS: 60.0,    # ~60x more expensive than Haiku
        }
        return costs[self]


@dataclass
class Query:
    """Query to be routed."""
    text: str
    tool_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    preferred_model: Optional[ModelType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def length(self) -> int:
        """Get query length in characters."""
        return len(self.text)
    
    @property
    def estimated_tokens(self) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token per 4 characters
        return self.length // 4


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    model: ModelType
    reason: str
    confidence: float  # 0.0 to 1.0
    rules_applied: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "model": self.model.value,
            "reason": self.reason,
            "confidence": self.confidence,
            "rules_applied": self.rules_applied,
            "metadata": self.metadata
        }


@dataclass
class ModelSelection:
    """Final model selection with override tracking."""
    model: ModelType
    routing_decision: Optional[RoutingDecision] = None
    overridden: bool = False
    override_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RoutingMetrics:
    """Metrics for routing decisions."""
    total_queries: int = 0
    model_distribution: Dict[ModelType, int] = field(default_factory=dict)
    override_count: int = 0
    average_confidence: float = 0.0
    rule_hit_counts: Dict[str, int] = field(default_factory=dict)
    
    def record_decision(self, selection: ModelSelection):
        """Record a routing decision."""
        self.total_queries += 1
        
        model = selection.model
        self.model_distribution[model] = self.model_distribution.get(model, 0) + 1
        
        if selection.overridden:
            self.override_count += 1
            
        if selection.routing_decision:
            # Update confidence average
            total_conf = self.average_confidence * (self.total_queries - 1)
            self.average_confidence = (total_conf + selection.routing_decision.confidence) / self.total_queries
            
            # Record rule hits
            for rule in selection.routing_decision.rules_applied:
                self.rule_hit_counts[rule] = self.rule_hit_counts.get(rule, 0) + 1
    
    def get_distribution_percentages(self) -> Dict[ModelType, float]:
        """Get model distribution as percentages."""
        if self.total_queries == 0:
            return {}
            
        return {
            model: (count / self.total_queries) * 100
            for model, count in self.model_distribution.items()
        }