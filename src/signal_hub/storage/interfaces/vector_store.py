"""Vector store interface for database abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Result from a vector search."""
    
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "score": self.score,
            "text": self.text,
            "metadata": self.metadata,
            "vector": self.vector
        }


class VectorStore(ABC):
    """Abstract base class for vector stores.
    
    This interface allows swapping between different vector databases
    (ChromaDB, pgvector, Pinecone, etc.) without changing application code.
    """
    
    @abstractmethod
    async def add_vectors(
        self,
        vectors: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Add vectors to the store.
        
        Args:
            vectors: List of embedding vectors
            texts: List of text content
            metadata: List of metadata dictionaries
            
        Returns:
            List of IDs for the added vectors
        """
        pass
        
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results ordered by similarity
        """
        pass
        
    @abstractmethod
    async def get_by_ids(self, ids: List[str]) -> List[SearchResult]:
        """Get vectors by their IDs.
        
        Args:
            ids: List of vector IDs
            
        Returns:
            List of search results
        """
        pass
        
    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all vectors from the store.
        
        Returns:
            True if successful
        """
        pass
        
    @abstractmethod
    async def count(self) -> int:
        """Get the total number of vectors.
        
        Returns:
            Number of vectors in the store
        """
        pass
        
    async def update_metadata(
        self,
        id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update metadata for a vector.
        
        Args:
            id: Vector ID
            metadata: New metadata dictionary
            
        Returns:
            True if successful
            
        Note: This is optional - not all stores may support it
        """
        raise NotImplementedError("This store does not support metadata updates")
        
    async def create_index(
        self,
        index_type: str = "hnsw",
        **kwargs
    ) -> bool:
        """Create an index for efficient search.
        
        Args:
            index_type: Type of index to create
            **kwargs: Additional index parameters
            
        Returns:
            True if successful
            
        Note: This is optional - not all stores may support it
        """
        return True  # Default no-op
        
    async def health_check(self) -> bool:
        """Check if the store is healthy and accessible.
        
        Returns:
            True if healthy
        """
        try:
            await self.count()
            return True
        except Exception:
            return False