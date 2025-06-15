"""Factory for creating storage instances."""

import logging
from typing import Any, Dict

from signal_hub.storage.interfaces import CacheStore, VectorStore

logger = logging.getLogger(__name__)


class StoreFactory:
    """Factory for creating store instances based on configuration."""
    
    @staticmethod
    def create_vector_store(config: Dict[str, Any]) -> VectorStore:
        """Create a vector store instance based on configuration.
        
        Args:
            config: Store configuration dictionary
            
        Returns:
            VectorStore instance
            
        Raises:
            ValueError: If store type is not supported
        """
        store_type = config.get("type", "chromadb").lower()
        
        if store_type == "chromadb":
            from signal_hub.storage.adapters.chromadb import ChromaDBAdapter
            
            return ChromaDBAdapter(
                path=config.get("path", "./chroma_data"),
                collection_name=config.get("collection_name", "signal_hub"),
                **config.get("settings", {})
            )
            
        elif store_type == "pgvector":
            # Placeholder for future implementation
            raise NotImplementedError(
                "PostgreSQL with pgvector support is planned for production deployments. "
                "Please use ChromaDB for development."
            )
            
        elif store_type == "memory":
            # For testing purposes
            from signal_hub.storage.adapters.memory import MemoryVectorStore
            return MemoryVectorStore()
            
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")
            
    @staticmethod
    def create_cache_store(config: Dict[str, Any]) -> CacheStore:
        """Create a cache store instance based on configuration.
        
        Args:
            config: Store configuration dictionary
            
        Returns:
            CacheStore instance
            
        Raises:
            ValueError: If store type is not supported
        """
        store_type = config.get("type", "sqlite").lower()
        
        if store_type == "sqlite":
            from signal_hub.storage.adapters.sqlite_cache import SQLiteCacheAdapter
            
            return SQLiteCacheAdapter(
                db_path=config.get("path", "./cache.db")
            )
            
        elif store_type == "redis":
            # Placeholder for future implementation
            raise NotImplementedError(
                "Redis support is planned for production deployments. "
                "Please use SQLite for development."
            )
            
        elif store_type == "memory":
            # For testing purposes
            from signal_hub.storage.adapters.memory import MemoryCacheStore
            return MemoryCacheStore()
            
        else:
            raise ValueError(f"Unsupported cache store type: {store_type}")
            
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Create all stores from a configuration dictionary.
        
        Args:
            config: Full configuration with 'vector_store' and 'cache_store' sections
            
        Returns:
            Dictionary with 'vector_store' and 'cache_store' instances
        """
        stores = {}
        
        # Create vector store
        if "vector_store" in config:
            stores["vector_store"] = StoreFactory.create_vector_store(
                config["vector_store"]
            )
            logger.info(f"Created vector store: {config['vector_store']['type']}")
            
        # Create cache store
        if "cache_store" in config:
            stores["cache_store"] = StoreFactory.create_cache_store(
                config["cache_store"]
            )
            logger.info(f"Created cache store: {config['cache_store']['type']}")
            
        return stores