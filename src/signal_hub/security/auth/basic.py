"""Basic authentication implementation."""

import base64
import hashlib
from typing import Dict, Optional

import bcrypt

from signal_hub.utils.logging import get_logger
from .models import AuthUser, AuthResult, AuthType


logger = get_logger(__name__)


class BasicAuthenticator:
    """HTTP Basic authentication."""
    
    def __init__(self, users: Optional[Dict[str, str]] = None):
        """
        Initialize authenticator.
        
        Args:
            users: Dict of username -> password hash
        """
        self.users = users or {}
    
    def add_user(self, username: str, password: str) -> None:
        """
        Add a user with hashed password.
        
        Args:
            username: Username
            password: Plain text password (will be hashed)
        """
        password_hash = self._hash_password(password)
        self.users[username] = password_hash
        logger.info(f"Added user: {username}")
    
    def remove_user(self, username: str) -> bool:
        """
        Remove a user.
        
        Args:
            username: Username to remove
            
        Returns:
            True if user was removed
        """
        if username in self.users:
            del self.users[username]
            logger.info(f"Removed user: {username}")
            return True
        return False
    
    def authenticate(self, auth_header: Optional[str]) -> AuthResult:
        """
        Authenticate from Authorization header.
        
        Args:
            auth_header: Authorization header value
            
        Returns:
            Authentication result
        """
        if not auth_header:
            return AuthResult.failure("No authorization header")
        
        # Parse header
        try:
            auth_type, credentials = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                return AuthResult.failure(f"Unsupported auth type: {auth_type}")
            
            # Decode credentials
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception as e:
            logger.debug(f"Failed to parse auth header: {e}")
            return AuthResult.failure("Invalid authorization header")
        
        # Verify credentials
        if username not in self.users:
            return AuthResult.failure("Invalid username or password")
        
        if not self._verify_password(password, self.users[username]):
            return AuthResult.failure("Invalid username or password")
        
        # Create authenticated user
        user = AuthUser(
            username=username,
            auth_type=AuthType.BASIC,
            roles=["user"]  # TODO: Add role management
        )
        
        return AuthResult.success(user)
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def create_header(self, username: str, password: str) -> str:
        """
        Create Basic auth header value.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Header value (e.g., "Basic dXNlcjpwYXNz")
        """
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"