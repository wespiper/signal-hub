"""Session-level escalation management."""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from signal_hub.routing.models import ModelType
from signal_hub.routing.escalation.models import ModelOverride

logger = logging.getLogger(__name__)


class SessionEscalationManager:
    """Manage session-level model escalations."""
    
    def __init__(self, default_duration_minutes: int = 30):
        """Initialize session manager.
        
        Args:
            default_duration_minutes: Default session duration
        """
        self.default_duration_minutes = default_duration_minutes
        self.sessions: Dict[str, Dict] = {}
        
    def set_session_model(
        self,
        session_id: str,
        model: ModelType,
        duration_minutes: Optional[int] = None,
        reason: Optional[str] = None
    ):
        """Set model for a session.
        
        Args:
            session_id: Session identifier
            model: Model to use for session
            duration_minutes: Session duration (or use default)
            reason: Reason for escalation
        """
        duration = duration_minutes or self.default_duration_minutes
        expires_at = datetime.utcnow() + timedelta(minutes=duration)
        
        self.sessions[session_id] = {
            "model": model,
            "expires_at": expires_at,
            "reason": reason or "Session escalation",
            "created_at": datetime.utcnow()
        }
        
        logger.info(
            f"Set session {session_id} to use {model.display_name} "
            f"for {duration} minutes"
        )
        
    def get_session_model(self, session_id: str) -> Optional[ModelOverride]:
        """Get model override for session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Model override or None if no session escalation
        """
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        
        # Check if expired
        if datetime.utcnow() > session["expires_at"]:
            del self.sessions[session_id]
            logger.debug(f"Session {session_id} escalation expired")
            return None
            
        return ModelOverride(
            model=session["model"],
            source="session",
            reason=session["reason"]
        )
        
    def clear_session(self, session_id: str):
        """Clear session escalation.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session {session_id} escalation")
            
    def cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self.sessions.items()
            if now > session["expires_at"]
        ]
        
        for session_id in expired:
            del self.sessions[session_id]
            
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")
            
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Get all active sessions.
        
        Returns:
            Active session information
        """
        self.cleanup_expired()
        
        return {
            session_id: {
                "model": session["model"].display_name,
                "expires_in_minutes": int(
                    (session["expires_at"] - datetime.utcnow()).total_seconds() / 60
                ),
                "reason": session["reason"]
            }
            for session_id, session in self.sessions.items()
        }