"""Main semantic cache implementation."""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from signal_hub.caching.models import (
    CachedResponse, CacheConfig, CacheStats, CacheSearchResult
)
from signal_hub.caching.embedder import CacheEmbedder
from signal_hub.caching.storage.base import CacheStorage
from signal_hub.caching.storage.memory import MemoryCacheStorage

logger = logging.getLogger(__name__)


class SemanticCache:
    """Semantic cache for query responses."""
    
    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        storage: Optional[CacheStorage] = None,
        embedder: Optional[CacheEmbedder] = None
    ):
        """Initialize semantic cache.
        
        Args:
            config: Cache configuration
            storage: Storage backend (or create default)
            embedder: Embedder for queries (or create default)
        """
        self.config = config or CacheConfig()
        self.config.validate()
        
        # Initialize storage
        if storage:
            self.storage = storage
        elif self.config.storage_backend == "memory":
            self.storage = MemoryCacheStorage(max_entries=self.config.max_entries)
        else:
            # For persistent storage, would use ChromaDB or similar
            raise NotImplementedError("Persistent storage not yet implemented")
            
        # Initialize embedder
        self.embedder = embedder or CacheEmbedder()
        
        # Statistics
        self.stats = CacheStats()
        self._initialized = False
        
    async def initialize(self):
        """Initialize cache components."""
        if self._initialized:
            return
            
        await self.storage.initialize()
        self._initialized = True
        logger.info("Semantic cache initialized")
        
    async def get(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached response for query.
        
        Args:
            query: Query text
            context: Optional context for matching
            
        Returns:
            Cached response or None if not found
        """
        if not self.config.enabled:
            return None
            
        start_time = datetime.utcnow()
        
        try:
            # Generate embedding for query
            embedding = await self.embedder.embed(query, context)
            
            # Search for similar entries
            results = await self.storage.search_similar(
                query_embedding=embedding,
                threshold=self.config.similarity_threshold,
                limit=1,  # Only need best match
                context=context if self.config.context_aware else None
            )
            
            if results and results[0].is_valid:
                # Found valid cache hit
                result = results[0]
                entry = result.entry
                
                # Update hit statistics
                entry.record_hit()
                await self.storage.update(entry)
                
                # Record metrics
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.stats.record_hit(result.similarity_score, duration_ms)
                
                logger.info(
                    f"Cache hit! Similarity: {result.similarity_score:.3f}, "
                    f"Response time: {duration_ms:.1f}ms"
                )
                
                return entry.response
                
            else:
                # Cache miss
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.stats.record_miss(duration_ms)
                
                logger.debug(f"Cache miss for query: {query[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error in cache lookup: {e}")
            return None
            
    async def put(
        self,
        query: str,
        response: Dict[str, Any],
        model: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store query-response pair in cache.
        
        Args:
            query: Query text
            response: Response to cache
            model: Model that generated response
            context: Optional context
            metadata: Optional metadata
            
        Returns:
            True if stored successfully
        """
        if not self.config.enabled:
            return False
            
        try:
            # Generate embedding
            embedding = await self.embedder.embed(query, context)
            
            # Create cache entry
            entry = CachedResponse(
                id=str(uuid.uuid4()),
                query=query,
                query_embedding=embedding,
                response=response,
                model=model,
                timestamp=datetime.utcnow(),
                ttl_seconds=self.config.ttl_seconds,
                context=context,
                metadata=metadata or {}
            )
            
            # Store in cache
            success = await self.storage.add(entry)
            
            if success:
                self.stats.total_entries = await self.storage.size()
                logger.debug(f"Cached response for: {query[:50]}...")
                
            return success
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False
            
    async def invalidate(self, entry_id: str) -> bool:
        """Invalidate specific cache entry.
        
        Args:
            entry_id: ID of entry to invalidate
            
        Returns:
            True if invalidated successfully
        """
        return await self.storage.delete(entry_id)
        
    async def clear(self) -> int:
        """Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = await self.storage.clear()
        self.stats.total_entries = 0
        logger.info(f"Cleared {count} cache entries")
        return count
        
    async def cleanup(self) -> int:
        """Clean up expired entries.
        
        Returns:
            Number of entries removed
        """
        count = await self.storage.cleanup_expired()
        self.stats.evictions += count
        self.stats.total_entries = await self.storage.size()
        return count
        
    async def search(
        self,
        query: str,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> List[CacheSearchResult]:
        """Search for similar cached queries.
        
        Args:
            query: Query to search for
            limit: Maximum results
            context: Optional context filter
            
        Returns:
            List of similar cache entries
        """
        # Generate embedding
        embedding = await self.embedder.embed(query, context)
        
        # Search storage
        return await self.storage.search_similar(
            query_embedding=embedding,
            threshold=self.config.similarity_threshold,
            limit=limit,
            context=context if self.config.context_aware else None
        )
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Combined statistics
        """
        storage_stats = await self.storage.get_stats()
        embedder_stats = self.embedder.cache_stats
        
        return {
            "cache_stats": {
                "total_queries": self.stats.total_queries,
                "hit_rate": self.stats.hit_rate,
                "miss_rate": self.stats.miss_rate,
                "average_similarity": self.stats.average_similarity,
                "average_response_time_ms": self.stats.average_response_time_ms,
                "evictions": self.stats.evictions
            },
            "storage_stats": storage_stats,
            "embedder_stats": embedder_stats,
            "config": {
                "enabled": self.config.enabled,
                "similarity_threshold": self.config.similarity_threshold,
                "ttl_hours": self.config.ttl_hours,
                "max_entries": self.config.max_entries
            }
        }
        
    async def warm_cache(self, common_queries: List[Dict[str, Any]]):
        """Warm cache with common queries.
        
        Args:
            common_queries: List of dicts with 'query', 'response', 'model'
        """
        success_count = 0
        
        for item in common_queries:
            success = await self.put(
                query=item["query"],
                response=item["response"],
                model=item.get("model", "unknown"),
                context=item.get("context"),
                metadata={"warmed": True}
            )
            
            if success:
                success_count += 1
                
        logger.info(f"Warmed cache with {success_count}/{len(common_queries)} entries")
        
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SemanticCache(enabled={self.config.enabled}, "
            f"threshold={self.config.similarity_threshold}, "
            f"entries={self.stats.total_entries}, "
            f"hit_rate={self.stats.hit_rate:.1f}%)"
        )