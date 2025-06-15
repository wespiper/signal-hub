"""Cache store interface for database abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CacheStore(ABC):
    """Abstract base class for cache stores.
    
    This interface allows swapping between different cache backends
    (SQLite, Redis, Memcached, etc.) without changing application code.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
        
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists
        """
        pass
        
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs (only existing keys)
        """
        pass
        
    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache.
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        pass
        
    async def increment(
        self,
        key: str,
        delta: int = 1
    ) -> Optional[int]:
        """Increment a numeric value.
        
        Args:
            key: Cache key
            delta: Amount to increment
            
        Returns:
            New value after increment, None if key doesn't exist
            
        Note: This is optional - not all stores may support it
        """
        raise NotImplementedError("This store does not support increment")
        
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful
            
        Note: This is optional - not all stores may support it
        """
        raise NotImplementedError("This store does not support expiration")
        
    async def health_check(self) -> bool:
        """Check if the cache is healthy and accessible.
        
        Returns:
            True if healthy
        """
        try:
            test_key = "_health_check_"
            await self.set(test_key, "ok", ttl=1)
            result = await self.get(test_key)
            await self.delete(test_key)
            return result == "ok"
        except Exception:
            return False