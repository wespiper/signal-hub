"""In-memory adapters for testing."""

import logging
from typing import Any, Dict, List, Optional

from signal_hub.storage.interfaces import CacheStore, SearchResult, VectorStore

logger = logging.getLogger(__name__)


class MemoryVectorStore(VectorStore):
    """In-memory implementation of VectorStore for testing."""
    
    def __init__(self):
        """Initialize memory vector store."""
        self.data: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        
    async def add_vectors(
        self,
        vectors: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Add vectors to memory store."""
        ids = []
        for vector, text, meta in zip(vectors, texts, metadata):
            id_ = f"mem_{self.next_id}"
            self.data[id_] = {
                "vector": vector,
                "text": text,
                "metadata": meta
            }
            ids.append(id_)
            self.next_id += 1
        return ids
        
    async def search(
        self,
        query_vector: List[float],
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors (simple implementation)."""
        results = []
        
        # Simple cosine similarity
        for id_, item in self.data.items():
            # Apply filters
            if filter_dict:
                match = all(
                    item["metadata"].get(key) == value
                    for key, value in filter_dict.items()
                )
                if not match:
                    continue
                    
            # Calculate similarity (simplified)
            vector = item["vector"]
            score = sum(a * b for a, b in zip(query_vector, vector))
            
            result = SearchResult(
                id=id_,
                score=score,
                text=item["text"],
                metadata=item["metadata"],
                vector=vector
            )
            results.append(result)
            
        # Sort by score and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
        
    async def get_by_ids(self, ids: List[str]) -> List[SearchResult]:
        """Get vectors by IDs."""
        results = []
        for id_ in ids:
            if id_ in self.data:
                item = self.data[id_]
                result = SearchResult(
                    id=id_,
                    score=1.0,
                    text=item["text"],
                    metadata=item["metadata"],
                    vector=item["vector"]
                )
                results.append(result)
        return results
        
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs."""
        for id_ in ids:
            self.data.pop(id_, None)
        return True
        
    async def clear(self) -> bool:
        """Clear all vectors."""
        self.data.clear()
        self.next_id = 1
        return True
        
    async def count(self) -> int:
        """Get vector count."""
        return len(self.data)


class MemoryCacheStore(CacheStore):
    """In-memory implementation of CacheStore for testing."""
    
    def __init__(self):
        """Initialize memory cache store."""
        self.cache: Dict[str, Any] = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache.get(key)
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        self.cache[key] = value
        return True
        
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
        
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.cache
        
    async def clear(self) -> bool:
        """Clear cache."""
        self.cache.clear()
        return True
        
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values."""
        return {k: self.cache.get(k) for k in keys if k in self.cache}
        
    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values."""
        self.cache.update(items)
        return True