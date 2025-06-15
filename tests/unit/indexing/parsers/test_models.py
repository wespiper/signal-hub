"""Unit tests for parser models."""

import pytest
from pathlib import Path

from signal_hub.indexing.parsers.models import Chunk, ChunkType


class TestChunk:
    """Test Chunk model."""
    
    def test_chunk_creation(self):
        """Test creating a chunk."""
        chunk = Chunk(
            type=ChunkType.FUNCTION,
            name="test_function",
            content="def test_function():\n    pass",
            start_line=10,
            end_line=11,
            file_path=Path("test.py"),
            language="python"
        )
        
        assert chunk.type == ChunkType.FUNCTION
        assert chunk.name == "test_function"
        assert chunk.start_line == 10
        assert chunk.end_line == 11
        assert chunk.line_count == 2
    
    def test_chunk_identifier(self):
        """Test chunk identifier generation."""
        chunk = Chunk(
            type=ChunkType.METHOD,
            name="method",
            content="def method(self): pass",
            start_line=20,
            end_line=20,
            file_path=Path("module.py"),
            parent="MyClass"
        )
        
        identifier = chunk.identifier
        assert "module.py" in identifier
        assert "MyClass" in identifier
        assert "method" in identifier
        assert "L20" in identifier
    
    def test_chunk_to_context_string(self):
        """Test context string generation."""
        chunk = Chunk(
            type=ChunkType.CLASS,
            name="TestClass",
            content="class TestClass:\n    pass",
            start_line=5,
            end_line=6,
            file_path=Path("test.py")
        )
        
        context = chunk.to_context_string()
        assert "File: test.py" in context
        assert "Lines 5-6" in context
        assert "class: TestClass" in context
        assert "class TestClass:" in context
    
    def test_chunk_overlaps(self):
        """Test chunk overlap detection."""
        chunk1 = Chunk(
            type=ChunkType.FUNCTION,
            name="func1",
            content="",
            start_line=10,
            end_line=20,
            file_path=Path("test.py")
        )
        
        # Overlapping chunk
        chunk2 = Chunk(
            type=ChunkType.FUNCTION,
            name="func2",
            content="",
            start_line=15,
            end_line=25,
            file_path=Path("test.py")
        )
        
        # Non-overlapping chunk
        chunk3 = Chunk(
            type=ChunkType.FUNCTION,
            name="func3",
            content="",
            start_line=30,
            end_line=35,
            file_path=Path("test.py")
        )
        
        # Different file
        chunk4 = Chunk(
            type=ChunkType.FUNCTION,
            name="func4",
            content="",
            start_line=15,
            end_line=25,
            file_path=Path("other.py")
        )
        
        assert chunk1.overlaps(chunk2)
        assert chunk2.overlaps(chunk1)
        assert not chunk1.overlaps(chunk3)
        assert not chunk1.overlaps(chunk4)
    
    def test_chunk_metadata(self):
        """Test chunk metadata handling."""
        chunk = Chunk(
            type=ChunkType.FUNCTION,
            name="func",
            content="",
            start_line=1,
            end_line=5,
            metadata={"async": True, "exported": False}
        )
        
        assert chunk.metadata["async"] is True
        assert chunk.metadata["exported"] is False
        
        # Test default metadata
        chunk2 = Chunk(
            type=ChunkType.FUNCTION,
            name="func2",
            content="",
            start_line=1,
            end_line=5
        )
        
        assert chunk2.metadata == {}