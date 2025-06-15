"""Result ranking and reranking algorithms."""

import logging
from typing import List, Dict, Any
from datetime import datetime

from signal_hub.retrieval.search.models import SearchResult, SearchQuery, SearchConfig

logger = logging.getLogger(__name__)


class ResultRanker:
    """Ranks and reranks search results."""
    
    def __init__(self, config: SearchConfig):
        """Initialize ranker with configuration."""
        self.config = config
        
    def rerank(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Rerank results based on multiple factors.
        
        Args:
            results: Initial search results
            query: Original search query
            
        Returns:
            Reranked results
        """
        if not results:
            return results
            
        # Calculate additional scores
        for result in results:
            # Base score from vector similarity
            base_score = result.score
            
            # Metadata boost
            metadata_score = 0.0
            if self.config.use_metadata_boost:
                metadata_score = self._calculate_metadata_score(result, query)
                
            # Recency boost
            recency_score = 0.0
            if query.boost_recent and self.config.recency_weight > 0:
                recency_score = self._calculate_recency_score(result)
                
            # Type boost (functions/classes typically more relevant)
            type_score = self._calculate_type_score(result)
            
            # Length penalty (very short or very long chunks less useful)
            length_score = self._calculate_length_score(result)
            
            # Combine scores
            final_score = (
                base_score * 0.6 +
                metadata_score * 0.2 +
                type_score * 0.1 +
                recency_score * self.config.recency_weight +
                length_score * 0.05
            )
            
            # Apply query-specific boosts
            if query.filters:
                # Boost results that match more filters
                filter_score = self._calculate_filter_match_score(result, query.filters)
                final_score += filter_score * 0.05
                
            result.score = final_score
            
        # Sort by final score
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results
        
    def _calculate_metadata_score(self, result: SearchResult, query: SearchQuery) -> float:
        """Calculate score based on metadata relevance."""
        score = 0.0
        metadata = result.metadata
        
        # Check for exact name matches
        query_words = set(query.text.lower().split())
        
        # Function/class name match
        if "function_name" in metadata:
            name = metadata["function_name"].lower()
            if any(word in name for word in query_words):
                score += 0.8
                
        if "class_name" in metadata:
            name = metadata["class_name"].lower()
            if any(word in name for word in query_words):
                score += 0.8
                
        # File name relevance
        if "file_path" in metadata:
            file_name = metadata["file_path"].split('/')[-1].lower()
            if any(word in file_name for word in query_words):
                score += 0.3
                
        # Documentation chunks often very relevant
        if metadata.get("chunk_type") == "documentation":
            score += 0.2
            
        return min(score, 1.0)
        
    def _calculate_recency_score(self, result: SearchResult) -> float:
        """Calculate score based on recency."""
        if "last_modified" not in result.metadata:
            return 0.0
            
        try:
            # Parse timestamp
            if isinstance(result.metadata["last_modified"], str):
                last_modified = datetime.fromisoformat(result.metadata["last_modified"])
            else:
                last_modified = result.metadata["last_modified"]
                
            # Calculate age in days
            age_days = (datetime.now() - last_modified).days
            
            # Decay function - newer is better
            if age_days < 7:
                return 1.0
            elif age_days < 30:
                return 0.8
            elif age_days < 90:
                return 0.5
            elif age_days < 365:
                return 0.3
            else:
                return 0.1
                
        except Exception as e:
            logger.warning(f"Failed to calculate recency score: {e}")
            return 0.0
            
    def _calculate_type_score(self, result: SearchResult) -> float:
        """Calculate score based on chunk type."""
        chunk_type = result.metadata.get("chunk_type", "unknown")
        
        # Prefer certain types
        type_scores = {
            "function": 0.9,
            "method": 0.9,
            "class": 0.8,
            "documentation": 0.7,
            "module": 0.6,
            "import": 0.4,
            "comment": 0.3,
            "block": 0.2,
            "unknown": 0.1
        }
        
        return type_scores.get(chunk_type, 0.1)
        
    def _calculate_length_score(self, result: SearchResult) -> float:
        """Calculate score based on chunk length."""
        length = len(result.text)
        
        # Optimal length range
        if 100 <= length <= 500:
            return 1.0
        elif 50 <= length < 100:
            return 0.8
        elif 500 < length <= 1000:
            return 0.8
        elif length < 50:
            return 0.5  # Too short
        else:
            return 0.6  # Too long
            
    def _calculate_filter_match_score(self, result: SearchResult, filters: Dict[str, Any]) -> float:
        """Calculate score based on filter matches."""
        if not filters:
            return 0.0
            
        matches = 0
        total = len(filters)
        
        for key, value in filters.items():
            if result.metadata.get(key) == value:
                matches += 1
                
        return matches / total if total > 0 else 0.0