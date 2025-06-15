"""Anthropic Claude model provider."""

import os
import logging
from typing import Dict, Any, Optional, AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import Message

from signal_hub.routing.models import ModelType
from signal_hub.routing.providers.base import ModelProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic Claude models."""
    
    # Model information
    MODEL_INFO = {
        ModelType.HAIKU: {
            "max_tokens": 200000,
            "max_output": 4096,
            "cost_per_1m_input": 0.25,
            "cost_per_1m_output": 1.25,
            "context_window": 200000,
        },
        ModelType.SONNET: {
            "max_tokens": 200000,
            "max_output": 8192,
            "cost_per_1m_input": 3.00,
            "cost_per_1m_output": 15.00,
            "context_window": 200000,
        },
        ModelType.OPUS: {
            "max_tokens": 200000,
            "max_output": 4096,
            "cost_per_1m_input": 15.00,
            "cost_per_1m_output": 75.00,
            "context_window": 200000,
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")
            
        self.client = AsyncAnthropic(api_key=self.api_key)
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return "anthropic"
        
    async def complete(
        self,
        model: ModelType,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion from Claude model."""
        try:
            # Get model info
            model_info = self.get_model_info(model)
            if max_tokens is None:
                max_tokens = model_info["max_output"]
                
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                    
            # Create message
            response = await self.client.messages.create(
                model=model.value,
                messages=anthropic_messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            
            if stream:
                return {"stream": response}
                
            # Extract completion
            return {
                "content": response.content[0].text,
                "model": model.value,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "stop_reason": response.stop_reason
            }
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise
            
    async def stream_complete(
        self,
        model: ModelType,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion from Claude model."""
        response = await self.complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        # Stream response chunks
        async for chunk in response["stream"]:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text
                
    async def count_tokens(self, text: str, model: ModelType) -> int:
        """Count tokens for given text.
        
        Note: This is an approximation. Anthropic doesn't provide
        a public tokenizer, so we estimate.
        """
        # Rough approximation: 1 token ≈ 4 characters
        # This matches our Query.estimated_tokens logic
        return len(text) // 4
        
    def get_model_info(self, model: ModelType) -> Dict[str, Any]:
        """Get information about a model."""
        if model not in self.MODEL_INFO:
            raise ValueError(f"Unknown model: {model}")
            
        return self.MODEL_INFO[model].copy()
        
    def is_available(self, model: ModelType) -> bool:
        """Check if model is available."""
        return model in self.MODEL_INFO and self.api_key is not None
        
    def calculate_cost(
        self,
        model: ModelType,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for tokens used.
        
        Args:
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        info = self.get_model_info(model)
        
        input_cost = (input_tokens / 1_000_000) * info["cost_per_1m_input"]
        output_cost = (output_tokens / 1_000_000) * info["cost_per_1m_output"]
        
        return input_cost + output_cost