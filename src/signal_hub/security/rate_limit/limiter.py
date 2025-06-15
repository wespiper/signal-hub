"""Rate limiting implementation."""

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, Optional

from signal_hub.routing.models import ModelType
from signal_hub.utils.logging import get_logger
from .models import RateLimitConfig, RateLimitExceeded


logger = get_logger(__name__)


class RateLimitBackend(ABC):
    """Abstract base for rate limit backends."""
    
    @abstractmethod
    async def get_usage(self, key: str, window: int) -> int:
        """Get current usage for a key."""
        pass
    
    @abstractmethod
    async def increment(self, key: str, window: int, amount: int = 1) -> int:
        """Increment usage and return new value."""
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset usage for a key."""
        pass


class MemoryBackend(RateLimitBackend):
    """In-memory rate limit backend."""
    
    def __init__(self):
        # Store: key -> (timestamp, count)
        self._usage: Dict[str, Dict[float, int]] = defaultdict(dict)
    
    async def get_usage(self, key: str, window: int) -> int:
        """Get current usage within window."""
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Clean old entries and sum recent ones
        usage = 0
        timestamps_to_remove = []
        
        for timestamp, count in self._usage[key].items():
            if timestamp < cutoff_time:
                timestamps_to_remove.append(timestamp)
            else:
                usage += count
        
        # Remove old entries
        for timestamp in timestamps_to_remove:
            del self._usage[key][timestamp]
        
        return usage
    
    async def increment(self, key: str, window: int, amount: int = 1) -> int:
        """Increment usage."""
        current_time = time.time()
        
        # Add to current timestamp
        self._usage[key][current_time] = amount
        
        # Return total usage
        return await self.get_usage(key, window)
    
    async def reset(self, key: str) -> None:
        """Reset usage for a key."""
        if key in self._usage:
            del self._usage[key]


class RateLimiter:
    """Main rate limiting class."""
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.backend = self._create_backend()
    
    def _create_backend(self) -> RateLimitBackend:
        """Create appropriate backend."""
        if self.config.backend == "memory":
            return MemoryBackend()
        elif self.config.backend == "redis":
            # TODO: Implement Redis backend
            logger.warning("Redis backend not implemented, falling back to memory")
            return MemoryBackend()
        else:
            raise ValueError(f"Unknown backend: {self.config.backend}")
    
    async def check_limit(
        self,
        key: str,
        model: Optional[ModelType] = None,
        cost: int = 1
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., user ID, IP)
            model: Model being used (for model-specific limits)
            cost: Request cost (default 1)
            
        Returns:
            True if within limit
            
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        if not self.config.enabled:
            return True
        
        # Determine limit
        limit = self._get_limit(key, model)
        
        # Check current usage
        current = await self.backend.get_usage(key, self.config.window_seconds)
        
        if current + cost > limit:
            raise RateLimitExceeded(key, limit, current)
        
        # Increment usage
        await self.backend.increment(key, self.config.window_seconds, cost)
        
        return True
    
    def _get_limit(self, key: str, model: Optional[ModelType]) -> int:
        """Get applicable limit for key and model."""
        # Check user-specific limit
        if key in self.config.user_limits:
            return self.config.user_limits[key]
        
        # Check model-specific limit
        if model and model in self.config.model_limits:
            return self.config.model_limits[model]
        
        # Default limit
        return self.config.default_limit
    
    async def get_remaining(
        self,
        key: str,
        model: Optional[ModelType] = None
    ) -> int:
        """
        Get remaining requests for a key.
        
        Args:
            key: Rate limit key
            model: Model being used
            
        Returns:
            Number of remaining requests
        """
        if not self.config.enabled:
            return float('inf')
        
        limit = self._get_limit(key, model)
        current = await self.backend.get_usage(key, self.config.window_seconds)
        
        return max(0, limit - current)
    
    async def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.
        
        Args:
            key: Rate limit key to reset
        """
        await self.backend.reset(key)
        logger.info(f"Reset rate limit for {key}")
    
    def get_headers(
        self,
        key: str,
        model: Optional[ModelType] = None
    ) -> Dict[str, str]:
        """
        Get rate limit headers for response.
        
        Args:
            key: Rate limit key
            model: Model being used
            
        Returns:
            Dict of headers to include
        """
        if not self.config.enabled:
            return {}
        
        limit = self._get_limit(key, model)
        remaining = self.get_remaining(key, model)
        reset_time = int(time.time()) + self.config.window_seconds
        
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }