"""Tests for semantic search engine."""

import pytest
from typing import List
import numpy as np

from signal_hub.retrieval.search import (
    SemanticSearchEngine,
    SearchQuery,
    SearchResult,
    SearchConfig
)
from signal_hub.storage.interfaces import VectorStore, SearchResult as VectorSearchResult


class MockVectorStore(VectorStore):
    """Mock vector store for testing."""
    
    def __init__(self):
        self.data = {}
        self.embeddings = {}
        
    async def add_vectors(self, vectors: List[List[float]], texts: List[str], metadata: List[dict]) -> List[str]:
        ids = []
        for i, (vec, text, meta) in enumerate(zip(vectors, texts, metadata)):
            id_ = f"test_{len(self.data)}"
            self.data[id_] = {"text": text, "metadata": meta}
            self.embeddings[id_] = vec
            ids.append(id_)
        return ids
        
    async def search(self, query_vector: List[float], k: int = 10, filter_dict: dict = None) -> List[VectorSearchResult]:
        # Simple cosine similarity
        results = []
        for id_, vec in self.embeddings.items():
            if filter_dict:
                # Apply filters
                item_meta = self.data[id_]["metadata"]
                if not all(item_meta.get(k) == v for k, v in filter_dict.items()):
                    continue
                    
            # Calculate similarity
            score = np.dot(query_vector, vec) / (np.linalg.norm(query_vector) * np.linalg.norm(vec))
            
            results.append(VectorSearchResult(
                id=id_,
                score=float(score),
                text=self.data[id_]["text"],
                metadata=self.data[id_]["metadata"]
            ))
            
        # Sort by score and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
        
    async def get_by_ids(self, ids: List[str]) -> List[VectorSearchResult]:
        results = []
        for id_ in ids:
            if id_ in self.data:
                results.append(VectorSearchResult(
                    id=id_,
                    score=1.0,
                    text=self.data[id_]["text"],
                    metadata=self.data[id_]["metadata"]
                ))
        return results
        
    async def delete(self, ids: List[str]) -> bool:
        for id_ in ids:
            self.data.pop(id_, None)
            self.embeddings.pop(id_, None)
        return True
        
    async def clear(self) -> bool:
        self.data.clear()
        self.embeddings.clear()
        return True
        
    async def count(self) -> int:
        return len(self.data)


class MockEmbeddingService:
    """Mock embedding service for testing."""
    
    async def generate_embeddings(self, texts: List[str]):
        # Simple mock embeddings based on text length
        embeddings = []
        for text in texts:
            # Create a simple embedding based on text features
            embedding = [
                len(text) / 100,  # Length feature
                text.count(' ') / 10,  # Word count feature
                1.0 if 'function' in text.lower() else 0.0,
                1.0 if 'class' in text.lower() else 0.0,
                1.0 if 'import' in text.lower() else 0.0,
            ]
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]
            embeddings.append(embedding)
            
        return type('Result', (), {'embeddings': embeddings})()


