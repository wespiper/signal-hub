"""Models for rate limiting."""

from typing import Dict, Optional

from pydantic import BaseModel, Field

from signal_hub.routing.models import ModelType


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, key: str, limit: int, current: int):
        self.key = key
        self.limit = limit
        self.current = current
        super().__init__(
            f"Rate limit exceeded for {key}: {current}/{limit} requests"
        )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    
    enabled: bool = Field(True, description="Whether rate limiting is enabled")
    backend: str = Field("memory", description="Backend type (memory or redis)")
    window_seconds: int = Field(3600, description="Time window in seconds")
    
    # Default limits
    default_limit: int = Field(1000, description="Default requests per window")
    
    # Per-model limits
    model_limits: Dict[ModelType, int] = Field(
        default_factory=lambda: {
            ModelType.HAIKU: 5000,
            ModelType.SONNET: 1000,
            ModelType.OPUS: 100,
        },
        description="Per-model request limits"
    )
    
    # Per-user limits (can be customized)
    user_limits: Dict[str, int] = Field(
        default_factory=dict,
        description="Custom per-user limits"
    )
    
    # Redis configuration (if using Redis backend)
    redis_url: Optional[str] = Field(
        None,
        description="Redis URL for distributed rate limiting"
    )
    
    class Config:
        use_enum_values = True