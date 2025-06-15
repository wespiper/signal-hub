"""Tests for chunking strategy interface."""

import pytest
from pathlib import Path
from typing import List

from signal_hub.indexing.chunking.strategy import (
    ChunkingStrategy,
    ChunkingContext,
    CodeChunk,
    ChunkType
)


class TestChunkingStrategy:
    """Test chunking strategy interface."""
    
    def test_chunk_type_enum(self):
        """Test chunk type enumeration."""
        assert ChunkType.FUNCTION.value == "function"
        assert ChunkType.CLASS.value == "class"
        assert ChunkType.MODULE.value == "module"
        assert ChunkType.DOCUMENTATION.value == "documentation"
        
    def test_code_chunk_creation(self):
        """Test CodeChunk model creation."""
        chunk = CodeChunk(
            content="def hello():\n    return 'world'",
            start_line=10,
            end_line=11,
            chunk_type=ChunkType.FUNCTION,
            metadata={
                "function_name": "hello",
                "language": "python"
            }
        )
        
        assert chunk.content == "def hello():\n    return 'world'"
        assert chunk.start_line == 10
        assert chunk.end_line == 11
        assert chunk.chunk_type == ChunkType.FUNCTION
        assert chunk.metadata["function_name"] == "hello"
        
    def test_code_chunk_with_context(self):
        """Test CodeChunk with parent context."""
        chunk = CodeChunk(
            content="def method(self):\n    pass",
            start_line=20,
            end_line=21,
            chunk_type=ChunkType.FUNCTION,
            parent_context="class MyClass",
            metadata={"class_name": "MyClass"}
        )
        
        assert chunk.parent_context == "class MyClass"
        assert chunk.get_full_context() == "class MyClass > method"
        
    def test_chunking_context(self):
        """Test ChunkingContext configuration."""
        context = ChunkingContext(
            max_chunk_size=1000,
            overlap_size=100,
            preserve_context=True,
            min_chunk_size=50
        )
        
        assert context.max_chunk_size == 1000
        assert context.overlap_size == 100
        assert context.preserve_context is True
        assert context.min_chunk_size == 50
        
    def test_code_chunk_size_calculation(self):
        """Test chunk size calculation."""
        chunk = CodeChunk(
            content="line1\nline2\nline3",
            start_line=1,
            end_line=3,
            chunk_type=ChunkType.MODULE
        )
        
        assert chunk.size == len("line1\nline2\nline3")
        assert chunk.line_count == 3
        
    def test_code_chunk_validation(self):
        """Test chunk validation."""
        # Valid chunk
        chunk = CodeChunk(
            content="def foo(): pass",
            start_line=1,
            end_line=1,
            chunk_type=ChunkType.FUNCTION
        )
        assert chunk.is_valid_syntax is None  # Not validated yet
        
        # Test with empty content
        with pytest.raises(ValueError):
            CodeChunk(
                content="",
                start_line=1,
                end_line=1,
                chunk_type=ChunkType.FUNCTION
            )
            
    def test_chunk_overlap_handling(self):
        """Test chunk overlap information."""
        chunk = CodeChunk(
            content="def func():\n    # implementation\n    pass",
            start_line=10,
            end_line=12,
            chunk_type=ChunkType.FUNCTION,
            overlap_with_previous=50,
            overlap_with_next=30
        )
        
        assert chunk.overlap_with_previous == 50
        assert chunk.overlap_with_next == 30