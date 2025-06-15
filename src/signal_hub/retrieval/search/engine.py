"""Semantic search engine implementation."""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from signal_hub.retrieval.search.models import (
    SearchQuery,
    SearchResult,
    SearchConfig,
    SearchMode
)
from signal_hub.retrieval.search.ranking import ResultRanker
from signal_hub.retrieval.search.filters import MetadataFilter
from signal_hub.storage.interfaces import VectorStore
from signal_hub.indexing.embeddings import EmbeddingService
from signal_hub.storage.interfaces import CacheStore

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Main search engine for semantic code search."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        config: Optional[SearchConfig] = None,
        cache_store: Optional[CacheStore] = None,
        metadata_store: Optional[Any] = None
    ):
        """Initialize search engine.
        
        Args:
            vector_store: Vector database for similarity search
            embedding_service: Service for generating embeddings
            config: Search configuration
            cache_store: Optional cache for results
            metadata_store: Optional metadata store for enhanced filtering
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.config = config or SearchConfig()
        self.cache_store = cache_store
        self.metadata_store = metadata_store
        self.ranker = ResultRanker(config)
        self.filter = MetadataFilter()
        
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        # Check cache if enabled
        if self.config.enable_caching and self.cache_store:
            cache_key = self._get_cache_key(query)
            cached = await self.cache_store.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for query: {query.text}")
                return [SearchResult(**r) for r in cached]
                
        # Execute search based on mode
        if query.mode == SearchMode.SEMANTIC:
            results = await self._semantic_search(query)
        elif query.mode == SearchMode.KEYWORD:
            results = await self._keyword_search(query)
        elif query.mode == SearchMode.HYBRID:
            results = await self._hybrid_search(query)
        else:
            raise ValueError(f"Unknown search mode: {query.mode}")
            
        # Apply post-processing
        results = self._apply_filters(results, query)
        results = self._remove_duplicates(results)
        
        # Rerank if configured
        if self.config.rerank_results:
            results = self.ranker.rerank(results, query)
            
        # Limit results
        results = results[:query.limit]
        
        # Cache results if enabled
        if self.config.enable_caching and self.cache_store:
            cache_data = [r.to_dict() for r in results]
            await self.cache_store.set(cache_key, cache_data, ttl=self.config.cache_ttl)
            
        return results
        
    async def batch_search(self, queries: List[SearchQuery]) -> List[List[SearchResult]]:
        """Perform multiple searches in batch.
        
        Args:
            queries: List of search queries
            
        Returns:
            List of result lists
        """
        tasks = [self.search(query) for query in queries]
        return await asyncio.gather(*tasks)
        
    async def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform pure semantic search."""
        # Generate query embedding
        embedding_result = await self.embedding_service.generate_embeddings([query.text])
        query_embedding = embedding_result.embeddings[0]
        
        # Build filter dict from query
        filter_dict = self._build_filter_dict(query)
        
        # Search vector store
        vector_results = await self.vector_store.search(
            query_vector=query_embedding,
            k=min(query.limit * 3, self.config.max_results),  # Get extra for filtering
            filter_dict=filter_dict
        )
        
        # Convert to search results
        results = []
        for vr in vector_results:
            # Skip if below threshold
            if vr.score < self.config.similarity_threshold:
                continue
                
            result = SearchResult(
                id=vr.id,
                text=vr.text,
                score=vr.score,
                metadata=vr.metadata,
                chunk_id=vr.id
            )
            results.append(result)
            
        return results
        
    async def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword-based search."""
        # Extract keywords from query
        keywords = self._extract_keywords(query.text)
        
        if not keywords:
            return []
            
        # For now, use semantic search with keyword boosting
        # In production, this would use a dedicated keyword index
        results = await self._semantic_search(query)
        
        # Boost results containing keywords
        for result in results:
            keyword_score = self._calculate_keyword_score(result.text, keywords)
            result.score = result.score * (1 - self.config.keyword_weight) + keyword_score * self.config.keyword_weight
            
        # Re-sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results
        
    async def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid semantic + keyword search."""
        # Get both types of results
        semantic_task = self._semantic_search(query)
        keyword_task = self._keyword_search(query)
        
        semantic_results, keyword_results = await asyncio.gather(
            semantic_task, keyword_task
        )
        
        # Merge results
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            result_map[result.id] = result
            
        # Merge keyword results
        for result in keyword_results:
            if result.id in result_map:
                # Average scores
                existing = result_map[result.id]
                existing.score = (existing.score + result.score) / 2
            else:
                result_map[result.id] = result
                
        # Convert back to list
        results = list(result_map.values())
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results
        
    def _build_filter_dict(self, query: SearchQuery) -> Dict[str, Any]:
        """Build filter dictionary from query."""
        filters = query.filters.copy()
        
        # Add language filter
        if query.language_filter:
            filters["language"] = query.language_filter
            
        # Add file pattern filter
        if query.file_pattern:
            filters["file_pattern"] = query.file_pattern
            
        return filters
        
    def _apply_filters(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Apply additional filters to results."""
        filtered = []
        
        for result in results:
            # Apply metadata filters
            if not self.filter.matches(result.metadata, query.filters):
                continue
                
            # Apply file pattern filter
            if query.file_pattern:
                file_path = result.metadata.get("file_path", "")
                if not self._matches_pattern(file_path, query.file_pattern):
                    continue
                    
            filtered.append(result)
            
        return filtered
        
    def _remove_duplicates(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate or highly overlapping results."""
        if not results:
            return results
            
        unique_results = []
        seen_content = set()
        
        for result in results:
            # Create content signature
            content_sig = self._get_content_signature(result.text)
            
            # Check if we've seen similar content
            if content_sig not in seen_content:
                unique_results.append(result)
                seen_content.add(content_sig)
            else:
                # Apply overlap penalty to score
                result.score *= (1 - self.config.chunk_overlap_penalty)
                
                # Still add if score is high enough
                if result.score >= self.config.similarity_threshold:
                    unique_results.append(result)
                    
        return unique_results
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from query text."""
        # Simple keyword extraction
        # Remove common words and punctuation
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words (simplified)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
        
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword match score."""
        if not keywords:
            return 0.0
            
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        
        return matches / len(keywords)
        
    def _get_content_signature(self, text: str) -> str:
        """Get a signature for content to detect duplicates."""
        # Use first 100 chars and last 100 chars
        if len(text) <= 200:
            return text
            
        return text[:100] + "..." + text[-100:]
        
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches pattern."""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)
        
    def _get_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for query."""
        import hashlib
        import json
        
        # Create stable string representation
        query_str = json.dumps(query.to_dict(), sort_keys=True)
        
        # Hash it
        return f"search:{hashlib.md5(query_str.encode()).hexdigest()}"