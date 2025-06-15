"""Configuration schema for routing system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from signal_hub.routing.models import ModelType


class ComplexityLevel(str, Enum):
    """Task complexity levels."""
    
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for this model")
    max_complexity: Optional[ComplexityLevel] = Field(None, description="Maximum complexity")
    preferred_tasks: List[str] = Field(default_factory=list, description="Preferred task types")
    
    class Config:
        use_enum_values = True


class RuleThresholds(BaseModel):
    """Thresholds for length-based routing."""
    
    haiku: int = Field(500, description="Max tokens for Haiku")
    sonnet: int = Field(2000, description="Max tokens for Sonnet")
    # Opus has no limit by default


class ComplexityIndicators(BaseModel):
    """Keywords indicating complexity levels."""
    
    simple: List[str] = Field(
        default_factory=lambda: ["what", "when", "where", "list", "find"],
        description="Simple query indicators"
    )
    moderate: List[str] = Field(
        default_factory=lambda: ["how", "why", "explain", "describe"],
        description="Moderate complexity indicators"
    )
    complex: List[str] = Field(
        default_factory=lambda: ["analyze", "design", "optimize", "refactor", "architect"],
        description="Complex query indicators"
    )


class TaskMappings(BaseModel):
    """Mappings from task types to models."""
    
    search_code: ModelType = Field(ModelType.HAIKU, description="Model for code search")
    explain_code: ModelType = Field(ModelType.SONNET, description="Model for explanations")
    find_similar: ModelType = Field(ModelType.HAIKU, description="Model for similarity search")
    get_context: ModelType = Field(ModelType.SONNET, description="Model for context assembly")
    analyze_architecture: ModelType = Field(ModelType.OPUS, description="Model for architecture")
    
    class Config:
        use_enum_values = True


class RoutingRule(BaseModel):
    """A single routing rule configuration."""
    
    name: str = Field(..., description="Rule name")
    enabled: bool = Field(True, description="Whether rule is active")
    priority: int = Field(1, description="Rule priority (lower = higher priority)")
    thresholds: Optional[RuleThresholds] = Field(None, description="Length thresholds")
    indicators: Optional[ComplexityIndicators] = Field(None, description="Complexity indicators")
    mappings: Optional[TaskMappings] = Field(None, description="Task type mappings")
    
    @validator("priority")
    def validate_priority(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Priority must be between 1 and 100")
        return v


class RuleOverride(BaseModel):
    """Pattern-based routing override."""
    
    pattern: str = Field(..., description="Regex pattern to match")
    model: ModelType = Field(..., description="Model to use")
    reason: str = Field(..., description="Reason for override")
    
    class Config:
        use_enum_values = True


class RoutingConfig(BaseModel):
    """Complete routing configuration."""
    
    # Model configurations
    models: Dict[ModelType, ModelConfig] = Field(
        default_factory=lambda: {
            ModelType.HAIKU: ModelConfig(
                max_tokens=1000,
                max_complexity=ComplexityLevel.SIMPLE,
                preferred_tasks=["search", "simple_query"]
            ),
            ModelType.SONNET: ModelConfig(
                max_tokens=4000,
                max_complexity=ComplexityLevel.MODERATE,
                preferred_tasks=["explain", "analyze"]
            ),
            ModelType.OPUS: ModelConfig(
                max_tokens=None,
                max_complexity=ComplexityLevel.COMPLEX,
                preferred_tasks=["debug", "architect", "refactor"]
            ),
        }
    )
    
    # Routing rules
    rules: List[RoutingRule] = Field(
        default_factory=lambda: [
            RoutingRule(
                name="length_based",
                enabled=True,
                priority=1,
                thresholds=RuleThresholds()
            ),
            RoutingRule(
                name="complexity_based",
                enabled=True,
                priority=2,
                indicators=ComplexityIndicators()
            ),
            RoutingRule(
                name="task_type",
                enabled=True,
                priority=3,
                mappings=TaskMappings()
            ),
        ]
    )
    
    # Pattern overrides
    overrides: List[RuleOverride] = Field(
        default_factory=lambda: [
            RuleOverride(
                pattern=r"security|vulnerability|exploit",
                model=ModelType.OPUS,
                reason="Security requires careful analysis"
            ),
            RuleOverride(
                pattern=r"performance|optimize|bottleneck",
                model=ModelType.OPUS,
                reason="Performance optimization needs deep analysis"
            ),
        ]
    )
    
    # Global settings
    default_model: ModelType = Field(
        ModelType.HAIKU,
        description="Default model when no rules match"
    )
    cache_similarity_threshold: float = Field(
        0.85,
        description="Minimum similarity for cache hits"
    )
    enable_escalation: bool = Field(
        True,
        description="Allow manual escalation"
    )
    
    class Config:
        use_enum_values = True
        
    def get_rule(self, name: str) -> Optional[RoutingRule]:
        """Get a specific rule by name."""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
        
    def get_enabled_rules(self) -> List[RoutingRule]:
        """Get all enabled rules sorted by priority."""
        return sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority
        )