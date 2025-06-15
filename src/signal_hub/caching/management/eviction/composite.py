"""Composite eviction strategy combining multiple strategies."""

import logging
from typing import List, Set, Dict, Any, Optional

from signal_hub.caching.models import CachedResponse
from signal_hub.caching.strategies.ttl import TTLEvictionStrategy
from signal_hub.caching.strategies.lru import LRUEvictionStrategy
from signal_hub.caching.strategies.quality import QualityBasedEvictionStrategy

logger = logging.getLogger(__name__)


class CompositeEvictionStrategy:
    """Combines multiple eviction strategies."""
    
    def __init__(
        self,
        strategies: Optional[List[str]] = None,
        ttl_seconds: int = 86400  # 24 hours
    ):
        """Initialize composite strategy.
        
        Args:
            strategies: List of strategy names to use
            ttl_seconds: TTL for TTL strategy
        """
        self.strategies = strategies or ["ttl", "quality", "lru"]
        
        # Initialize individual strategies
        self.ttl_strategy = TTLEvictionStrategy(ttl_seconds)
        self.lru_strategy = LRUEvictionStrategy()
        self.quality_strategy = QualityBasedEvictionStrategy()
        
    def select_for_eviction(
        self,
        entries: List[CachedResponse],
        target_count: int
    ) -> Set[str]:
        """Select entries for eviction using multiple strategies.
        
        Args:
            entries: All cache entries
            target_count: Number of entries to evict
            
        Returns:
            Set of entry IDs to evict
        """
        evict_ids = set()
        remaining_target = target_count
        
        # Apply strategies in order
        for strategy_name in self.strategies:
            if remaining_target <= 0:
                break
                
            if strategy_name == "ttl":
                # First, remove all expired entries
                ttl_evictions = self.ttl_strategy.select_for_eviction(
                    entries, None  # Get all expired
                )
                evict_ids.update(ttl_evictions)
                remaining_target -= len(ttl_evictions)
                
            elif strategy_name == "quality" and remaining_target > 0:
                # Then remove low-quality entries
                # Filter out already selected entries
                remaining_entries = [
                    e for e in entries if e.id not in evict_ids
                ]
                quality_evictions = self.quality_strategy.select_for_eviction(
                    remaining_entries, remaining_target
                )
                evict_ids.update(quality_evictions)
                remaining_target -= len(quality_evictions)
                
            elif strategy_name == "lru" and remaining_target > 0:
                # Finally use LRU for remaining
                remaining_entries = [
                    e for e in entries if e.id not in evict_ids
                ]
                lru_evictions = self.lru_strategy.select_for_eviction(
                    remaining_entries, remaining_target
                )
                evict_ids.update(lru_evictions)
                remaining_target -= len(lru_evictions)
                
        logger.info(
            f"Composite strategy selected {len(evict_ids)} entries for eviction "
            f"(target was {target_count})"
        )
        
        return evict_ids