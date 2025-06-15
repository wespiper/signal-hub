"""Tests for storage interfaces."""

import pytest
from typing import List, Dict, Any
import numpy as np

from signal_hub.storage.interfaces import VectorStore, CacheStore, SearchResult


class TestVectorStoreInterface:
    """Test VectorStore interface compliance."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store for testing."""
        
        class MockVectorStore(VectorStore):
            """Mock implementation of VectorStore."""
            
            def __init__(self):
                self.data = {}
                self.next_id = 1
                
            async def add_vectors(
                self,
                vectors: List[List[float]],
                texts: List[str],
                metadata: List[Dict[str, Any]]
            ) -> List[str]:
                """Add vectors to store."""
                ids = []
                for i, (vector, text, meta) in enumerate(zip(vectors, texts, metadata)):
                    id_ = f"vec_{self.next_id}"
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
                filter_dict: Dict[str, Any] = None
            ) -> List[SearchResult]:
                """Search for similar vectors."""
                # Simple mock search - return first k items
                results = []
                for id_, item in list(self.data.items())[:k]:
                    # Apply filters if provided
                    if filter_dict:
                        match = all(
                            item["metadata"].get(key) == value
                            for key, value in filter_dict.items()
                        )
                        if not match:
                            continue
                            
                    result = SearchResult(
                        id=id_,
                        score=0.9,  # Mock score
                        text=item["text"],
                        metadata=item["metadata"]
                    )
                    results.append(result)
                return results
                
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
                            metadata=item["metadata"]
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
                """Get total vector count."""
                return len(self.data)
                
        return MockVectorStore()
        
    @pytest.mark.asyncio
    async def test_vector_store_add_and_search(self, mock_vector_store):
        """Test adding and searching vectors."""
        # Add vectors
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        texts = ["First document", "Second document"]
        metadata = [{"type": "code"}, {"type": "docs"}]
        
        ids = await mock_vector_store.add_vectors(vectors, texts, metadata)
        assert len(ids) == 2
        
        # Search vectors
        query = [0.1, 0.2, 0.3]
        results = await mock_vector_store.search(query, k=2)
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        
    @pytest.mark.asyncio
    async def test_vector_store_filter_search(self, mock_vector_store):
        """Test searching with filters."""
        # Add vectors with metadata
        vectors = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        texts = ["Python code", "JavaScript code", "Documentation"]
        metadata = [
            {"language": "python", "type": "code"},
            {"language": "javascript", "type": "code"},
            {"language": "markdown", "type": "docs"}
        ]
        
        await mock_vector_store.add_vectors(vectors, texts, metadata)
        
        # Search with filter
        query = [0.2, 0.3]
        results = await mock_vector_store.search(
            query, k=10, filter_dict={"type": "code"}
        )
        
        # Should only return code items
        assert all(r.metadata["type"] == "code" for r in results)
        
    @pytest.mark.asyncio
    async def test_vector_store_get_by_ids(self, mock_vector_store):
        """Test getting vectors by IDs."""
        # Add vectors
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["Text 1", "Text 2"]
        metadata = [{}, {}]
        
        ids = await mock_vector_store.add_vectors(vectors, texts, metadata)
        
        # Get by IDs
        results = await mock_vector_store.get_by_ids([ids[0]])
        assert len(results) == 1
        assert results[0].id == ids[0]
        assert results[0].text == "Text 1"
        
    @pytest.mark.asyncio
    async def test_vector_store_delete(self, mock_vector_store):
        """Test deleting vectors."""
        # Add vectors
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["Text 1", "Text 2"]
        metadata = [{}, {}]
        
        ids = await mock_vector_store.add_vectors(vectors, texts, metadata)
        initial_count = await mock_vector_store.count()
        
        # Delete one vector
        await mock_vector_store.delete([ids[0]])
        
        # Verify deletion
        final_count = await mock_vector_store.count()
        assert final_count == initial_count - 1
        
        results = await mock_vector_store.get_by_ids([ids[0]])
        assert len(results) == 0
        
    @pytest.mark.asyncio
    async def test_vector_store_clear(self, mock_vector_store):
        """Test clearing all vectors."""
        # Add vectors
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["Text 1", "Text 2"]
        metadata = [{}, {}]
        
        await mock_vector_store.add_vectors(vectors, texts, metadata)
        
        # Clear store
        await mock_vector_store.clear()
        
        # Verify empty
        count = await mock_vector_store.count()
        assert count == 0


class TestCacheStoreInterface:
    """Test CacheStore interface compliance."""
    
    @pytest.fixture
    def mock_cache_store(self):
        """Create a mock cache store for testing."""
        
        class MockCacheStore(CacheStore):
            """Mock implementation of CacheStore."""
            
            def __init__(self):
                self.cache = {}
                
            async def get(self, key: str) -> Any:
                """Get value from cache."""
                return self.cache.get(key)
                
            async def set(self, key: str, value: Any, ttl: int = None) -> bool:
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
                """Clear all cache entries."""
                self.cache.clear()
                return True
                
            async def get_many(self, keys: List[str]) -> Dict[str, Any]:
                """Get multiple values."""
                return {k: self.cache.get(k) for k in keys if k in self.cache}
                
            async def set_many(self, items: Dict[str, Any], ttl: int = None) -> bool:
                """Set multiple values."""
                self.cache.update(items)
                return True
                
        return MockCacheStore()
        
    @pytest.mark.asyncio
    async def test_cache_store_basic_operations(self, mock_cache_store):
        """Test basic cache operations."""
        # Set value
        await mock_cache_store.set("key1", "value1")
        
        # Get value
        value = await mock_cache_store.get("key1")
        assert value == "value1"
        
        # Check existence
        exists = await mock_cache_store.exists("key1")
        assert exists is True
        
        # Delete value
        deleted = await mock_cache_store.delete("key1")
        assert deleted is True
        
        # Verify deletion
        value = await mock_cache_store.get("key1")
        assert value is None
        
    @pytest.mark.asyncio
    async def test_cache_store_batch_operations(self, mock_cache_store):
        """Test batch cache operations."""
        # Set multiple values
        items = {"key1": "value1", "key2": "value2", "key3": "value3"}
        await mock_cache_store.set_many(items)
        
        # Get multiple values
        values = await mock_cache_store.get_many(["key1", "key2", "key4"])
        assert values == {"key1": "value1", "key2": "value2"}
        
    @pytest.mark.asyncio
    async def test_cache_store_clear(self, mock_cache_store):
        """Test clearing cache."""
        # Add items
        await mock_cache_store.set("key1", "value1")
        await mock_cache_store.set("key2", "value2")
        
        # Clear cache
        await mock_cache_store.clear()
        
        # Verify empty
        exists1 = await mock_cache_store.exists("key1")
        exists2 = await mock_cache_store.exists("key2")
        assert exists1 is False
        assert exists2 is False
        
    @pytest.mark.asyncio
    async def test_cache_store_complex_values(self, mock_cache_store):
        """Test storing complex values."""
        # Store different types
        await mock_cache_store.set("dict", {"a": 1, "b": 2})
        await mock_cache_store.set("list", [1, 2, 3])
        await mock_cache_store.set("nested", {"data": [{"id": 1}]})
        
        # Retrieve and verify
        dict_val = await mock_cache_store.get("dict")
        assert dict_val == {"a": 1, "b": 2}
        
        list_val = await mock_cache_store.get("list")
        assert list_val == [1, 2, 3]
        
        nested_val = await mock_cache_store.get("nested")
        assert nested_val == {"data": [{"id": 1}]}