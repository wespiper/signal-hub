"""Base interface for cache storage backends."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from signal_hub.caching.models import CachedResponse, CacheSearchResult


class CacheStorage(ABC):
    """Abstract base class for cache storage."""
    
    @abstractmethod
    async def initialize(self):
        """Initialize storage backend."""
        pass
        
    @abstractmethod
    async def add(self, entry: CachedResponse) -> bool:
        """Add entry to cache.
        
        Args:
            entry: Cache entry to add
            
        Returns:
            True if added successfully
        """
        pass
        
    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        threshold: float = 0.85,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> List[CacheSearchResult]:
        """Search for similar cached queries.
        
        Args:
            query_embedding: Embedding of query
            threshold: Minimum similarity threshold
            limit: Maximum results to return
            context: Optional context for filtering
            
        Returns:
            List of similar cache entries
        """
        pass
        
    @abstractmethod
    async def get(self, entry_id: str) -> Optional[CachedResponse]:
        """Get specific cache entry by ID.
        
        Args:
            entry_id: ID of cache entry
            
        Returns:
            Cache entry or None if not found
        """
        pass
        
    @abstractmethod
    async def update(self, entry: CachedResponse) -> bool:
        """Update existing cache entry.
        
        Args:
            entry: Updated cache entry
            
        Returns:
            True if updated successfully
        """
        pass
        
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete cache entry.
        
        Args:
            entry_id: ID of entry to delete
            
        Returns:
            True if deleted successfully
        """
        pass
        
    @abstractmethod
    async def clear(self) -> int:
        """Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        pass
        
    @abstractmethod
    async def size(self) -> int:
        """Get number of cache entries.
        
        Returns:
            Number of entries
        """
        pass
        
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Storage statistics
        """
        pass
        
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        pass