"""TTL-based cache eviction strategy."""

import logging
from typing import List, Set
from datetime import datetime

from signal_hub.caching.models import CachedResponse

logger = logging.getLogger(__name__)


class TTLEvictionStrategy:
    """Evict cache entries based on time-to-live."""
    
    def __init__(self, ttl_seconds: int):
        """Initialize TTL strategy.
        
        Args:
            ttl_seconds: Default TTL for entries
        """
        self.ttl_seconds = ttl_seconds
        
    def select_for_eviction(
        self,
        entries: List[CachedResponse],
        target_count: int = None
    ) -> Set[str]:
        """Select entries for eviction based on TTL.
        
        Args:
            entries: All cache entries
            target_count: Optional target number to evict
            
        Returns:
            Set of entry IDs to evict
        """
        expired_ids = set()
        
        for entry in entries:
            if entry.is_expired:
                expired_ids.add(entry.id)
                
        logger.debug(f"TTL strategy found {len(expired_ids)} expired entries")
        
        # If we have a target count and found more, sort by age
        if target_count and len(expired_ids) > target_count:
            # Sort by age and take oldest
            sorted_entries = sorted(
                [e for e in entries if e.id in expired_ids],
                key=lambda e: e.timestamp
            )
            expired_ids = {e.id for e in sorted_entries[:target_count]}
            
        return expired_ids