"""Quality-based cache eviction strategy."""

import logging
from typing import List, Set, Dict, Any

from signal_hub.caching.models import CachedResponse

logger = logging.getLogger(__name__)


class QualityBasedEvictionStrategy:
    """Evict cache entries based on quality metrics."""
    
    def __init__(
        self,
        min_hit_count: int = 2,
        min_similarity_score: float = 0.9
    ):
        """Initialize quality-based strategy.
        
        Args:
            min_hit_count: Minimum hits to be considered high quality
            min_similarity_score: Minimum similarity for high quality
        """
        self.min_hit_count = min_hit_count
        self.min_similarity_score = min_similarity_score
        
    def select_for_eviction(
        self,
        entries: List[CachedResponse],
        target_count: int
    ) -> Set[str]:
        """Select low-quality entries for eviction.
        
        Args:
            entries: All cache entries
            target_count: Number of entries to evict
            
        Returns:
            Set of entry IDs to evict
        """
        if not entries or target_count <= 0:
            return set()
            
        # Calculate quality scores
        scored_entries = []
        for entry in entries:
            score = self._calculate_quality_score(entry)
            scored_entries.append((entry, score))
            
        # Sort by quality score (lowest first)
        scored_entries.sort(key=lambda x: x[1])
        
        # Select lowest quality entries for eviction
        evict_ids = {
            entry.id for entry, _ in scored_entries[:target_count]
        }
        
        logger.debug(
            f"Quality strategy selected {len(evict_ids)} low-quality entries for eviction"
        )
        
        return evict_ids
        
    def _calculate_quality_score(self, entry: CachedResponse) -> float:
        """Calculate quality score for entry.
        
        Args:
            entry: Cache entry
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        score = 0.0
        
        # Hit count factor (normalized to 0-0.4)
        hit_factor = min(entry.hit_count / 10, 0.4)
        score += hit_factor
        
        # Recency factor (0-0.3)
        age_hours = entry.age_seconds / 3600
        if age_hours < 1:
            recency_factor = 0.3
        elif age_hours < 24:
            recency_factor = 0.2
        elif age_hours < 168:  # 1 week
            recency_factor = 0.1
        else:
            recency_factor = 0.0
        score += recency_factor
        
        # Model factor (0-0.3)
        # Prefer caching expensive model responses
        model_factors = {
            "opus": 0.3,
            "sonnet": 0.2,
            "haiku": 0.1
        }
        model_name = entry.model.lower()
        for key, factor in model_factors.items():
            if key in model_name:
                score += factor
                break
                
        return score