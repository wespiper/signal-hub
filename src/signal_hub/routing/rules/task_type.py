"""Task type-based routing rule."""

import logging
from typing import Optional, Dict

from signal_hub.routing.models import Query, ModelType, RoutingDecision
from signal_hub.routing.rules.base import RoutingRule

logger = logging.getLogger(__name__)


class TaskTypeRule(RoutingRule):
    """Route queries based on MCP tool task type."""
    
    # Default task mappings
    DEFAULT_MAPPINGS = {
        "search_code": ModelType.HAIKU,
        "find_similar": ModelType.HAIKU,
        "explain_code": ModelType.SONNET,
        "get_context": ModelType.SONNET,
        "analyze_architecture": ModelType.OPUS,
        "refactor_code": ModelType.OPUS,
        "security_audit": ModelType.OPUS,
    }
    
    def __init__(
        self,
        task_mappings: Optional[Dict[str, ModelType]] = None,
        priority: int = 30,
        enabled: bool = True
    ):
        """Initialize task type rule.
        
        Args:
            task_mappings: Mapping of task names to models
            priority: Rule priority
            enabled: Whether rule is enabled
        """
        super().__init__(priority, enabled)
        self.task_mappings = task_mappings or self.DEFAULT_MAPPINGS
        
    @property
    def name(self) -> str:
        """Get rule name."""
        return "task_type"
        
    def evaluate(self, query: Query) -> Optional[RoutingDecision]:
        """Evaluate query based on task type."""
        if not self.enabled:
            return None
            
        # Check if query has a tool name
        if not query.tool_name:
            return None
            
        # Look up model for this task
        if query.tool_name not in self.task_mappings:
            logger.debug(f"Task type '{query.tool_name}' not in mappings")
            return None
            
        model = self.task_mappings[query.tool_name]
        
        # High confidence for explicit task mappings
        confidence = 0.95
        
        reason = f"Task '{query.tool_name}' mapped to {model.display_name}"
        logger.debug(f"Task rule: {query.tool_name} -> {model.display_name}")
        
        return RoutingDecision(
            model=model,
            reason=reason,
            confidence=confidence,
            rules_applied=[self.name],
            metadata={
                "task_type": query.tool_name,
                "mapped_model": model.value
            }
        )
        
    def add_mapping(self, task: str, model: ModelType):
        """Add or update a task mapping."""
        self.task_mappings[task] = model
        
    def remove_mapping(self, task: str):
        """Remove a task mapping."""
        self.task_mappings.pop(task, None)
        
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for configuration."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "task_mappings": {
                task: model.value
                for task, model in self.task_mappings.items()
            }
        }