"""Unit tests for base parser."""

import pytest
from pathlib import Path
from typing import List, Optional

from signal_hub.indexing.parsers.base import Parser, ParseError
from signal_hub.indexing.parsers.models import Chunk, ChunkType


class MockParser(Parser):
    """Mock parser for testing base functionality."""
    
    languages = ["mock"]
    extensions = [".mock", ".mck"]
    
    def parse(self, content: str, file_path: Optional[Path] = None) -> List[Chunk]:
        """Simple mock parsing."""
        lines = content.split('\n')
        return [
            Chunk(
                type=ChunkType.BLOCK,
                name="mock_chunk",
                content=content,
                start_line=1,
                end_line=len(lines),
                file_path=file_path,
                language="mock"
            )
        ]


class TestParser:
    """Test base Parser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a mock parser."""
        return MockParser()
    
    def test_can_parse(self, parser):
        """Test file extension checking."""
        assert parser.can_parse("test.mock")
        assert parser.can_parse(Path("dir/file.mck"))
        assert not parser.can_parse("test.py")
        assert not parser.can_parse("file.txt")
    
    def test_parse_file(self, parser, tmp_path):
        """Test parsing a file."""
        # Create test file
        test_file = tmp_path / "test.mock"
        test_file.write_text("line1\nline2\nline3")
        
        chunks = parser.parse_file(test_file)
        
        assert len(chunks) == 1
        assert chunks[0].name == "mock_chunk"
        assert chunks[0].content == "line1\nline2\nline3"
        assert chunks[0].file_path == test_file
    
    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file."""
        with pytest.raises(IOError) as exc_info:
            parser.parse_file("/nonexistent/file.mock")
        
        assert "Failed to read file" in str(exc_info.value)
    
    def test_clean_content(self, parser):
        """Test content cleaning."""
        # Test trailing whitespace removal
        content = "line1  \nline2\t\nline3"
        cleaned = parser.clean_content(content)
        assert cleaned == "line1\nline2\nline3"
        
        # Test excessive blank lines
        content = "line1\n\n\n\n\nline2\n\n\n\nline3"
        cleaned = parser.clean_content(content)
        assert cleaned == "line1\n\n\nline2\n\n\nline3"
    
    def test_split_large_chunk(self, parser):
        """Test splitting large chunks."""
        # Create large content
        lines = [f"Line {i} with some content" for i in range(100)]
        large_content = '\n'.join(lines)
        
        chunk = Chunk(
            type=ChunkType.BLOCK,
            name="large_chunk",
            content=large_content,
            start_line=1,
            end_line=100,
            file_path=Path("test.py")
        )
        
        # Set small max size to force splitting
        parser.max_chunk_size = 500
        
        splits = parser.split_large_chunk(chunk)
        
        # Should be split into multiple chunks
        assert len(splits) > 1
        
        # Check split metadata
        for i, split in enumerate(splits):
            assert f"large_chunk_part_{i+1}" in split.name
            assert split.metadata["split"] is True
            assert split.metadata["original"] == "large_chunk"
        
        # Verify content is preserved
        combined = '\n'.join(s.content for s in splits)
        assert combined == large_content
    
    def test_split_preserves_small_chunks(self, parser):
        """Test that small chunks are not split."""
        small_chunk = Chunk(
            type=ChunkType.FUNCTION,
            name="small_func",
            content="def small_func():\n    return 42",
            start_line=10,
            end_line=11
        )
        
        splits = parser.split_large_chunk(small_chunk)
        
        assert len(splits) == 1
        assert splits[0] == small_chunk