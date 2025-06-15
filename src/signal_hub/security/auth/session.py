"""Session management for web dashboard."""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from signal_hub.utils.logging import get_logger
from .models import AuthUser, AuthType


logger = get_logger(__name__)


class Session:
    """User session information."""
    
    def __init__(self, session_id: str, user: AuthUser, expires: datetime):
        self.session_id = session_id
        self.user = user
        self.expires = expires
        self.created = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.data: Dict[str, any] = {}
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires
    
    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.utcnow()


class SessionManager:
    """Manages user sessions."""
    
    def __init__(
        self,
        session_ttl_minutes: int = 60,
        cookie_name: str = "signal_hub_session"
    ):
        """
        Initialize session manager.
        
        Args:
            session_ttl_minutes: Session time-to-live in minutes
            cookie_name: Name of session cookie
        """
        self.session_ttl_minutes = session_ttl_minutes
        self.cookie_name = cookie_name
        self._sessions: Dict[str, Session] = {}
    
    def create_session(self, user: AuthUser) -> str:
        """
        Create a new session.
        
        Args:
            user: Authenticated user
            
        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(minutes=self.session_ttl_minutes)
        
        # Update user auth type
        session_user = user.copy()
        session_user.auth_type = AuthType.SESSION
        
        session = Session(session_id, session_user, expires)
        self._sessions[session_id] = session
        
        logger.info(f"Created session for user: {user.username}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None if not found/expired
        """
        session = self._sessions.get(session_id)
        
        if not session:
            return None
        
        if session.is_expired():
            del self._sessions[session_id]
            return None
        
        # Touch session to update last accessed
        session.touch()
        return session
    
    def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a session.
        
        Args:
            session_id: Session ID to destroy
            
        Returns:
            True if session was destroyed
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]
            del self._sessions[session_id]
            logger.info(f"Destroyed session for user: {session.user.username}")
            return True
        return False
    
    def destroy_user_sessions(self, username: str) -> int:
        """
        Destroy all sessions for a user.
        
        Args:
            username: Username whose sessions to destroy
            
        Returns:
            Number of sessions destroyed
        """
        sessions_to_destroy = []
        
        for session_id, session in self._sessions.items():
            if session.user.username == username:
                sessions_to_destroy.append(session_id)
        
        for session_id in sessions_to_destroy:
            del self._sessions[session_id]
        
        if sessions_to_destroy:
            logger.info(f"Destroyed {len(sessions_to_destroy)} sessions for user: {username}")
        
        return len(sessions_to_destroy)
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def extend_session(self, session_id: str, minutes: Optional[int] = None) -> bool:
        """
        Extend session expiry.
        
        Args:
            session_id: Session to extend
            minutes: Minutes to extend (defaults to session_ttl_minutes)
            
        Returns:
            True if session was extended
        """
        session = self._sessions.get(session_id)
        
        if not session or session.is_expired():
            return False
        
        minutes = minutes or self.session_ttl_minutes
        session.expires = datetime.utcnow() + timedelta(minutes=minutes)
        session.touch()
        
        return True
    
    def get_cookie_config(self, secure: bool = True) -> Dict[str, any]:
        """
        Get cookie configuration.
        
        Args:
            secure: Whether to use secure cookies
            
        Returns:
            Cookie configuration dict
        """
        return {
            "name": self.cookie_name,
            "httponly": True,
            "secure": secure,
            "samesite": "lax",
            "max_age": self.session_ttl_minutes * 60,
        }