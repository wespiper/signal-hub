"""Manual escalation MCP tool."""

import logging
from typing import Dict, Any, Optional

from signal_hub.core.tools.base import Tool
from signal_hub.routing.models import ModelType
from signal_hub.routing.escalation.escalator import EscalationManager

logger = logging.getLogger(__name__)


class EscalateQueryTool(Tool):
    """MCP tool for manually escalating to a more capable model."""
    
    def __init__(
        self,
        escalation_manager: Optional[EscalationManager] = None
    ):
        """Initialize escalate query tool.
        
        Args:
            escalation_manager: Escalation manager (or create default)
        """
        self.escalation_manager = escalation_manager or EscalationManager()
        super().__init__()
        
    @property
    def name(self) -> str:
        """Get tool name."""
        return "escalate_query"
        
    @property
    def description(self) -> str:
        """Get tool description."""
        return "Manually request a more capable model for complex queries"
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool inputs."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to process with escalated model"
                },
                "model": {
                    "type": "string",
                    "enum": ["sonnet", "opus"],
                    "description": "Model to escalate to",
                    "default": "opus"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation (optional)"
                },
                "duration": {
                    "type": "string",
                    "enum": ["single", "session"],
                    "description": "Apply to single query or entire session",
                    "default": "single"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for session-level escalation"
                }
            },
            "required": ["query"]
        }
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the escalation tool.
        
        Args:
            params: Tool parameters
            
        Returns:
            Escalation result
        """
        try:
            # Validate parameters
            error = self.validate_params(params)
            if error:
                return {
                    "success": False,
                    "error": error
                }
                
            # Extract parameters
            query = params["query"]
            model_name = params.get("model", "opus").lower()
            reason = params.get("reason", "Manual escalation requested")
            duration = params.get("duration", "single")
            session_id = params.get("session_id")
            
            # Map model name to ModelType
            if model_name == "sonnet":
                model = ModelType.SONNET
            elif model_name == "opus":
                model = ModelType.OPUS
            else:
                return {
                    "success": False,
                    "error": f"Invalid model: {model_name}. Use 'sonnet' or 'opus'"
                }
                
            # Handle session escalation
            if duration == "session" and session_id:
                self.escalation_manager.escalate_session(
                    session_id=session_id,
                    model=model,
                    reason=reason
                )
                
                return {
                    "success": True,
                    "escalation": {
                        "type": "session",
                        "model": model.display_name,
                        "session_id": session_id,
                        "reason": reason,
                        "message": f"All queries in session will use {model.display_name}"
                    }
                }
                
            # Single query escalation
            # In practice, this would return a modified query with preferred_model set
            # The routing engine would then use this preference
            
            cost_info = self._get_cost_impact(model)
            
            return {
                "success": True,
                "escalation": {
                    "type": "single",
                    "model": model.display_name,
                    "reason": reason,
                    "query": query,
                    "cost_impact": cost_info,
                    "message": f"Query will be processed with {model.display_name}"
                },
                "instructions": {
                    "next_step": "Process the query with the escalated model",
                    "cost_note": cost_info["note"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in escalate_query tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _get_cost_impact(self, model: ModelType) -> Dict[str, Any]:
        """Get cost impact information for escalation.
        
        Args:
            model: Model to escalate to
            
        Returns:
            Cost impact information
        """
        relative_costs = {
            ModelType.HAIKU: 1.0,
            ModelType.SONNET: 12.0,
            ModelType.OPUS: 60.0
        }
        
        haiku_cost = relative_costs[ModelType.HAIKU]
        target_cost = relative_costs[model]
        
        return {
            "relative_cost": target_cost,
            "times_more_expensive": target_cost / haiku_cost,
            "note": f"{model.display_name} is ~{int(target_cost)}x more expensive than Haiku"
        }