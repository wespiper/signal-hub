"""Unit tests for storage models."""

import pytest
from datetime import datetime

from signal_hub.storage.models import (
    Document, QueryResult, CollectionMetadata, QueryFilter
)


class TestDocument:
    """Test Document model."""
    
    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            id="doc1",
            content="test content",
            embedding=[0.1, 0.2, 0.3],
            metadata={"key": "value"}
        )
        
        assert doc.id == "doc1"
        assert doc.content == "test content"
        assert doc.embedding == [0.1, 0.2, 0.3]
        assert doc.metadata["key"] == "value"
    
    def test_document_create_factory(self):
        """Test document factory method."""
        doc = Document.create(
            content="test",
            embedding=[0.1, 0.2],
            metadata={"type": "test"}
        )
        
        # Should generate UUID
        assert doc.id is not None
        assert len(doc.id) == 36  # UUID format
        
        # Should add timestamp
        assert "timestamp" in doc.metadata
        assert doc.metadata["type"] == "test"
    
    def test_document_create_with_id(self):
        """Test document factory with custom ID."""
        doc = Document.create(
            content="test",
            embedding=[0.1, 0.2],
            doc_id="custom-id"
        )
        
        assert doc.id == "custom-id"


class TestQueryResult:
    """Test QueryResult model."""
    
    def test_query_result_creation(self):
        """Test creating a query result."""
        result = QueryResult(
            id="doc1",
            content="test content",
            metadata={"key": "value"},
            distance=0.15
        )
        
        assert result.id == "doc1"
        assert result.content == "test content"
        assert result.distance == 0.15
        assert result.similarity == 0.85  # 1 - 0.15
    
    def test_query_result_with_score(self):
        """Test query result with explicit score."""
        result = QueryResult(
            id="doc1",
            content="test",
            metadata={},
            distance=0.2,
            score=0.95
        )
        
        # Should use explicit score
        assert result.similarity == 0.95
    
    def test_similarity_bounds(self):
        """Test similarity score bounds."""
        # High distance
        result = QueryResult(
            id="doc1",
            content="test",
            metadata={},
            distance=1.5
        )
        
        # Should clamp to 0
        assert result.similarity == 0.0


class TestCollectionMetadata:
    """Test CollectionMetadata model."""
    
    def test_metadata_creation(self):
        """Test creating collection metadata."""
        now = datetime.now()
        metadata = CollectionMetadata(
            name="test-collection",
            description="Test collection",
            created_at=now,
            document_count=100,
            dimension=128
        )
        
        assert metadata.name == "test-collection"
        assert metadata.description == "Test collection"
        assert metadata.created_at == now
        assert metadata.document_count == 100
        assert metadata.dimension == 128
    
    def test_metadata_serialization(self):
        """Test metadata serialization."""
        now = datetime.now()
        metadata = CollectionMetadata(
            name="test",
            created_at=now,
            updated_at=now,
            metadata={"custom": "field"}
        )
        
        data = metadata.to_dict()
        assert data["name"] == "test"
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        assert data["custom"] == "field"
        
        # Test deserialization
        metadata2 = CollectionMetadata.from_dict(data)
        assert metadata2.name == "test"
        assert metadata2.created_at == now
        assert metadata2.metadata["custom"] == "field"


class TestQueryFilter:
    """Test QueryFilter model."""
    
    def test_empty_filter(self):
        """Test empty filter."""
        filter = QueryFilter()
        result = filter.to_chroma_format()
        assert result == {}
    
    def test_metadata_filter(self):
        """Test metadata filter."""
        filter = QueryFilter(
            where={"type": {"$eq": "function"}}
        )
        
        result = filter.to_chroma_format()
        assert "where" in result
        assert result["where"]["type"]["$eq"] == "function"
    
    def test_document_filter(self):
        """Test document content filter."""
        filter = QueryFilter(
            where_document={"$contains": "search text"}
        )
        
        result = filter.to_chroma_format()
        assert "where_document" in result
        assert result["where_document"]["$contains"] == "search text"
    
    def test_combined_filter(self):
        """Test combined filters."""
        filter = QueryFilter(
            where={"type": {"$eq": "function"}},
            where_document={"$contains": "def"}
        )
        
        result = filter.to_chroma_format()
        assert "where" in result
        assert "where_document" in result