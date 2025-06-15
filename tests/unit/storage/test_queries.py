"""Unit tests for query builders."""

import pytest

from signal_hub.storage.queries import (
    QueryBuilder, FilterOperator, SearchQuery
)


class TestQueryBuilder:
    """Test QueryBuilder class."""
    
    @pytest.fixture
    def builder(self):
        """Create a query builder."""
        return QueryBuilder()
    
    def test_simple_equality(self, builder):
        """Test simple equality filter."""
        filter = builder.where("type", FilterOperator.EQ, "function").build()
        
        assert filter.where is not None
        assert filter.where["type"]["$eq"] == "function"
    
    def test_comparison_operators(self, builder):
        """Test comparison operators."""
        # Greater than
        filter = builder.where("size", FilterOperator.GT, 100).build()
        assert filter.where["size"]["$gt"] == 100
        
        # Less than or equal
        builder.reset()
        filter = builder.where("lines", FilterOperator.LTE, 50).build()
        assert filter.where["lines"]["$lte"] == 50
    
    def test_list_operators(self, builder):
        """Test list operators."""
        # In list
        filter = builder.where("language", FilterOperator.IN, ["python", "javascript"]).build()
        assert filter.where["language"]["$in"] == ["python", "javascript"]
        
        # Single value converted to list
        builder.reset()
        filter = builder.where("type", FilterOperator.IN, "function").build()
        assert filter.where["type"]["$in"] == ["function"]
    
    def test_document_filter(self, builder):
        """Test document content filter."""
        filter = builder.where_document(FilterOperator.EQ, "search text").build()
        
        assert filter.where_document is not None
        assert filter.where_document["$contains"] == "search text"
    
    def test_and_conditions(self, builder):
        """Test AND conditions."""
        filter = builder.and_(
            {"type": {"$eq": "function"}},
            {"language": {"$eq": "python"}}
        ).build()
        
        assert "$and" in filter.where
        assert len(filter.where["$and"]) == 2
    
    def test_or_conditions(self, builder):
        """Test OR conditions."""
        filter = builder.or_(
            {"type": {"$eq": "function"}},
            {"type": {"$eq": "class"}}
        ).build()
        
        assert "$or" in filter.where
        assert len(filter.where["$or"]) == 2
    
    def test_chaining(self, builder):
        """Test method chaining."""
        filter = (builder
            .where("type", FilterOperator.EQ, "function")
            .where("language", FilterOperator.IN, ["python", "javascript"])
            .where_document(FilterOperator.EQ, "async")
            .build())
        
        assert filter.where["type"]["$eq"] == "function"
        assert filter.where["language"]["$in"] == ["python", "javascript"]
        assert filter.where_document["$contains"] == "async"
    
    def test_reset(self, builder):
        """Test resetting builder."""
        builder.where("type", FilterOperator.EQ, "function")
        builder.reset()
        
        filter = builder.build()
        assert filter.where is None
        assert filter.where_document is None
    
    def test_static_helpers(self):
        """Test static helper methods."""
        # Equality
        cond = QueryBuilder.eq("type", "function")
        assert cond["type"]["$eq"] == "function"
        
        # Not equal
        cond = QueryBuilder.ne("status", "deleted")
        assert cond["status"]["$ne"] == "deleted"
        
        # Comparison
        cond = QueryBuilder.gt("size", 100)
        assert cond["size"]["$gt"] == 100
        
        cond = QueryBuilder.gte("score", 0.8)
        assert cond["score"]["$gte"] == 0.8
        
        # List operations
        cond = QueryBuilder.in_("language", ["python", "go"])
        assert cond["language"]["$in"] == ["python", "go"]
        
        cond = QueryBuilder.nin("status", ["draft", "deleted"])
        assert cond["status"]["$nin"] == ["draft", "deleted"]


class TestSearchQuery:
    """Test SearchQuery class."""
    
    def test_valid_text_query(self):
        """Test valid text-based query."""
        query = SearchQuery(text="search text", limit=20)
        query.validate()  # Should not raise
        
        assert query.text == "search text"
        assert query.limit == 20
        assert query.include_scores is True
    
    def test_valid_embedding_query(self):
        """Test valid embedding-based query."""
        query = SearchQuery(embedding=[0.1, 0.2, 0.3], limit=10)
        query.validate()  # Should not raise
        
        assert query.embedding == [0.1, 0.2, 0.3]
        assert query.limit == 10
    
    def test_invalid_no_input(self):
        """Test query without text or embedding."""
        query = SearchQuery(limit=10)
        
        with pytest.raises(ValueError) as exc_info:
            query.validate()
        
        assert "text or embedding must be provided" in str(exc_info.value)
    
    def test_invalid_both_inputs(self):
        """Test query with both text and embedding."""
        query = SearchQuery(
            text="search",
            embedding=[0.1, 0.2],
            limit=10
        )
        
        with pytest.raises(ValueError) as exc_info:
            query.validate()
        
        assert "Only one of text or embedding" in str(exc_info.value)
    
    def test_invalid_limit(self):
        """Test invalid limit values."""
        query = SearchQuery(text="search", limit=0)
        
        with pytest.raises(ValueError) as exc_info:
            query.validate()
        
        assert "Limit must be positive" in str(exc_info.value)
    
    def test_invalid_offset(self):
        """Test invalid offset values."""
        query = SearchQuery(text="search", offset=-1)
        
        with pytest.raises(ValueError) as exc_info:
            query.validate()
        
        assert "Offset must be non-negative" in str(exc_info.value)