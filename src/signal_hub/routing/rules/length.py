"""Length-based routing rule."""

import logging
from typing import Optional, Dict

from signal_hub.routing.models import Query, ModelType, RoutingDecision
from signal_hub.routing.rules.base import RoutingRule

logger = logging.getLogger(__name__)


class LengthBasedRule(RoutingRule):
    """Route queries based on length thresholds."""
    
    def __init__(
        self,
        haiku_threshold: int = 500,
        sonnet_threshold: int = 2000,
        priority: int = 10,
        enabled: bool = True
    ):
        """Initialize length-based rule.
        
        Args:
            haiku_threshold: Max chars for Haiku
            sonnet_threshold: Max chars for Sonnet (above = Opus)
            priority: Rule priority
            enabled: Whether rule is enabled
        """
        super().__init__(priority, enabled)
        self.haiku_threshold = haiku_threshold
        self.sonnet_threshold = sonnet_threshold
        
    @property
    def name(self) -> str:
        """Get rule name."""
        return "length_based"
        
    def evaluate(self, query: Query) -> Optional[RoutingDecision]:
        """Evaluate query based on length."""
        if not self.enabled:
            return None
            
        length = query.length
        
        # Determine model based on length
        if length <= self.haiku_threshold:
            model = ModelType.HAIKU
            reason = f"Short query ({length} chars) suitable for Haiku"
            confidence = 0.9
        elif length <= self.sonnet_threshold:
            model = ModelType.SONNET
            reason = f"Medium query ({length} chars) suitable for Sonnet"
            confidence = 0.85
        else:
            model = ModelType.OPUS
            reason = f"Long query ({length} chars) requires Opus"
            confidence = 0.8
            
        logger.debug(f"Length rule: {length} chars -> {model.display_name}")
        
        return RoutingDecision(
            model=model,
            reason=reason,
            confidence=confidence,
            rules_applied=[self.name],
            metadata={
                "query_length": length,
                "haiku_threshold": self.haiku_threshold,
                "sonnet_threshold": self.sonnet_threshold
            }
        )
        
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for configuration."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "haiku_threshold": self.haiku_threshold,
            "sonnet_threshold": self.sonnet_threshold
        }