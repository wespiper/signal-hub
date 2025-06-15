"""Tests for ChromaDB adapter."""

import pytest
import numpy as np
from pathlib import Path

from signal_hub.storage.adapters.chromadb import ChromaDBAdapter
from signal_hub.storage.interfaces import SearchResult


class TestChromaDBAdapter:
    """Test ChromaDB adapter functionality."""
    
    @pytest.fixture
    async def adapter(self, tmp_path):
        """Create ChromaDB adapter for testing."""
        adapter = ChromaDBAdapter(
            path=str(tmp_path / "chroma_test"),
            collection_name="test_collection"
        )
        yield adapter
        # Cleanup
        await adapter.clear()
        
    @pytest.mark.asyncio
    async def test_add_and_search_vectors(self, adapter):
        """Test adding and searching vectors."""
        # Prepare test data
        vectors = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 0.1, 0.2, 0.3]
        ]
        texts = [
            "First document about Python",
            "Second document about JavaScript",
            "Third document about Rust"
        ]
        metadata = [
            {"language": "python", "type": "tutorial"},
            {"language": "javascript", "type": "guide"},
            {"language": "rust", "type": "tutorial"}
        ]
        
        # Add vectors
        ids = await adapter.add_vectors(vectors, texts, metadata)
        assert len(ids) == 3
        
        # Search for similar vectors
        query_vector = [0.1, 0.2, 0.3, 0.4]  # Similar to first document
        results = await adapter.search(query_vector, k=2)
        
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        # First result should be most similar
        assert "Python" in results[0].text
        
    @pytest.mark.asyncio
    async def test_search_with_filters(self, adapter):
        """Test searching with metadata filters."""
        # Add test data
        vectors = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        texts = ["Doc 1", "Doc 2", "Doc 3"]
        metadata = [
            {"type": "code", "language": "python"},
            {"type": "docs", "language": "python"},
            {"type": "code", "language": "javascript"}
        ]
        
        await adapter.add_vectors(vectors, texts, metadata)
        
        # Search with filter
        query = [0.5, 0.5, 0.5]
        results = await adapter.search(
            query, k=10, filter_dict={"type": "code"}
        )
        
        # Should only return code documents
        assert all(r.metadata["type"] == "code" for r in results)
        assert len(results) == 2
        
    @pytest.mark.asyncio
    async def test_get_by_ids(self, adapter):
        """Test retrieving vectors by IDs."""
        # Add vectors
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["Doc A", "Doc B"]
        metadata = [{"id": 1}, {"id": 2}]
        
        ids = await adapter.add_vectors(vectors, texts, metadata)
        
        # Get by IDs
        results = await adapter.get_by_ids([ids[0]])
        assert len(results) == 1
        assert results[0].text == "Doc A"
        assert results[0].metadata["id"] == 1
        
    @pytest.mark.asyncio
    async def test_delete_vectors(self, adapter):
        """Test deleting vectors."""
        # Add vectors
        vectors = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        texts = ["A", "B", "C"]
        metadata = [{}, {}, {}]
        
        ids = await adapter.add_vectors(vectors, texts, metadata)
        initial_count = await adapter.count()
        assert initial_count == 3
        
        # Delete one vector
        success = await adapter.delete([ids[0]])
        assert success is True
        
        # Verify count
        final_count = await adapter.count()
        assert final_count == 2
        
        # Verify deleted vector is gone
        results = await adapter.get_by_ids([ids[0]])
        assert len(results) == 0
        
    @pytest.mark.asyncio
    async def test_clear_collection(self, adapter):
        """Test clearing the collection."""
        # Add vectors
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["X", "Y"]
        metadata = [{}, {}]
        
        await adapter.add_vectors(vectors, texts, metadata)
        assert await adapter.count() > 0
        
        # Clear
        success = await adapter.clear()
        assert success is True
        
        # Verify empty
        assert await adapter.count() == 0
        
    @pytest.mark.asyncio
    async def test_update_metadata(self, adapter):
        """Test updating vector metadata."""
        # Add vector
        vectors = [[0.1, 0.2]]
        texts = ["Original"]
        metadata = [{"version": 1}]
        
        ids = await adapter.add_vectors(vectors, texts, metadata)
        
        # Update metadata
        new_metadata = {"version": 2, "updated": True}
        success = await adapter.update_metadata(ids[0], new_metadata)
        assert success is True
        
        # Verify update
        results = await adapter.get_by_ids([ids[0]])
        assert results[0].metadata["version"] == 2
        assert results[0].metadata["updated"] is True
        
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check."""
        # Should be healthy
        healthy = await adapter.health_check()
        assert healthy is True
        
    @pytest.mark.asyncio
    async def test_empty_search(self, adapter):
        """Test searching empty collection."""
        results = await adapter.search([0.1, 0.2, 0.3], k=5)
        assert len(results) == 0
        
    @pytest.mark.asyncio
    async def test_large_batch(self, adapter):
        """Test adding large batch of vectors."""
        # Create 100 vectors
        n = 100
        dim = 10
        vectors = [[float(i+j) for j in range(dim)] for i in range(n)]
        texts = [f"Document {i}" for i in range(n)]
        metadata = [{"index": i} for i in range(n)]
        
        # Add all vectors
        ids = await adapter.add_vectors(vectors, texts, metadata)
        assert len(ids) == n
        
        # Verify count
        count = await adapter.count()
        assert count == n