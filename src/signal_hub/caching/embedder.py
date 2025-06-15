"""Fast embedding generation for caching."""

import hashlib
import logging
from typing import List, Optional, Dict, Any
from functools import lru_cache

from signal_hub.indexing.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


class CacheEmbedder:
    """Fast embedder optimized for cache queries."""
    
    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        cache_size: int = 1000
    ):
        """Initialize cache embedder.
        
        Args:
            embedding_provider: Provider for embeddings (or create default)
            cache_size: Size of embedding cache
        """
        self.embedding_provider = embedding_provider
        self._embedding_cache = {}  # Simple dict cache
        self.cache_size = cache_size
        
    async def embed(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[float]:
        """Generate embedding for text with caching.
        
        Args:
            text: Text to embed
            context: Optional context for cache key
            
        Returns:
            Embedding vector
        """
        # Create cache key
        cache_key = self._create_cache_key(text, context)
        
        # Check cache
        if cache_key in self._embedding_cache:
            logger.debug(f"Embedding cache hit for key: {cache_key[:8]}...")
            return self._embedding_cache[cache_key]
            
        # Generate embedding
        if self.embedding_provider:
            embedding = await self.embedding_provider.embed_text(text)
        else:
            # Fallback to simple hash-based embedding for testing
            embedding = self._create_mock_embedding(text)
            
        # Cache result
        self._cache_embedding(cache_key, embedding)
        
        return embedding
        
    def _create_cache_key(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create cache key from text and context."""
        key_parts = [text]
        
        if context:
            # Add relevant context to key
            if "file_path" in context:
                key_parts.append(f"file:{context['file_path']}")
            if "project" in context:
                key_parts.append(f"project:{context['project']}")
                
        key_string = "|".join(key_parts)
        
        # Hash for consistent length
        return hashlib.sha256(key_string.encode()).hexdigest()
        
    def _create_mock_embedding(self, text: str) -> List[float]:
        """Create mock embedding for testing without real provider."""
        # Simple deterministic embedding based on text
        # This is just for testing - real embeddings come from provider
        
        # Use hash to generate consistent values
        text_hash = hashlib.md5(text.encode()).digest()
        
        # Convert to floats in range [-1, 1]
        embedding = []
        for i in range(0, min(len(text_hash), 384)):  # 384 dimensions like sentence-transformers
            byte_val = text_hash[i % len(text_hash)]
            normalized = (byte_val / 127.5) - 1.0  # Normalize to [-1, 1]
            embedding.append(normalized)
            
        # Pad to standard size if needed
        while len(embedding) < 384:
            embedding.append(0.0)
            
        return embedding[:384]  # Ensure exactly 384 dimensions
        
    def _cache_embedding(self, key: str, embedding: List[float]):
        """Cache embedding with size limit."""
        # Simple FIFO eviction if cache is full
        if len(self._embedding_cache) >= self.cache_size:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._embedding_cache))
            del self._embedding_cache[oldest_key]
            
        self._embedding_cache[key] = embedding
        
    def clear_cache(self):
        """Clear embedding cache."""
        self._embedding_cache.clear()
        logger.info("Cleared embedding cache")
        
    @property
    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self._embedding_cache),
            "max_size": self.cache_size,
            "utilization": (len(self._embedding_cache) / self.cache_size) * 100
        }