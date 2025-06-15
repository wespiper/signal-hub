"""Cache management implementation."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from signal_hub.caching.models import CacheConfig, CacheStats
from signal_hub.caching.storage.base import CacheStorage
from signal_hub.caching.management.eviction.composite import CompositeEvictionStrategy

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages cache lifecycle including eviction and maintenance."""
    
    def __init__(
        self,
        storage: CacheStorage,
        config: CacheConfig,
        eviction_strategy: Optional[CompositeEvictionStrategy] = None
    ):
        """Initialize cache manager.
        
        Args:
            storage: Cache storage backend
            config: Cache configuration
            eviction_strategy: Eviction strategy (or use default)
        """
        self.storage = storage
        self.config = config
        self.eviction_strategy = eviction_strategy or CompositeEvictionStrategy(
            ttl_seconds=config.ttl_seconds
        )
        
        self._maintenance_task = None
        self._maintenance_interval = 3600  # 1 hour
        self._running = False
        
    async def start_maintenance(self, interval_seconds: Optional[int] = None):
        """Start background maintenance task.
        
        Args:
            interval_seconds: Maintenance interval (or use default)
        """
        if self._maintenance_task:
            logger.warning("Maintenance already running")
            return
            
        self._maintenance_interval = interval_seconds or self._maintenance_interval
        self._running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        logger.info(f"Started cache maintenance (interval: {self._maintenance_interval}s)")
        
    async def stop_maintenance(self):
        """Stop background maintenance task."""
        self._running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
            self._maintenance_task = None
        logger.info("Stopped cache maintenance")
        
    async def _maintenance_loop(self):
        """Background maintenance loop."""
        while self._running:
            try:
                await asyncio.sleep(self._maintenance_interval)
                await self.run_maintenance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                
    async def run_maintenance(self):
        """Run cache maintenance tasks."""
        logger.debug("Running cache maintenance")
        
        # 1. Clean up expired entries
        expired_count = await self.storage.cleanup_expired()
        
        # 2. Check size limits and evict if needed
        evicted_count = await self._check_and_evict()
        
        # 3. Optimize storage if supported
        await self._optimize_storage()
        
        logger.info(
            f"Maintenance complete: {expired_count} expired, "
            f"{evicted_count} evicted"
        )
        
    async def _check_and_evict(self) -> int:
        """Check cache size and evict if needed.
        
        Returns:
            Number of entries evicted
        """
        current_size = await self.storage.size()
        
        if current_size <= self.config.max_entries:
            return 0
            
        # Calculate how many to evict
        target_evictions = current_size - int(self.config.max_entries * 0.9)  # 90% target
        
        logger.info(
            f"Cache over limit ({current_size}/{self.config.max_entries}), "
            f"evicting {target_evictions} entries"
        )
        
        # Get all entries (this could be optimized for large caches)
        # In production, would use pagination
        all_entries = []
        stats = await self.storage.get_stats()
        
        # For now, we'll use a simpler approach
        # Real implementation would fetch entries in batches
        evicted = 0
        
        # Use eviction strategy to select entries
        # This is simplified - real implementation would be more efficient
        if hasattr(self.storage, 'entries'):
            entries = list(self.storage.entries.values())
            evict_ids = self.eviction_strategy.select_for_eviction(
                entries, target_evictions
            )
            
            for entry_id in evict_ids:
                if await self.storage.delete(entry_id):
                    evicted += 1
                    
        return evicted
        
    async def _optimize_storage(self):
        """Optimize storage backend."""
        # Storage-specific optimization
        if hasattr(self.storage, 'optimize'):
            await self.storage.optimize()
            
    async def evict_all(self) -> int:
        """Evict all cache entries.
        
        Returns:
            Number of entries evicted
        """
        count = await self.storage.clear()
        logger.info(f"Evicted all {count} cache entries")
        return count
        
    async def evict_pattern(self, pattern: str) -> int:
        """Evict entries matching pattern.
        
        Args:
            pattern: Pattern to match (in query text)
            
        Returns:
            Number of entries evicted
        """
        evicted = 0
        
        # This is simplified - real implementation would be more efficient
        if hasattr(self.storage, 'entries'):
            matching_ids = []
            for entry_id, entry in self.storage.entries.items():
                if pattern in entry.query:
                    matching_ids.append(entry_id)
                    
            for entry_id in matching_ids:
                if await self.storage.delete(entry_id):
                    evicted += 1
                    
        logger.info(f"Evicted {evicted} entries matching pattern '{pattern}'")
        return evicted
        
    async def get_management_stats(self) -> Dict[str, Any]:
        """Get cache management statistics.
        
        Returns:
            Management statistics
        """
        storage_stats = await self.storage.get_stats()
        
        # Calculate health metrics
        utilization = (
            storage_stats.get('total_entries', 0) / self.config.max_entries * 100
        )
        
        expired_ratio = (
            storage_stats.get('expired_entries', 0) / 
            max(1, storage_stats.get('total_entries', 1)) * 100
        )
        
        return {
            "storage": storage_stats,
            "config": {
                "max_entries": self.config.max_entries,
                "ttl_hours": self.config.ttl_hours,
                "eviction_strategy": self.config.eviction_strategy
            },
            "health": {
                "utilization_percent": utilization,
                "expired_ratio_percent": expired_ratio,
                "maintenance_running": self._running,
                "last_maintenance": getattr(self, '_last_maintenance', None)
            }
        }