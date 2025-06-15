"""Base interface for routing rules."""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from signal_hub.routing.models import Query, ModelType, RoutingDecision

logger = logging.getLogger(__name__)


class RoutingRule(ABC):
    """Base class for routing rules."""
    
    def __init__(self, priority: int = 0, enabled: bool = True):
        """Initialize routing rule.
        
        Args:
            priority: Rule priority (higher = evaluated first)
            enabled: Whether rule is enabled
        """
        self.priority = priority
        self.enabled = enabled
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Get rule name."""
        pass
        
    @abstractmethod
    def evaluate(self, query: Query) -> Optional[RoutingDecision]:
        """Evaluate query and return routing decision if applicable.
        
        Args:
            query: Query to evaluate
            
        Returns:
            RoutingDecision if rule applies, None otherwise
        """
        pass
        
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(priority={self.priority}, enabled={self.enabled})"
        
    def __lt__(self, other):
        """Compare rules by priority (for sorting)."""
        return self.priority > other.priority  # Higher priority first