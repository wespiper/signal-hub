"""Authentication models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AuthType(str, Enum):
    """Authentication types."""
    
    NONE = "none"
    BASIC = "basic"
    TOKEN = "token"
    SESSION = "session"


class AuthUser(BaseModel):
    """Authenticated user information."""
    
    username: str = Field(..., description="Username")
    auth_type: AuthType = Field(..., description="How user authenticated")
    roles: list[str] = Field(default_factory=list, description="User roles")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles


class AuthResult(BaseModel):
    """Authentication result."""
    
    success: bool = Field(..., description="Whether auth succeeded")
    user: Optional[AuthUser] = Field(None, description="Authenticated user")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @classmethod
    def success(cls, user: AuthUser) -> "AuthResult":
        """Create successful auth result."""
        return cls(success=True, user=user)
    
    @classmethod
    def failure(cls, error: str) -> "AuthResult":
        """Create failed auth result."""
        return cls(success=False, error=error)