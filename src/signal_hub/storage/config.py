"""Storage configuration models."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VectorStoreConfig(BaseModel):
    """Configuration for vector store."""
    
    type: str = Field(default="chromadb", description="Type of vector store")
    path: str = Field(default="./chroma_data", description="Path for data storage")
    collection_name: str = Field(default="signal_hub", description="Collection/index name")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")
    
    class Config:
        """Pydantic configuration."""
        
        extra = "allow"


class CacheStoreConfig(BaseModel):
    """Configuration for cache store."""
    
    type: str = Field(default="sqlite", description="Type of cache store")
    path: str = Field(default="./cache.db", description="Path for cache storage")
    ttl: Optional[int] = Field(default=3600, description="Default TTL in seconds")
    max_size: Optional[int] = Field(default=None, description="Maximum cache size")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")
    
    class Config:
        """Pydantic configuration."""
        
        extra = "allow"


class StorageConfig(BaseModel):
    """Complete storage configuration."""
    
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    cache_store: CacheStoreConfig = Field(default_factory=CacheStoreConfig)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "StorageConfig":
        """Create from dictionary configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            StorageConfig instance
        """
        return cls(
            vector_store=VectorStoreConfig(**config.get("vector_store", {})),
            cache_store=CacheStoreConfig(**config.get("cache_store", {}))
        )
        
    def to_factory_config(self) -> Dict[str, Dict[str, Any]]:
        """Convert to factory configuration format.
        
        Returns:
            Dictionary suitable for StoreFactory
        """
        return {
            "vector_store": self.vector_store.model_dump(),
            "cache_store": self.cache_store.model_dump()
        }