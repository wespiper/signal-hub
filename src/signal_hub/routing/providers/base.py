"""Base interface for model providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
import logging

from signal_hub.routing.models import ModelType

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Base class for AI model providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name."""
        pass
        
    @abstractmethod
    async def complete(
        self,
        model: ModelType,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion from model.
        
        Args:
            model: Model to use
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Completion response
        """
        pass
        
    @abstractmethod
    async def count_tokens(self, text: str, model: ModelType) -> int:
        """Count tokens for given text and model.
        
        Args:
            text: Text to count tokens for
            model: Model to use for counting
            
        Returns:
            Token count
        """
        pass
        
    @abstractmethod
    def get_model_info(self, model: ModelType) -> Dict[str, Any]:
        """Get information about a model.
        
        Args:
            model: Model to get info for
            
        Returns:
            Model information including limits, pricing, etc.
        """
        pass
        
    @abstractmethod
    def is_available(self, model: ModelType) -> bool:
        """Check if model is available.
        
        Args:
            model: Model to check
            
        Returns:
            True if model is available
        """
        pass
        
    async def stream_complete(
        self,
        model: ModelType,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from model.
        
        Args:
            model: Model to use
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Completion chunks
        """
        # Default implementation calls complete() - providers can override
        response = await self.complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )
        
        # Yield entire response as single chunk
        if "content" in response:
            yield response["content"]
        elif "text" in response:
            yield response["text"]