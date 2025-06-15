"""Main escalation manager."""

import logging
from typing import Optional, Dict, Any

from signal_hub.routing.models import Query, ModelType
from signal_hub.routing.escalation.models import ModelOverride, EscalationType
from signal_hub.routing.escalation.parser import EscalationParser
from signal_hub.routing.escalation.session import SessionEscalationManager

logger = logging.getLogger(__name__)


class EscalationManager:
    """Manage all forms of model escalation."""
    
    def __init__(self):
        """Initialize escalation manager."""
        self.parser = EscalationParser()
        self.session_manager = SessionEscalationManager()
        self.metrics = {
            "total_escalations": 0,
            "inline_escalations": 0,
            "explicit_escalations": 0,
            "session_escalations": 0
        }
        
    def check_escalation(
        self,
        query: Query,
        session_id: Optional[str] = None
    ) -> Optional[ModelOverride]:
        """Check for any escalation on the query.
        
        Args:
            query: Query to check
            session_id: Optional session identifier
            
        Returns:
            Model override if escalation found
        """
        # 1. Check if query already has preferred model (explicit)
        if query.preferred_model:
            self.metrics["total_escalations"] += 1
            self.metrics["explicit_escalations"] += 1
            
            return ModelOverride(
                model=query.preferred_model,
                source="explicit",
                reason="Explicit model preference"
            )
            
        # 2. Check session-level escalation
        if session_id:
            override = self.session_manager.get_session_model(session_id)
            if override:
                self.metrics["total_escalations"] += 1
                self.metrics["session_escalations"] += 1
                return override
                
        # 3. Check inline hints
        hint_result = self.parser.extract_hint(query.text)
        if hint_result:
            cleaned_query, escalation_request = hint_result
            
            # Update query text to remove hint
            query.text = cleaned_query
            
            self.metrics["total_escalations"] += 1
            self.metrics["inline_escalations"] += 1
            
            return ModelOverride(
                model=escalation_request.requested_model,
                source="inline",
                reason=escalation_request.reason
            )
            
        return None
        
    def escalate_session(
        self,
        session_id: str,
        model: ModelType,
        duration_minutes: Optional[int] = None,
        reason: Optional[str] = None
    ):
        """Escalate all queries in a session.
        
        Args:
            session_id: Session to escalate
            model: Model to use
            duration_minutes: Duration of escalation
            reason: Reason for escalation
        """
        self.session_manager.set_session_model(
            session_id=session_id,
            model=model,
            duration_minutes=duration_minutes,
            reason=reason
        )
        
    def clear_session_escalation(self, session_id: str):
        """Clear session escalation.
        
        Args:
            session_id: Session to clear
        """
        self.session_manager.clear_session(session_id)
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get escalation metrics.
        
        Returns:
            Escalation statistics
        """
        metrics = self.metrics.copy()
        
        # Calculate escalation rate
        if metrics["total_escalations"] > 0:
            metrics["inline_percentage"] = (
                metrics["inline_escalations"] / metrics["total_escalations"] * 100
            )
            metrics["explicit_percentage"] = (
                metrics["explicit_escalations"] / metrics["total_escalations"] * 100
            )
            metrics["session_percentage"] = (
                metrics["session_escalations"] / metrics["total_escalations"] * 100
            )
        else:
            metrics["inline_percentage"] = 0
            metrics["explicit_percentage"] = 0
            metrics["session_percentage"] = 0
            
        # Add active sessions
        metrics["active_sessions"] = len(self.session_manager.sessions)
        
        return metrics
        
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Get information about active session escalations.
        
        Returns:
            Active session details
        """
        return self.session_manager.get_active_sessions()