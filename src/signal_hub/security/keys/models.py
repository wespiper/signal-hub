"""Models for API key management."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, SecretStr


class KeyProvider(str, Enum):
    """Supported API key providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class APIKey(BaseModel):
    """API key information."""
    
    provider: KeyProvider = Field(..., description="API provider")
    key: SecretStr = Field(..., description="The API key (encrypted)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = Field(None, description="Last usage time")
    rotation_date: Optional[datetime] = Field(None, description="Next rotation date")
    
    class Config:
        use_enum_values = True