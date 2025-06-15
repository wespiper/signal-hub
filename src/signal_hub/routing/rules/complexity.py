"""Complexity-based routing rule."""

import re
import logging
from typing import Optional, List, Set

from signal_hub.routing.models import Query, ModelType, RoutingDecision
from signal_hub.routing.rules.base import RoutingRule

logger = logging.getLogger(__name__)


class ComplexityBasedRule(RoutingRule):
    """Route queries based on complexity indicators."""
    
    # Default complexity indicators
    SIMPLE_INDICATORS = {
        "what", "when", "where", "who", "list", "show", "find", "search",
        "get", "fetch", "display", "print", "count", "check"
    }
    
    MODERATE_INDICATORS = {
        "explain", "describe", "summarize", "compare", "why", "how",
        "implement", "create", "build", "fix", "update", "modify"
    }
    
    COMPLEX_INDICATORS = {
        "analyze", "design", "architect", "optimize", "refactor", "debug",
        "review", "audit", "improve", "enhance", "restructure", "evaluate",
        "integrate", "migrate", "transform", "performance", "security"
    }
    
    def __init__(
        self,
        simple_indicators: Optional[Set[str]] = None,
        moderate_indicators: Optional[Set[str]] = None,
        complex_indicators: Optional[Set[str]] = None,
        priority: int = 20,
        enabled: bool = True
    ):
        """Initialize complexity-based rule.
        
        Args:
            simple_indicators: Words indicating simple queries
            moderate_indicators: Words indicating moderate queries
            complex_indicators: Words indicating complex queries
            priority: Rule priority
            enabled: Whether rule is enabled
        """
        super().__init__(priority, enabled)
        self.simple_indicators = simple_indicators or self.SIMPLE_INDICATORS
        self.moderate_indicators = moderate_indicators or self.MODERATE_INDICATORS
        self.complex_indicators = complex_indicators or self.COMPLEX_INDICATORS
        
    @property
    def name(self) -> str:
        """Get rule name."""
        return "complexity_based"
        
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from query text."""
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        return set(words)
        
    def _calculate_complexity(self, query: Query) -> tuple[str, float]:
        """Calculate query complexity.
        
        Returns:
            Tuple of (complexity_level, confidence)
        """
        keywords = self._extract_keywords(query.text)
        
        # Count matches for each complexity level
        simple_matches = len(keywords & self.simple_indicators)
        moderate_matches = len(keywords & self.moderate_indicators)
        complex_matches = len(keywords & self.complex_indicators)
        
        # Determine complexity based on matches
        if complex_matches > 0:
            # Any complex indicator = complex query
            confidence = min(0.9, 0.7 + (0.1 * complex_matches))
            return "complex", confidence
        elif moderate_matches > simple_matches:
            # More moderate than simple = moderate
            confidence = min(0.85, 0.6 + (0.1 * moderate_matches))
            return "moderate", confidence
        elif simple_matches > 0:
            # Has simple indicators = simple
            confidence = min(0.9, 0.7 + (0.1 * simple_matches))
            return "simple", confidence
        else:
            # No clear indicators, default to moderate
            return "moderate", 0.5
            
    def evaluate(self, query: Query) -> Optional[RoutingDecision]:
        """Evaluate query based on complexity."""
        if not self.enabled:
            return None
            
        complexity, confidence = self._calculate_complexity(query)
        
        # Map complexity to model
        if complexity == "simple":
            model = ModelType.HAIKU
            reason = "Simple query with basic information retrieval"
        elif complexity == "moderate":
            model = ModelType.SONNET
            reason = "Moderate complexity requiring explanation or implementation"
        else:  # complex
            model = ModelType.OPUS
            reason = "Complex query requiring analysis or design"
            
        logger.debug(f"Complexity rule: {complexity} -> {model.display_name}")
        
        # Check for code-specific complexity
        if "```" in query.text or query.estimated_tokens > 500:
            # Queries with code blocks are inherently more complex
            if model == ModelType.HAIKU:
                model = ModelType.SONNET
                reason += " (contains code)"
                confidence *= 0.9
                
        return RoutingDecision(
            model=model,
            reason=reason,
            confidence=confidence,
            rules_applied=[self.name],
            metadata={
                "complexity_level": complexity,
                "indicators_found": list(self._extract_keywords(query.text) & 
                                       (self.simple_indicators | self.moderate_indicators | self.complex_indicators))
            }
        )