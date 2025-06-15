"""LRU (Least Recently Used) cache eviction strategy."""

import logging
from typing import List, Set
from datetime import datetime

from signal_hub.caching.models import CachedResponse

logger = logging.getLogger(__name__)


class LRUEvictionStrategy:
    """Evict least recently used cache entries."""
    
    def select_for_eviction(
        self,
        entries: List[CachedResponse],
        target_count: int
    ) -> Set[str]:
        """Select entries for eviction based on LRU.
        
        Args:
            entries: All cache entries
            target_count: Number of entries to evict
            
        Returns:
            Set of entry IDs to evict
        """
        if not entries or target_count <= 0:
            return set()
            
        # Sort by last accessed time (oldest first)
        # Entries never accessed use timestamp as fallback
        sorted_entries = sorted(
            entries,
            key=lambda e: e.last_accessed or e.timestamp
        )
        
        # Select oldest entries for eviction
        evict_ids = {
            entry.id for entry in sorted_entries[:target_count]
        }
        
        logger.debug(f"LRU strategy selected {len(evict_ids)} entries for eviction")
        
        return evict_ids