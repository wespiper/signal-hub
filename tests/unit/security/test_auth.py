"""Tests for authentication components."""

import pytest

from signal_hub.security.auth import (
    BasicAuthenticator,
    TokenManager,
    SessionManager,
    AuthUser,
    AuthType,
)


class TestBasicAuth:
    """Test basic authentication."""
    
    def test_add_user_and_authenticate(self):
        """Test adding user and authenticating."""
        auth = BasicAuthenticator()
        
        # Add user
        auth.add_user("testuser", "testpass")
        
        # Create auth header
        header = auth.create_header("testuser", "testpass")
        
        # Authenticate
        result = auth.authenticate(header)
        
        assert result.success is True
        assert result.user.username == "testuser"
        assert result.user.auth_type == AuthType.BASIC
        
    def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        auth = BasicAuthenticator()
        auth.add_user("user", "pass")
        
        # Wrong password
        header = auth.create_header("user", "wrongpass")
        result = auth.authenticate(header)
        
        assert result.success is False
        assert "Invalid username or password" in result.error
        
    def test_missing_auth_header(self):
        """Test authentication without header."""
        auth = BasicAuthenticator()
        
        result = auth.authenticate(None)
        
        assert result.success is False
        assert "No authorization header" in result.error
        
    def test_remove_user(self):
        """Test removing a user."""
        auth = BasicAuthenticator()
        auth.add_user("user", "pass")
        
        # Remove user
        removed = auth.remove_user("user")
        assert removed is True
        
        # Try to authenticate
        header = auth.create_header("user", "pass")
        result = auth.authenticate(header)
        
        assert result.success is False


class TestTokenManager:
    """Test token management."""
    
    def test_generate_and_authenticate(self):
        """Test token generation and authentication."""
        manager = TokenManager()
        
        # Create user
        user = AuthUser(username="testuser", auth_type=AuthType.BASIC)
        
        # Generate token
        token = manager.generate_token(user)
        assert len(token) > 20
        
        # Authenticate with token
        result = manager.authenticate(token)
        
        assert result.success is True
        assert result.user.username == "testuser"
        assert result.user.auth_type == AuthType.TOKEN
        
    def test_invalid_token(self):
        """Test authentication with invalid token."""
        manager = TokenManager()
        
        result = manager.authenticate("invalid-token")
        
        assert result.success is False
        assert "Invalid token" in result.error
        
    def test_revoke_token(self):
        """Test revoking tokens."""
        manager = TokenManager()
        user = AuthUser(username="user", auth_type=AuthType.BASIC)
        
        # Generate token
        token = manager.generate_token(user)
        
        # Revoke token
        revoked = manager.revoke_token(token)
        assert revoked is True
        
        # Try to authenticate
        result = manager.authenticate(token)
        assert result.success is False
        
    def test_revoke_user_tokens(self):
        """Test revoking all user tokens."""
        manager = TokenManager()
        user = AuthUser(username="user", auth_type=AuthType.BASIC)
        
        # Generate multiple tokens
        tokens = [manager.generate_token(user) for _ in range(3)]
        
        # Revoke all user tokens
        count = manager.revoke_user_tokens("user")
        assert count == 3
        
        # All tokens should be invalid
        for token in tokens:
            result = manager.authenticate(token)
            assert result.success is False


class TestSessionManager:
    """Test session management."""
    
    def test_create_and_get_session(self):
        """Test session creation and retrieval."""
        manager = SessionManager()
        user = AuthUser(username="user", auth_type=AuthType.BASIC)
        
        # Create session
        session_id = manager.create_session(user)
        assert len(session_id) > 20
        
        # Get session
        session = manager.get_session(session_id)
        assert session is not None
        assert session.user.username == "user"
        assert session.user.auth_type == AuthType.SESSION
        
    def test_invalid_session(self):
        """Test getting invalid session."""
        manager = SessionManager()
        
        session = manager.get_session("invalid-session-id")
        assert session is None
        
    def test_destroy_session(self):
        """Test destroying session."""
        manager = SessionManager()
        user = AuthUser(username="user", auth_type=AuthType.BASIC)
        
        # Create session
        session_id = manager.create_session(user)
        
        # Destroy session
        destroyed = manager.destroy_session(session_id)
        assert destroyed is True
        
        # Session should be gone
        session = manager.get_session(session_id)
        assert session is None
        
    def test_extend_session(self):
        """Test extending session expiry."""
        manager = SessionManager(session_ttl_minutes=1)
        user = AuthUser(username="user", auth_type=AuthType.BASIC)
        
        # Create session
        session_id = manager.create_session(user)
        
        # Get initial expiry
        session1 = manager.get_session(session_id)
        initial_expiry = session1.expires
        
        # Extend session
        extended = manager.extend_session(session_id, minutes=10)
        assert extended is True
        
        # Check new expiry
        session2 = manager.get_session(session_id)
        assert session2.expires > initial_expiry