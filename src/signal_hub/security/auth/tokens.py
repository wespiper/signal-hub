"""API token management."""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from signal_hub.utils.logging import get_logger
from .models import AuthUser, AuthResult, AuthType


logger = get_logger(__name__)


class TokenManager:
    """Manages API tokens for authentication."""
    
    def __init__(self, token_length: int = 32, ttl_hours: int = 24):
        """
        Initialize token manager.
        
        Args:
            token_length: Length of generated tokens
            ttl_hours: Token time-to-live in hours
        """
        self.token_length = token_length
        self.ttl_hours = ttl_hours
        # token -> (user, expiry)
        self._tokens: Dict[str, tuple[AuthUser, datetime]] = {}
    
    def generate_token(self, user: AuthUser) -> str:
        """
        Generate a new API token for user.
        
        Args:
            user: User to generate token for
            
        Returns:
            Generated token
        """
        token = secrets.token_urlsafe(self.token_length)
        expiry = datetime.utcnow() + timedelta(hours=self.ttl_hours)
        
        self._tokens[token] = (user, expiry)
        
        logger.info(f"Generated token for user: {user.username}")
        return token
    
    def authenticate(self, token: str) -> AuthResult:
        """
        Authenticate using API token.
        
        Args:
            token: API token
            
        Returns:
            Authentication result
        """
        if token not in self._tokens:
            return AuthResult.failure("Invalid token")
        
        user, expiry = self._tokens[token]
        
        # Check expiry
        if datetime.utcnow() > expiry:
            del self._tokens[token]
            return AuthResult.failure("Token expired")
        
        # Update auth type
        auth_user = user.copy()
        auth_user.auth_type = AuthType.TOKEN
        
        return AuthResult.success(auth_user)
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if token was revoked
        """
        if token in self._tokens:
            user, _ = self._tokens[token]
            del self._tokens[token]
            logger.info(f"Revoked token for user: {user.username}")
            return True
        return False
    
    def revoke_user_tokens(self, username: str) -> int:
        """
        Revoke all tokens for a user.
        
        Args:
            username: Username whose tokens to revoke
            
        Returns:
            Number of tokens revoked
        """
        tokens_to_revoke = []
        
        for token, (user, _) in self._tokens.items():
            if user.username == username:
                tokens_to_revoke.append(token)
        
        for token in tokens_to_revoke:
            del self._tokens[token]
        
        if tokens_to_revoke:
            logger.info(f"Revoked {len(tokens_to_revoke)} tokens for user: {username}")
        
        return len(tokens_to_revoke)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired tokens.
        
        Returns:
            Number of tokens removed
        """
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, (_, expiry) in self._tokens.items():
            if current_time > expiry:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self._tokens[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        
        return len(expired_tokens)
    
    def list_tokens(self, username: Optional[str] = None) -> list[Dict[str, str]]:
        """
        List active tokens.
        
        Args:
            username: Filter by username (optional)
            
        Returns:
            List of token info (without actual tokens)
        """
        tokens = []
        
        for token, (user, expiry) in self._tokens.items():
            if username and user.username != username:
                continue
            
            tokens.append({
                "username": user.username,
                "token_prefix": token[:8] + "...",
                "expires": expiry.isoformat(),
                "remaining_hours": (expiry - datetime.utcnow()).total_seconds() / 3600
            })
        
        return tokens