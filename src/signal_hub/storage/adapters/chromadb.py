"""ChromaDB adapter for VectorStore interface."""

import logging
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from signal_hub.storage.interfaces import SearchResult, VectorStore

logger = logging.getLogger(__name__)


class ChromaDBAdapter(VectorStore):
    """ChromaDB implementation of VectorStore interface."""
    
    def __init__(
        self,
        path: str = "./chroma_data",
        collection_name: str = "signal_hub",
        **kwargs
    ):
        """Initialize ChromaDB adapter.
        
        Args:
            path: Path to ChromaDB data directory
            collection_name: Name of the collection to use
            **kwargs: Additional ChromaDB settings
        """
        self.path = path
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        settings = Settings(
            persist_directory=path,
            anonymized_telemetry=False,
            **kwargs
        )
        self.client = chromadb.Client(settings)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
    async def add_vectors(
        self,
        vectors: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Add vectors to ChromaDB.
        
        Args:
            vectors: List of embedding vectors
            texts: List of text content
            metadata: List of metadata dictionaries
            
        Returns:
            List of IDs for the added vectors
        """
        # Generate IDs
        ids = [f"doc_{i}_{hash(texts[i])}" for i in range(len(texts))]
        
        # Add to collection
        self.collection.add(
            embeddings=vectors,
            documents=texts,
            metadatas=metadata,
            ids=ids
        )
        
        return ids
        
    async def search(
        self,
        query_vector: List[float],
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors in ChromaDB.
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results ordered by similarity
        """
        # Build where clause for filters
        where = filter_dict if filter_dict else None
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances", "embeddings"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        for i in range(len(results["ids"][0])):
            result = SearchResult(
                id=results["ids"][0][i],
                score=1.0 - results["distances"][0][i],  # Convert distance to similarity
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i] or {},
                vector=results["embeddings"][0][i] if results.get("embeddings") else None
            )
            search_results.append(result)
            
        return search_results
        
    async def get_by_ids(self, ids: List[str]) -> List[SearchResult]:
        """Get vectors by their IDs from ChromaDB.
        
        Args:
            ids: List of vector IDs
            
        Returns:
            List of search results
        """
        # Get from collection
        results = self.collection.get(
            ids=ids,
            include=["documents", "metadatas", "embeddings"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        for i in range(len(results["ids"])):
            result = SearchResult(
                id=results["ids"][i],
                score=1.0,  # Direct retrieval has perfect score
                text=results["documents"][i],
                metadata=results["metadatas"][i] or {},
                vector=results["embeddings"][i] if results.get("embeddings") else None
            )
            search_results.append(result)
            
        return search_results
        
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs from ChromaDB.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
            
    async def clear(self) -> bool:
        """Clear all vectors from ChromaDB collection.
        
        Returns:
            True if successful
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
            
    async def count(self) -> int:
        """Get the total number of vectors in ChromaDB.
        
        Returns:
            Number of vectors in the collection
        """
        return self.collection.count()
        
    async def update_metadata(
        self,
        id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update metadata for a vector in ChromaDB.
        
        Args:
            id: Vector ID
            metadata: New metadata dictionary
            
        Returns:
            True if successful
        """
        try:
            self.collection.update(
                ids=[id],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False
            
    async def health_check(self) -> bool:
        """Check if ChromaDB is healthy and accessible.
        
        Returns:
            True if healthy
        """
        try:
            # Try to count documents
            count = await self.count()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False