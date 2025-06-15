"""In-memory cache storage implementation."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np

from signal_hub.caching.models import CachedResponse, CacheSearchResult, CacheEntryStatus
from signal_hub.caching.storage.base import CacheStorage

logger = logging.getLogger(__name__)


class MemoryCacheStorage(CacheStorage):
    """In-memory cache storage using dictionaries and numpy."""
    
    def __init__(self, max_entries: int = 10000):
        """Initialize memory storage.
        
        Args:
            max_entries: Maximum number of entries to store
        """
        self.max_entries = max_entries
        self.entries: Dict[str, CachedResponse] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        
    async def initialize(self):
        """Initialize storage backend."""
        self._initialized = True
        logger.info(f"Initialized memory cache storage (max_entries={self.max_entries})")
        
    async def add(self, entry: CachedResponse) -> bool:
        """Add entry to cache."""
        async with self._lock:
            # Check size limit
            if len(self.entries) >= self.max_entries:
                logger.warning("Cache is full, cannot add new entry")
                return False
                
            # Store entry and embedding
            self.entries[entry.id] = entry
            self.embeddings[entry.id] = np.array(entry.query_embedding)
            
            logger.debug(f"Added cache entry: {entry.id}")
            return True
            
    async def search_similar(
        self,
        query_embedding: List[float],
        threshold: float = 0.85,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> List[CacheSearchResult]:
        """Search for similar cached queries using cosine similarity."""
        if not self.entries:
            return []
            
        query_vec = np.array(query_embedding)
        results = []
        
        async with self._lock:
            for entry_id, entry in self.entries.items():
                # Skip expired entries
                if entry.is_expired:
                    continue
                    
                # Apply context filter if provided
                if context and not self._matches_context(entry, context):
                    continue
                    
                # Calculate cosine similarity
                entry_vec = self.embeddings[entry_id]
                similarity = self._cosine_similarity(query_vec, entry_vec)
                
                if similarity >= threshold:
                    results.append(CacheSearchResult(
                        entry=entry,
                        similarity_score=similarity
                    ))
                    
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
        
    async def get(self, entry_id: str) -> Optional[CachedResponse]:
        """Get specific cache entry by ID."""
        async with self._lock:
            return self.entries.get(entry_id)
            
    async def update(self, entry: CachedResponse) -> bool:
        """Update existing cache entry."""
        async with self._lock:
            if entry.id not in self.entries:
                return False
                
            self.entries[entry.id] = entry
            self.embeddings[entry.id] = np.array(entry.query_embedding)
            return True
            
    async def delete(self, entry_id: str) -> bool:
        """Delete cache entry."""
        async with self._lock:
            if entry_id in self.entries:
                del self.entries[entry_id]
                del self.embeddings[entry_id]
                logger.debug(f"Deleted cache entry: {entry_id}")
                return True
            return False
            
    async def clear(self) -> int:
        """Clear all cache entries."""
        async with self._lock:
            count = len(self.entries)
            self.entries.clear()
            self.embeddings.clear()
            logger.info(f"Cleared {count} cache entries")
            return count
            
    async def size(self) -> int:
        """Get number of cache entries."""
        return len(self.entries)
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        async with self._lock:
            total_entries = len(self.entries)
            expired_count = sum(1 for e in self.entries.values() if e.is_expired)
            
            # Estimate memory usage
            entry_size = 0
            if self.entries:
                # Sample first entry for size estimation
                sample_entry = next(iter(self.entries.values()))
                entry_size = len(str(sample_entry.to_dict()).encode())
                
            embedding_size = 0
            if self.embeddings:
                # Each embedding is float32 * dimensions
                sample_embedding = next(iter(self.embeddings.values()))
                embedding_size = sample_embedding.nbytes
                
            estimated_memory_mb = (
                (entry_size * total_entries + embedding_size * total_entries) / 1024 / 1024
            )
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "active_entries": total_entries - expired_count,
                "max_entries": self.max_entries,
                "utilization": (total_entries / self.max_entries) * 100,
                "estimated_memory_mb": estimated_memory_mb
            }
            
    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        async with self._lock:
            expired_ids = [
                entry_id for entry_id, entry in self.entries.items()
                if entry.is_expired
            ]
            
            for entry_id in expired_ids:
                del self.entries[entry_id]
                del self.embeddings[entry_id]
                
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired cache entries")
                
            return len(expired_ids)
            
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Ensure result is in [0, 1] range
        return float(np.clip(similarity, -1.0, 1.0))
        
    def _matches_context(self, entry: CachedResponse, context: Dict[str, Any]) -> bool:
        """Check if entry matches the given context."""
        if not entry.context:
            return True  # No context to match
            
        # Check each context key
        for key, value in context.items():
            if key in entry.context and entry.context[key] != value:
                return False
                
        return True