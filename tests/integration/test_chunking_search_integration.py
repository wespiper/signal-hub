"""Integration tests for chunking and search."""

import pytest
import asyncio
from pathlib import Path
from typing import List

from signal_hub.indexing.chunking import ChunkingStrategy, ChunkingContext
from signal_hub.indexing.embeddings import EmbeddingService
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery, SearchConfig
from signal_hub.storage.factory import StoreFactory


class TestChunkingSearchIntegration:
    """Test integration between chunking and semantic search."""
    
    @pytest.fixture
    async def test_environment(self, tmp_path):
        """Set up test environment with all components."""
        # Create stores
        stores = StoreFactory.create_from_config({
            "vector_store": {
                "type": "memory"
            },
            "cache_store": {
                "type": "memory"
            }
        })
        
        # Create services
        embedding_service = EmbeddingService()
        search_config = SearchConfig(
            similarity_threshold=0.3,
            rerank_results=True
        )
        
        search_engine = SemanticSearchEngine(
            vector_store=stores["vector_store"],
            embedding_service=embedding_service,
            config=search_config,
            cache_store=stores["cache_store"]
        )
        
        return {
            "vector_store": stores["vector_store"],
            "cache_store": stores["cache_store"],
            "embedding_service": embedding_service,
            "search_engine": search_engine
        }
        
    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return '''
"""User authentication module."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

from database import User, Session
from .exceptions import AuthenticationError


class UserAuthenticator:
    """Handles user authentication and session management."""
    
    def __init__(self, secret_key: str):
        """Initialize authenticator with secret key."""
        self.secret_key = secret_key
        self.sessions: Dict[str, Session] = {}
        
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with credentials.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User object if authenticated, None otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Hash password
        password_hash = self._hash_password(password)
        
        # Query database
        user = User.query.filter_by(
            username=username,
            password_hash=password_hash
        ).first()
        
        if not user:
            raise AuthenticationError("Invalid credentials")
            
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
            
        # Create session
        session = self._create_session(user)
        self.sessions[session.token] = session
        
        return user
        
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        combined = f"{password}{self.secret_key}"
        return hashlib.sha256(combined.encode()).hexdigest()
        
    def _create_session(self, user: User) -> Session:
        """Create a new session for user."""
        return Session(
            token=secrets.token_urlsafe(32),
            user_id=user.id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )


def validate_session(token: str, authenticator: UserAuthenticator) -> bool:
    """Validate a session token."""
    session = authenticator.sessions.get(token)
    
    if not session:
        return False
        
    if session.expires_at < datetime.now():
        # Session expired
        del authenticator.sessions[token]
        return False
        
    return True
'''
        
    @pytest.mark.asyncio
    async def test_chunk_and_index(self, test_environment, sample_python_code, tmp_path):
        """Test chunking code and indexing for search."""
        # Write sample code to file
        test_file = tmp_path / "auth.py"
        test_file.write_text(sample_python_code)
        
        # Chunk the code
        strategy = ChunkingStrategy.for_language("python")
        chunks = strategy.chunk_file(test_file)
        
        # Should have multiple chunks
        assert len(chunks) > 0
        
        # Index chunks
        vector_store = test_environment["vector_store"]
        embedding_service = test_environment["embedding_service"]
        
        for chunk in chunks:
            # Generate embedding
            result = await embedding_service.generate_embeddings([chunk.content])
            
            # Store in vector database
            metadata = {
                **chunk.metadata,
                "chunk_type": chunk.chunk_type.value,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "file_path": str(test_file),
                "parent_context": chunk.parent_context
            }
            
            await vector_store.add_vectors(
                vectors=result.embeddings,
                texts=[chunk.content],
                metadata=[metadata]
            )
            
        # Verify indexing
        count = await vector_store.count()
        assert count == len(chunks)
        
    @pytest.mark.asyncio
    async def test_search_indexed_code(self, test_environment, sample_python_code, tmp_path):
        """Test searching indexed code."""
        # Index the sample code
        await self.test_chunk_and_index(test_environment, sample_python_code, tmp_path)
        
        search_engine = test_environment["search_engine"]
        
        # Search for authentication functionality
        query = SearchQuery(
            text="user authentication password",
            limit=5
        )
        
        results = await search_engine.search(query)
        
        # Should find relevant results
        assert len(results) > 0
        
        # Top result should be the authenticate method
        top_result = results[0]
        assert "authenticate" in top_result.text.lower()
        assert top_result.metadata.get("chunk_type") in ["method", "function"]
        
    @pytest.mark.asyncio
    async def test_search_with_filters(self, test_environment, sample_python_code, tmp_path):
        """Test searching with metadata filters."""
        # Index the sample code
        await self.test_chunk_and_index(test_environment, sample_python_code, tmp_path)
        
        search_engine = test_environment["search_engine"]
        
        # Search for only methods
        query = SearchQuery(
            text="password",
            filters={"chunk_type": "method"},
            limit=10
        )
        
        results = await search_engine.search(query)
        
        # All results should be methods
        assert all(r.metadata.get("chunk_type") == "method" for r in results)
        
        # Should include _hash_password method
        method_names = [r.metadata.get("function_name", "") for r in results]
        assert "_hash_password" in method_names
        
    @pytest.mark.asyncio
    async def test_search_with_context(self, test_environment, sample_python_code, tmp_path):
        """Test that parent context is preserved in search."""
        await self.test_chunk_and_index(test_environment, sample_python_code, tmp_path)
        
        search_engine = test_environment["search_engine"]
        
        # Search for session management
        query = SearchQuery(
            text="create session",
            limit=5
        )
        
        results = await search_engine.search(query)
        
        # Find the _create_session method
        session_results = [r for r in results 
                          if "_create_session" in r.text]
        
        assert len(session_results) > 0
        
        # Should have parent context
        result = session_results[0]
        assert result.metadata.get("parent_context") == "UserAuthenticator"
        
    @pytest.mark.asyncio
    async def test_hybrid_search(self, test_environment, sample_python_code, tmp_path):
        """Test hybrid semantic + keyword search."""
        await self.test_chunk_and_index(test_environment, sample_python_code, tmp_path)
        
        search_engine = test_environment["search_engine"]
        
        # Hybrid search for specific terms
        query = SearchQuery(
            text="SHA256 hash security",
            mode="hybrid",
            limit=5
        )
        
        results = await search_engine.search(query)
        
        # Should find the _hash_password method
        assert any("sha256" in r.text.lower() for r in results)
        
    @pytest.mark.asyncio
    async def test_search_performance(self, test_environment, tmp_path):
        """Test search performance with multiple files."""
        # Create and index multiple Python files
        for i in range(10):
            code = f'''
def function_{i}(param):
    """Function {i} documentation."""
    return param * {i}
    
class Class_{i}:
    """Class {i} for testing."""
    
    def method_{i}(self):
        """Method {i} implementation."""
        return "result_{i}"
'''
            test_file = tmp_path / f"test_{i}.py"
            test_file.write_text(code)
            
            # Chunk and index
            strategy = ChunkingStrategy.for_language("python")
            chunks = strategy.chunk_file(test_file)
            
            for chunk in chunks:
                result = await test_environment["embedding_service"].generate_embeddings([chunk.content])
                
                metadata = {
                    "chunk_type": chunk.chunk_type.value,
                    "file_path": str(test_file),
                    "file_index": i
                }
                
                await test_environment["vector_store"].add_vectors(
                    vectors=result.embeddings,
                    texts=[chunk.content],
                    metadata=[metadata]
                )
                
        # Perform search
        import time
        start = time.time()
        
        query = SearchQuery(text="method implementation", limit=10)
        results = await test_environment["search_engine"].search(query)
        
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 2.0  # Less than 2 seconds
        assert len(results) > 0
        
        # Should find methods from different files
        file_indices = set(r.metadata.get("file_index") for r in results)
        assert len(file_indices) > 1
        
    @pytest.mark.asyncio
    async def test_caching(self, test_environment, sample_python_code, tmp_path):
        """Test search result caching."""
        await self.test_chunk_and_index(test_environment, sample_python_code, tmp_path)
        
        search_engine = test_environment["search_engine"]
        
        # First search
        query = SearchQuery(text="authentication", limit=5)
        
        import time
        start1 = time.time()
        results1 = await search_engine.search(query)
        time1 = time.time() - start1
        
        # Second search (should hit cache)
        start2 = time.time()
        results2 = await search_engine.search(query)
        time2 = time.time() - start2
        
        # Cache should be faster
        assert time2 < time1
        
        # Results should be the same
        assert len(results1) == len(results2)
        assert results1[0].id == results2[0].id