class TestSemanticSearchEngine:
    """Test semantic search engine functionality."""
    
    @pytest.fixture
    async def search_engine(self):
        """Create search engine with mocks."""
        vector_store = MockVectorStore()
        embedding_service = MockEmbeddingService()
        
        config = SearchConfig(
            similarity_threshold=0.5,
            max_results=10,
            rerank_results=True
        )
        
        engine = SemanticSearchEngine(
            vector_store=vector_store,
            embedding_service=embedding_service,
            config=config
        )
        
        # Add some test data
        test_data = [
            ("def authenticate_user(username, password):", {"type": "function", "name": "authenticate_user"}),
            ("class UserAuthenticator:", {"type": "class", "name": "UserAuthenticator"}),
            ("import jwt from jsonwebtoken", {"type": "import", "module": "jwt"}),
            ("function validateToken(token) {", {"type": "function", "language": "javascript"}),
            ("# This function handles user login", {"type": "comment"}),
        ]
        
        for text, metadata in test_data:
            result = await embedding_service.generate_embeddings([text])
            await vector_store.add_vectors(
                result.embeddings,
                [text],
                [metadata]
            )
            
        return engine
        
    @pytest.mark.asyncio
    async def test_basic_search(self, search_engine):
        """Test basic semantic search."""
        query = SearchQuery(
            text="user authentication function",
            limit=5
        )
        
        results = await search_engine.search(query)
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        
        # Should find authentication-related results
        auth_results = [r for r in results if 'auth' in r.text.lower()]
        assert len(auth_results) > 0
        
    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_engine):
        """Test search with metadata filters."""
        query = SearchQuery(
            text="function",
            filters={"type": "function"},
            limit=10
        )
        
        results = await search_engine.search(query)
        
        # All results should be functions
        assert all(r.metadata.get("type") == "function" for r in results)
        
    @pytest.mark.asyncio
    async def test_search_with_language_filter(self, search_engine):
        """Test filtering by programming language."""
        query = SearchQuery(
            text="function",
            filters={"language": "javascript"},
            limit=5
        )
        
        results = await search_engine.search(query)
        
        # Should only return JavaScript functions
        assert all(r.metadata.get("language") == "javascript" for r in results)
        
    @pytest.mark.asyncio
    async def test_similarity_threshold(self, search_engine):
        """Test similarity threshold filtering."""
        # Search for something very specific
        query = SearchQuery(
            text="xyz123 nonexistent",
            limit=10
        )
        
        results = await search_engine.search(query)
        
        # Results should respect similarity threshold
        assert all(r.score >= search_engine.config.similarity_threshold for r in results)
        
    @pytest.mark.asyncio
    async def test_result_limit(self, search_engine):
        """Test result limit is respected."""
        query = SearchQuery(
            text="code",
            limit=2
        )
        
        results = await search_engine.search(query)
        
        assert len(results) <= 2
        
    @pytest.mark.asyncio
    async def test_empty_query(self, search_engine):
        """Test handling of empty query."""
        query = SearchQuery(
            text="",
            limit=5
        )
        
        results = await search_engine.search(query)
        
        # Should handle gracefully
        assert isinstance(results, list)
        
    @pytest.mark.asyncio
    async def test_result_ranking(self, search_engine):
        """Test that results are properly ranked."""
        query = SearchQuery(
            text="authenticate user function",
            limit=10
        )
        
        results = await search_engine.search(query)
        
        # Results should be sorted by score descending
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
        
        # Most relevant result should be first
        if results:
            assert 'authenticate' in results[0].text.lower()
            
    @pytest.mark.asyncio
    async def test_search_result_structure(self, search_engine):
        """Test search result structure."""
        query = SearchQuery(text="function", limit=1)
        
        results = await search_engine.search(query)
        
        if results:
            result = results[0]
            assert hasattr(result, 'id')
            assert hasattr(result, 'text')
            assert hasattr(result, 'score')
            assert hasattr(result, 'metadata')
            assert hasattr(result, 'chunk_id')
            assert 0 <= result.score <= 1
            
    @pytest.mark.asyncio
    async def test_batch_search(self, search_engine):
        """Test batch search functionality."""
        queries = [
            SearchQuery(text="authentication", limit=3),
            SearchQuery(text="class", limit=3),
            SearchQuery(text="import", limit=3),
        ]
        
        all_results = await search_engine.batch_search(queries)
        
        assert len(all_results) == len(queries)
        assert all(isinstance(results, list) for results in all_results)
        
    @pytest.mark.asyncio
    async def test_reranking(self, search_engine):
        """Test result reranking."""
        # Disable reranking
        search_engine.config.rerank_results = False
        query = SearchQuery(text="user function", limit=5)
        initial_results = await search_engine.search(query)
        
        # Enable reranking
        search_engine.config.rerank_results = True
        reranked_results = await search_engine.search(query)
        
        # Results might be in different order
        assert len(initial_results) == len(reranked_results)