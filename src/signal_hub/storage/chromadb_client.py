"""ChromaDB client for vector storage."""

import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from contextlib import asynccontextmanager

from signal_hub.storage.collections import Collection
from signal_hub.storage.models import CollectionMetadata

logger = logging.getLogger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("ChromaDB not installed. Vector storage will not be available.")


class ChromaDBClient:
    """Client for ChromaDB vector database."""
    
    def __init__(
        self,
        path: Optional[Path] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        settings: Optional[Dict[str, Any]] = None,
    ):
        """Initialize ChromaDB client.
        
        Args:
            path: Path for persistent storage (local mode)
            host: Host for client-server mode
            port: Port for client-server mode
            settings: Additional ChromaDB settings
        """
        if not HAS_CHROMADB:
            raise ImportError("ChromaDB is required. Install with: pip install chromadb")
        
        self.path = path
        self.host = host
        self.port = port
        self.settings = settings or {}
        
        self._client = None
        self._collections: Dict[str, Collection] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Connect to ChromaDB."""
        async with self._lock:
            if self._client is not None:
                return
            
            try:
                if self.host and self.port:
                    # Client-server mode
                    logger.info(f"Connecting to ChromaDB at {self.host}:{self.port}")
                    self._client = chromadb.HttpClient(
                        host=self.host,
                        port=self.port,
                        settings=Settings(**self.settings)
                    )
                else:
                    # Local persistent mode
                    if self.path:
                        self.path.mkdir(parents=True, exist_ok=True)
                        persist_directory = str(self.path)
                    else:
                        persist_directory = None
                    
                    logger.info(f"Initializing ChromaDB client (persist_dir: {persist_directory})")
                    
                    # Create settings
                    chroma_settings = Settings(
                        persist_directory=persist_directory,
                        anonymized_telemetry=False,
                        **self.settings
                    )
                    
                    # Create client
                    self._client = chromadb.PersistentClient(
                        path=persist_directory,
                        settings=chroma_settings
                    )
                
                # Test connection
                await self._run_async(self._client.heartbeat)
                logger.info("ChromaDB client connected successfully")
                
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
                self._client = None
                raise
    
    async def disconnect(self) -> None:
        """Disconnect from ChromaDB."""
        async with self._lock:
            if self._client is None:
                return
            
            # Close collections
            self._collections.clear()
            
            # ChromaDB doesn't have explicit disconnect
            self._client = None
            logger.info("ChromaDB client disconnected")
    
    async def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_function: Optional[Any] = None,
    ) -> Collection:
        """Create a new collection.
        
        Args:
            name: Collection name
            metadata: Collection metadata
            embedding_function: Optional embedding function
            
        Returns:
            Collection wrapper
        """
        if not self._client:
            await self.connect()
        
        async with self._lock:
            try:
                # Create collection metadata
                collection_metadata = CollectionMetadata(
                    name=name,
                    metadata=metadata or {}
                )
                
                # Create ChromaDB collection
                chroma_collection = await self._run_async(
                    self._client.create_collection,
                    name=name,
                    metadata=collection_metadata.to_dict(),
                    embedding_function=embedding_function
                )
                
                # Wrap in our Collection class
                collection = Collection(
                    name=name,
                    client=AsyncCollectionWrapper(chroma_collection),
                    metadata=collection_metadata
                )
                
                await collection.initialize()
                self._collections[name] = collection
                
                logger.info(f"Created collection '{name}'")
                return collection
                
            except Exception as e:
                logger.error(f"Failed to create collection '{name}': {e}")
                raise
    
    async def get_collection(self, name: str) -> Optional[Collection]:
        """Get an existing collection.
        
        Args:
            name: Collection name
            
        Returns:
            Collection wrapper or None if not found
        """
        if not self._client:
            await self.connect()
        
        # Check cache
        if name in self._collections:
            return self._collections[name]
        
        async with self._lock:
            try:
                # Get from ChromaDB
                chroma_collection = await self._run_async(
                    self._client.get_collection,
                    name=name
                )
                
                # Extract metadata
                metadata_dict = chroma_collection.metadata or {}
                collection_metadata = CollectionMetadata.from_dict(metadata_dict)
                
                # Wrap in our Collection class
                collection = Collection(
                    name=name,
                    client=AsyncCollectionWrapper(chroma_collection),
                    metadata=collection_metadata
                )
                
                await collection.initialize()
                self._collections[name] = collection
                
                return collection
                
            except ValueError:
                # Collection doesn't exist
                return None
            except Exception as e:
                logger.error(f"Failed to get collection '{name}': {e}")
                raise
    
    async def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_function: Optional[Any] = None,
    ) -> Collection:
        """Get or create a collection.
        
        Args:
            name: Collection name
            metadata: Collection metadata (for creation)
            embedding_function: Optional embedding function
            
        Returns:
            Collection wrapper
        """
        # Try to get existing
        collection = await self.get_collection(name)
        if collection:
            return collection
        
        # Create new
        return await self.create_collection(name, metadata, embedding_function)
    
    async def list_collections(self) -> List[str]:
        """List all collection names.
        
        Returns:
            List of collection names
        """
        if not self._client:
            await self.connect()
        
        try:
            collections = await self._run_async(self._client.list_collections)
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
    
    async def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: Collection name
        """
        if not self._client:
            await self.connect()
        
        async with self._lock:
            try:
                await self._run_async(self._client.delete_collection, name=name)
                
                # Remove from cache
                self._collections.pop(name, None)
                
                logger.info(f"Deleted collection '{name}'")
                
            except Exception as e:
                logger.error(f"Failed to delete collection '{name}': {e}")
                raise
    
    async def _run_async(self, func, *args, **kwargs):
        """Run a synchronous function asynchronously.
        
        Args:
            func: Function to run
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions (if supported)."""
        # ChromaDB doesn't support transactions yet
        # This is a placeholder for future functionality
        yield self
    
    def __repr__(self) -> str:
        """String representation."""
        if self.host and self.port:
            return f"ChromaDBClient(host='{self.host}', port={self.port})"
        else:
            return f"ChromaDBClient(path='{self.path}')"


class AsyncCollectionWrapper:
    """Async wrapper for ChromaDB collection."""
    
    def __init__(self, collection):
        """Initialize wrapper.
        
        Args:
            collection: ChromaDB collection
        """
        self._collection = collection
        self.metadata = collection.metadata
    
    async def add(self, **kwargs):
        """Add documents asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collection.add, **kwargs)
    
    async def query(self, **kwargs):
        """Query asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collection.query, **kwargs)
    
    async def get(self, **kwargs):
        """Get documents asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collection.get, **kwargs)
    
    async def update(self, **kwargs):
        """Update documents asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collection.update, **kwargs)
    
    async def delete(self, **kwargs):
        """Delete documents asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collection.delete, **kwargs)
    
    async def count(self):
        """Count documents asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collection.count)