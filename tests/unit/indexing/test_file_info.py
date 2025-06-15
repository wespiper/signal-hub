"""Unit tests for FileInfo class."""

import pytest
from pathlib import Path
import tempfile

from signal_hub.indexing.file_info import FileInfo, FileType, EXTENSION_MAP


class TestFileType:
    """Test FileType enum and extension mapping."""
    
    def test_extension_map_coverage(self):
        """Test that common extensions are mapped."""
        assert EXTENSION_MAP[".py"] == FileType.PYTHON
        assert EXTENSION_MAP[".js"] == FileType.JAVASCRIPT
        assert EXTENSION_MAP[".ts"] == FileType.TYPESCRIPT
        assert EXTENSION_MAP[".java"] == FileType.JAVA
        assert EXTENSION_MAP[".cpp"] == FileType.CPP
        assert EXTENSION_MAP[".go"] == FileType.GO
        assert EXTENSION_MAP[".rs"] == FileType.RUST
        assert EXTENSION_MAP[".md"] == FileType.MARKDOWN
    
    def test_multiple_extensions_same_type(self):
        """Test that related extensions map to same type."""
        assert EXTENSION_MAP[".py"] == EXTENSION_MAP[".pyi"]
        assert EXTENSION_MAP[".js"] == EXTENSION_MAP[".jsx"]
        assert EXTENSION_MAP[".ts"] == EXTENSION_MAP[".tsx"]
        assert EXTENSION_MAP[".yaml"] == EXTENSION_MAP[".yml"]


class TestFileInfo:
    """Test FileInfo class."""
    
    def test_file_info_creation(self):
        """Test creating FileInfo manually."""
        path = Path("/test/file.py")
        info = FileInfo(
            path=path,
            size=1024,
            file_type=FileType.PYTHON,
            language="python",
            encoding="utf-8",
            is_binary=False
        )
        
        assert info.path == path
        assert info.size == 1024
        assert info.file_type == FileType.PYTHON
        assert info.language == "python"
        assert info.encoding == "utf-8"
        assert not info.is_binary
    
    def test_extension_property(self):
        """Test file extension extraction."""
        info = FileInfo(
            path=Path("/test/file.PY"),  # Test case insensitive
            size=100,
            file_type=FileType.PYTHON
        )
        
        assert info.extension == ".py"
    
    def test_should_index_text_file(self):
        """Test that text files should be indexed."""
        info = FileInfo(
            path=Path("/test/file.py"),
            size=1000,
            file_type=FileType.PYTHON,
            is_binary=False
        )
        
        assert info.should_index() is True
    
    def test_should_not_index_binary(self):
        """Test that binary files should not be indexed."""
        info = FileInfo(
            path=Path("/test/file.exe"),
            size=1000,
            file_type=FileType.UNKNOWN,
            is_binary=True
        )
        
        assert info.should_index() is False
    
    def test_should_not_index_large_file(self):
        """Test that very large files should not be indexed."""
        info = FileInfo(
            path=Path("/test/file.py"),
            size=2 * 1024 * 1024,  # 2MB
            file_type=FileType.PYTHON,
            is_binary=False
        )
        
        assert info.should_index() is False
    
    def test_should_not_index_unknown_type(self):
        """Test that unknown file types should not be indexed."""
        info = FileInfo(
            path=Path("/test/file.xyz"),
            size=100,
            file_type=FileType.UNKNOWN,
            is_binary=False
        )
        
        assert info.should_index() is False
    
    def test_from_path_with_python_file(self):
        """Test creating FileInfo from an actual Python file."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"print('hello world')\n")
            f.flush()
            
            path = Path(f.name)
            info = FileInfo.from_path(path)
            
            assert info.path == path
            assert info.size == 21  # Length of content
            assert info.file_type == FileType.PYTHON
            assert not info.is_binary
            assert info.should_index() is True
            
            path.unlink()
    
    def test_from_path_with_binary_file(self):
        """Test creating FileInfo from a binary file."""
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            f.flush()
            
            path = Path(f.name)
            info = FileInfo.from_path(path)
            
            assert info.path == path
            assert info.size == 4
            assert info.file_type == FileType.UNKNOWN
            assert info.is_binary is True
            assert info.should_index() is False
            
            path.unlink()
    
    def test_from_path_text_file_unknown_extension(self):
        """Test that unknown extensions are checked for text content."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"This is plain text content\n")
            f.flush()
            
            path = Path(f.name)
            info = FileInfo.from_path(path)
            
            assert info.path == path
            assert info.file_type == FileType.TEXT
            assert not info.is_binary
            assert info.should_index() is True
            
            path.unlink()
    
    def test_from_path_nonexistent_file(self):
        """Test handling of non-existent files."""
        path = Path("/nonexistent/file.py")
        info = FileInfo.from_path(path)
        
        assert info.path == path
        assert info.size == 0
        assert info.file_type == FileType.PYTHON