"""Collection management for vector storage."""

from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime

from signal_hub.storage.models import Document, QueryResult, CollectionMetadata, QueryFilter

logger = logging.getLogger(__name__)


class Collection:
    """Wrapper for a vector database collection."""
    
    def __init__(self, name: str, client: Any, metadata: Optional[CollectionMetadata] = None):
        """Initialize collection wrapper.
        
        Args:
            name: Collection name
            client: Database client
            metadata: Collection metadata
        """
        self.name = name
        self._client = client
        self._collection = None
        self.metadata = metadata or CollectionMetadata(name=name, created_at=datetime.now())
    
    async def initialize(self) -> None:
        """Initialize the collection."""
        try:
            # Get or create collection
            self._collection = await self._client.get_or_create_collection(
                name=self.name,
                metadata=self.metadata.to_dict()
            )
            
            # Update metadata
            if hasattr(self._collection, "metadata"):
                stored_metadata = CollectionMetadata.from_dict(self._collection.metadata)
                self.metadata = stored_metadata
                
            logger.info(f"Collection '{self.name}' initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection '{self.name}': {e}")
            raise
    
    async def add(
        self,
        documents: Union[Document, List[Document]],
        batch_size: int = 100
    ) -> None:
        """Add documents to the collection.
        
        Args:
            documents: Document or list of documents
            batch_size: Batch size for adding
        """
        if not self._collection:
            await self.initialize()
        
        # Ensure list
        if isinstance(documents, Document):
            documents = [documents]
        
        if not documents:
            return
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Prepare data for ChromaDB
                ids = [doc.id for doc in batch]
                embeddings = [doc.embedding for doc in batch]
                documents_text = [doc.content for doc in batch]
                metadatas = [doc.metadata for doc in batch]
                
                # Add to collection
                await self._collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents_text,
                    metadatas=metadatas
                )
                
                logger.debug(f"Added {len(batch)} documents to collection '{self.name}'")
                
            except Exception as e:
                logger.error(f"Failed to add batch to collection: {e}")
                raise
        
        # Update document count
        self.metadata.document_count += len(documents)
        self.metadata.updated_at = datetime.now()
    
    async def query(
        self,
        query_embeddings: Union[List[float], List[List[float]]],
        n_results: int = 10,
        filter: Optional[QueryFilter] = None,
        include_content: bool = True,
        include_metadata: bool = True,
    ) -> List[QueryResult]:
        """Query the collection for similar vectors.
        
        Args:
            query_embeddings: Query embedding(s)
            n_results: Number of results to return
            filter: Optional query filter
            include_content: Include document content
            include_metadata: Include metadata
            
        Returns:
            List of query results
        """
        if not self._collection:
            await self.initialize()
        
        # Ensure 2D array
        if query_embeddings and isinstance(query_embeddings[0], (int, float)):
            query_embeddings = [query_embeddings]
        
        # Prepare include parameter
        include = []
        if include_content:
            include.append("documents")
        if include_metadata:
            include.append("metadatas")
        include.append("distances")  # Always include distances
        
        # Build query parameters
        query_params = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "include": include
        }
        
        # Add filter if provided
        if filter:
            query_params.update(filter.to_chroma_format())
        
        try:
            # Execute query
            results = await self._collection.query(**query_params)
            
            # Parse results
            query_results = []
            
            # Results are grouped by query
            for q_idx in range(len(query_embeddings)):
                ids = results.get("ids", [[]])[q_idx]
                distances = results.get("distances", [[]])[q_idx]
                documents = results.get("documents", [[]])[q_idx] if include_content else [None] * len(ids)
                metadatas = results.get("metadatas", [[]])[q_idx] if include_metadata else [{}] * len(ids)
                
                for i in range(len(ids)):
                    query_results.append(QueryResult(
                        id=ids[i],
                        content=documents[i] or "",
                        metadata=metadatas[i] or {},
                        distance=distances[i]
                    ))
            
            return query_results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    async def get(
        self,
        ids: Union[str, List[str]],
        include_content: bool = True,
        include_metadata: bool = True
    ) -> List[Document]:
        """Get documents by ID.
        
        Args:
            ids: Document ID(s)
            include_content: Include document content
            include_metadata: Include metadata
            
        Returns:
            List of documents
        """
        if not self._collection:
            await self.initialize()
        
        # Ensure list
        if isinstance(ids, str):
            ids = [ids]
        
        # Prepare include parameter
        include = ["embeddings"]  # Always include embeddings
        if include_content:
            include.append("documents")
        if include_metadata:
            include.append("metadatas")
        
        try:
            # Get documents
            results = await self._collection.get(
                ids=ids,
                include=include
            )
            
            # Parse results
            documents = []
            
            result_ids = results.get("ids", [])
            embeddings = results.get("embeddings", [])
            contents = results.get("documents", []) if include_content else [None] * len(result_ids)
            metadatas = results.get("metadatas", []) if include_metadata else [{}] * len(result_ids)
            
            for i in range(len(result_ids)):
                documents.append(Document(
                    id=result_ids[i],
                    content=contents[i] or "",
                    embedding=embeddings[i],
                    metadata=metadatas[i] or {}
                ))
            
            return documents
            
        except Exception as e:
            logger.error(f"Get documents failed: {e}")
            raise
    
    async def update(
        self,
        ids: Union[str, List[str]],
        embeddings: Optional[Union[List[float], List[List[float]]]] = None,
        metadatas: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        documents: Optional[Union[str, List[str]]] = None
    ) -> None:
        """Update documents in the collection.
        
        Args:
            ids: Document ID(s) to update
            embeddings: New embeddings
            metadatas: New metadata
            documents: New document content
        """
        if not self._collection:
            await self.initialize()
        
        # Ensure lists
        if isinstance(ids, str):
            ids = [ids]
        
        update_params = {"ids": ids}
        
        if embeddings is not None:
            if embeddings and isinstance(embeddings[0], (int, float)):
                embeddings = [embeddings]
            update_params["embeddings"] = embeddings
        
        if metadatas is not None:
            if isinstance(metadatas, dict):
                metadatas = [metadatas]
            update_params["metadatas"] = metadatas
        
        if documents is not None:
            if isinstance(documents, str):
                documents = [documents]
            update_params["documents"] = documents
        
        try:
            await self._collection.update(**update_params)
            self.metadata.updated_at = datetime.now()
            logger.debug(f"Updated {len(ids)} documents in collection '{self.name}'")
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
    
    async def delete(
        self,
        ids: Optional[Union[str, List[str]]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> None:
        """Delete documents from the collection.
        
        Args:
            ids: Document ID(s) to delete
            where: Filter for deletion
        """
        if not self._collection:
            await self.initialize()
        
        if ids is None and where is None:
            raise ValueError("Either ids or where must be provided")
        
        delete_params = {}
        
        if ids is not None:
            if isinstance(ids, str):
                ids = [ids]
            delete_params["ids"] = ids
        
        if where is not None:
            delete_params["where"] = where
        
        try:
            await self._collection.delete(**delete_params)
            
            # Update document count (approximate)
            if ids:
                self.metadata.document_count -= len(ids)
            
            self.metadata.updated_at = datetime.now()
            logger.debug(f"Deleted documents from collection '{self.name}'")
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    async def count(self) -> int:
        """Get the number of documents in the collection.
        
        Returns:
            Document count
        """
        if not self._collection:
            await self.initialize()
        
        try:
            return await self._collection.count()
        except Exception as e:
            logger.error(f"Count failed: {e}")
            # Return cached count as fallback
            return self.metadata.document_count
    
    async def clear(self) -> None:
        """Clear all documents from the collection."""
        if not self._collection:
            await self.initialize()
        
        try:
            # ChromaDB doesn't have a clear method, so delete all
            # This is inefficient for large collections
            all_ids = await self._collection.get(include=[])
            if all_ids["ids"]:
                await self._collection.delete(ids=all_ids["ids"])
            
            self.metadata.document_count = 0
            self.metadata.updated_at = datetime.now()
            logger.info(f"Cleared collection '{self.name}'")
            
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            raise