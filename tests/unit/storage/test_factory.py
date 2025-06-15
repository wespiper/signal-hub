"""Tests for storage factory."""

import pytest
from pathlib import Path

from signal_hub.storage.factory import StoreFactory
from signal_hub.storage.interfaces import VectorStore, CacheStore


class TestStoreFactory:
    """Test store factory functionality."""
    
    def test_create_chromadb_vector_store(self, tmp_path):
        """Test creating ChromaDB vector store."""
        config = {
            "type": "chromadb",
            "path": str(tmp_path / "chroma"),
            "collection_name": "test_collection"
        }
        
        store = StoreFactory.create_vector_store(config)
        assert isinstance(store, VectorStore)
        
    def test_create_sqlite_cache_store(self, tmp_path):
        """Test creating SQLite cache store."""
        config = {
            "type": "sqlite",
            "path": str(tmp_path / "cache.db")
        }
        
        store = StoreFactory.create_cache_store(config)
        assert isinstance(store, CacheStore)
        
    def test_create_memory_stores(self):
        """Test creating memory stores for testing."""
        # Memory vector store
        vector_config = {"type": "memory"}
        vector_store = StoreFactory.create_vector_store(vector_config)
        assert isinstance(vector_store, VectorStore)
        
        # Memory cache store
        cache_config = {"type": "memory"}
        cache_store = StoreFactory.create_cache_store(cache_config)
        assert isinstance(cache_store, CacheStore)
        
    def test_unsupported_vector_store_type(self):
        """Test error for unsupported vector store type."""
        config = {"type": "unsupported"}
        
        with pytest.raises(ValueError, match="Unsupported vector store type"):
            StoreFactory.create_vector_store(config)
            
    def test_unsupported_cache_store_type(self):
        """Test error for unsupported cache store type."""
        config = {"type": "unsupported"}
        
        with pytest.raises(ValueError, match="Unsupported cache store type"):
            StoreFactory.create_cache_store(config)
            
    def test_pgvector_not_implemented(self):
        """Test pgvector raises NotImplementedError."""
        config = {"type": "pgvector"}
        
        with pytest.raises(NotImplementedError, match="pgvector support is planned"):
            StoreFactory.create_vector_store(config)
            
    def test_redis_not_implemented(self):
        """Test Redis raises NotImplementedError."""
        config = {"type": "redis"}
        
        with pytest.raises(NotImplementedError, match="Redis support is planned"):
            StoreFactory.create_cache_store(config)
            
    def test_create_from_config(self, tmp_path):
        """Test creating all stores from config."""
        config = {
            "vector_store": {
                "type": "chromadb",
                "path": str(tmp_path / "chroma")
            },
            "cache_store": {
                "type": "sqlite",
                "path": str(tmp_path / "cache.db")
            }
        }
        
        stores = StoreFactory.create_from_config(config)
        
        assert "vector_store" in stores
        assert "cache_store" in stores
        assert isinstance(stores["vector_store"], VectorStore)
        assert isinstance(stores["cache_store"], CacheStore)
        
    def test_create_from_partial_config(self, tmp_path):
        """Test creating stores from partial config."""
        # Only vector store
        config = {
            "vector_store": {
                "type": "memory"
            }
        }
        
        stores = StoreFactory.create_from_config(config)
        assert "vector_store" in stores
        assert "cache_store" not in stores
        
    def test_default_values(self, tmp_path):
        """Test default values are used when not specified."""
        # Minimal config
        vector_config = {"type": "chromadb"}
        vector_store = StoreFactory.create_vector_store(vector_config)
        assert vector_store is not None
        
        cache_config = {"type": "sqlite"}
        cache_store = StoreFactory.create_cache_store(cache_config)
        assert cache_store is not None