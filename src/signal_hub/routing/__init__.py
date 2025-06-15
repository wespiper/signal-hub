"""Routing module for intelligent model selection."""

from signal_hub.routing.engine import RoutingEngine
from signal_hub.routing.models import (
    ModelType,
    Query,
    RoutingDecision,
    ModelSelection,
    RoutingMetrics
)
from signal_hub.routing.rules.base import RoutingRule
from signal_hub.routing.rules.length import LengthBasedRule
from signal_hub.routing.rules.complexity import ComplexityBasedRule
from signal_hub.routing.rules.task_type import TaskTypeRule
from signal_hub.routing.providers.base import ModelProvider
from signal_hub.routing.providers.anthropic import AnthropicProvider

__all__ = [
    # Engine
    "RoutingEngine",
    
    # Models
    "ModelType",
    "Query",
    "RoutingDecision",
    "ModelSelection",
    "RoutingMetrics",
    
    # Rules
    "RoutingRule",
    "LengthBasedRule",
    "ComplexityBasedRule",
    "TaskTypeRule",
    
    # Providers
    "ModelProvider",
    "AnthropicProvider",
]