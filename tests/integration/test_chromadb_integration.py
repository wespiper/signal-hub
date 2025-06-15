"""Integration tests for ChromaDB storage."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from signal_hub.storage import ChromaDBClient, Document, QueryResult
from signal_hub.storage.queries import QueryBuilder, FilterOperator


# Skip tests if ChromaDB not installed
pytest.importorskip("chromadb")


class TestChromaDBIntegration:
    """Integration tests for ChromaDB client."""
    
    @pytest.fixture
    async def client(self):
        """Create a test ChromaDB client."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = ChromaDBClient(path=Path(tmpdir))
            await client.connect()
            yield client
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_client_connect_disconnect(self):
        """Test client connection lifecycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = ChromaDBClient(path=Path(tmpdir))
            
            # Connect
            await client.connect()
            assert client._client is not None
            
            # Disconnect
            await client.disconnect()
            assert client._client is None
    
    @pytest.mark.asyncio
    async def test_create_collection(self, client):
        """Test creating a collection."""
        collection = await client.create_collection("test-collection")
        
        assert collection.name == "test-collection"
        assert collection.metadata.name == "test-collection"
        
        # Verify it exists
        collections = await client.list_collections()
        assert "test-collection" in collections
    
    @pytest.mark.asyncio
    async def test_get_collection(self, client):
        """Test getting an existing collection."""
        # Create collection
        await client.create_collection("test-get")
        
        # Get it
        collection = await client.get_collection("test-get")
        assert collection is not None
        assert collection.name == "test-get"
        
        # Get non-existent
        collection = await client.get_collection("non-existent")
        assert collection is None
    
    @pytest.mark.asyncio
    async def test_get_or_create_collection(self, client):
        """Test get or create collection."""
        # First call creates
        collection1 = await client.get_or_create_collection("test-goc")
        assert collection1.name == "test-goc"
        
        # Second call gets existing
        collection2 = await client.get_or_create_collection("test-goc")
        assert collection2.name == "test-goc"
    
    @pytest.mark.asyncio
    async def test_delete_collection(self, client):
        """Test deleting a collection."""
        # Create and verify
        await client.create_collection("test-delete")
        collections = await client.list_collections()
        assert "test-delete" in collections
        
        # Delete
        await client.delete_collection("test-delete")
        
        # Verify deleted
        collections = await client.list_collections()
        assert "test-delete" not in collections
    
    @pytest.mark.asyncio
    async def test_collection_add_documents(self, client):
        """Test adding documents to collection."""
        collection = await client.create_collection("test-add")
        
        # Create documents
        docs = [
            Document.create(
                content="def hello(): print('Hello')",
                embedding=[0.1, 0.2, 0.3],
                metadata={"type": "function", "language": "python"}
            ),
            Document.create(
                content="class MyClass: pass",
                embedding=[0.4, 0.5, 0.6],
                metadata={"type": "class", "language": "python"}
            )
        ]
        
        # Add to collection
        await collection.add(docs)
        
        # Verify count
        count = await collection.count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_collection_query(self, client):
        """Test querying collection."""
        collection = await client.create_collection("test-query")
        
        # Add test documents
        docs = [
            Document.create(
                content="function one",
                embedding=[1.0, 0.0, 0.0],
                metadata={"id": 1}
            ),
            Document.create(
                content="function two",
                embedding=[0.0, 1.0, 0.0],
                metadata={"id": 2}
            ),
            Document.create(
                content="function three",
                embedding=[0.0, 0.0, 1.0],
                metadata={"id": 3}
            ),
        ]
        await collection.add(docs)
        
        # Query with similar vector
        results = await collection.query(
            query_embeddings=[0.9, 0.1, 0.0],  # Close to first doc
            n_results=2
        )
        
        assert len(results) == 2
        # First result should be closest
        assert results[0].metadata["id"] == 1
        assert results[0].similarity > 0.8
    
    @pytest.mark.asyncio
    async def test_collection_query_with_filter(self, client):
        """Test querying with metadata filter."""
        collection = await client.create_collection("test-filter")
        
        # Add documents with different types
        docs = [
            Document.create(
                content="def func1()",
                embedding=[0.1, 0.2, 0.3],
                metadata={"type": "function", "name": "func1"}
            ),
            Document.create(
                content="class Class1",
                embedding=[0.1, 0.2, 0.3],  # Same embedding
                metadata={"type": "class", "name": "Class1"}
            ),
            Document.create(
                content="def func2()",
                embedding=[0.1, 0.2, 0.3],  # Same embedding
                metadata={"type": "function", "name": "func2"}
            ),
        ]
        await collection.add(docs)
        
        # Query with filter
        builder = QueryBuilder()
        filter = builder.where("type", FilterOperator.EQ, "function").build()
        
        results = await collection.query(
            query_embeddings=[0.1, 0.2, 0.3],
            n_results=10,
            filter=filter
        )
        
        # Should only get functions
        assert len(results) == 2
        assert all(r.metadata["type"] == "function" for r in results)
    
    @pytest.mark.asyncio
    async def test_collection_get_by_id(self, client):
        """Test getting documents by ID."""
        collection = await client.create_collection("test-get-id")
        
        # Add documents with known IDs
        docs = [
            Document(
                id="doc1",
                content="content 1",
                embedding=[0.1, 0.2],
                metadata={"num": 1}
            ),
            Document(
                id="doc2",
                content="content 2",
                embedding=[0.3, 0.4],
                metadata={"num": 2}
            ),
        ]
        await collection.add(docs)
        
        # Get by single ID
        results = await collection.get("doc1")
        assert len(results) == 1
        assert results[0].id == "doc1"
        assert results[0].content == "content 1"
        
        # Get by multiple IDs
        results = await collection.get(["doc1", "doc2"])
        assert len(results) == 2
        assert {r.id for r in results} == {"doc1", "doc2"}
    
    @pytest.mark.asyncio
    async def test_collection_update(self, client):
        """Test updating documents."""
        collection = await client.create_collection("test-update")
        
        # Add document
        doc = Document(
            id="update-me",
            content="original content",
            embedding=[0.1, 0.2],
            metadata={"version": 1}
        )
        await collection.add(doc)
        
        # Update content and metadata
        await collection.update(
            ids="update-me",
            documents="updated content",
            metadatas={"version": 2, "updated": True}
        )
        
        # Verify update
        results = await collection.get("update-me")
        assert results[0].content == "updated content"
        assert results[0].metadata["version"] == 2
        assert results[0].metadata["updated"] is True
    
    @pytest.mark.asyncio
    async def test_collection_delete(self, client):
        """Test deleting documents."""
        collection = await client.create_collection("test-delete-docs")
        
        # Add documents
        docs = [
            Document(id=f"doc{i}", content=f"content {i}", embedding=[i*0.1, i*0.2])
            for i in range(5)
        ]
        await collection.add(docs)
        
        # Delete by ID
        await collection.delete(ids=["doc1", "doc3"])
        
        # Verify deletion
        remaining = await collection.get([f"doc{i}" for i in range(5)])
        remaining_ids = {doc.id for doc in remaining}
        assert remaining_ids == {"doc0", "doc2", "doc4"}
    
    @pytest.mark.asyncio
    async def test_collection_clear(self, client):
        """Test clearing all documents."""
        collection = await client.create_collection("test-clear")
        
        # Add documents
        docs = [
            Document.create(content=f"doc{i}", embedding=[i*0.1])
            for i in range(3)
        ]
        await collection.add(docs)
        
        # Clear
        await collection.clear()
        
        # Verify empty
        count = await collection.count()
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, client):
        """Test concurrent operations on collections."""
        collection = await client.create_collection("test-concurrent")
        
        # Concurrent adds
        async def add_batch(start_id):
            docs = [
                Document.create(
                    content=f"doc{start_id + i}",
                    embedding=[float(start_id + i)],
                    metadata={"batch": start_id}
                )
                for i in range(10)
            ]
            await collection.add(docs)
        
        # Run concurrent adds
        await asyncio.gather(
            add_batch(0),
            add_batch(10),
            add_batch(20)
        )
        
        # Verify all added
        count = await collection.count()
        assert count == 30
    
    @pytest.mark.asyncio
    async def test_persistence(self):
        """Test data persistence across client restarts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            
            # First client - add data
            client1 = ChromaDBClient(path=path)
            await client1.connect()
            
            collection1 = await client1.create_collection("persistent")
            await collection1.add([
                Document.create(content="persistent doc", embedding=[0.1, 0.2])
            ])
            
            await client1.disconnect()
            
            # Second client - verify data
            client2 = ChromaDBClient(path=path)
            await client2.connect()
            
            collection2 = await client2.get_collection("persistent")
            assert collection2 is not None
            
            count = await collection2.count()
            assert count == 1
            
            await client2.disconnect()