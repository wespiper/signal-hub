"""File information and metadata for scanned files."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import mimetypes


class FileType(Enum):
    """Supported file types for indexing."""
    
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"
    TEXT = "text"
    UNKNOWN = "unknown"


# File extension to type mapping
EXTENSION_MAP = {
    ".py": FileType.PYTHON,
    ".pyi": FileType.PYTHON,
    ".pyx": FileType.PYTHON,
    ".js": FileType.JAVASCRIPT,
    ".jsx": FileType.JAVASCRIPT,
    ".mjs": FileType.JAVASCRIPT,
    ".ts": FileType.TYPESCRIPT,
    ".tsx": FileType.TYPESCRIPT,
    ".java": FileType.JAVA,
    ".cpp": FileType.CPP,
    ".cc": FileType.CPP,
    ".cxx": FileType.CPP,
    ".hpp": FileType.CPP,
    ".h": FileType.C,
    ".c": FileType.C,
    ".go": FileType.GO,
    ".rs": FileType.RUST,
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    ".yaml": FileType.YAML,
    ".yml": FileType.YAML,
    ".json": FileType.JSON,
    ".txt": FileType.TEXT,
}


@dataclass
class FileInfo:
    """Information about a scanned file."""
    
    path: Path
    size: int
    file_type: FileType
    language: Optional[str] = None
    encoding: str = "utf-8"
    is_binary: bool = False
    
    @property
    def relative_path(self) -> Path:
        """Get path relative to the repository root."""
        # This will be set by the scanner
        return self.path
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()
    
    def should_index(self) -> bool:
        """Check if file should be indexed."""
        if self.is_binary:
            return False
        if self.file_type == FileType.UNKNOWN:
            return False
        # Skip very large files (>1MB)
        if self.size > 1024 * 1024:
            return False
        return True
    
    @classmethod
    def from_path(cls, path: Path) -> "FileInfo":
        """Create FileInfo from a file path."""
        try:
            stat = path.stat()
            size = stat.st_size
        except OSError:
            size = 0
        
        # Determine file type
        extension = path.suffix.lower()
        file_type = EXTENSION_MAP.get(extension, FileType.UNKNOWN)
        
        # Check if binary
        is_binary = False
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type and not mime_type.startswith("text/"):
            is_binary = True
        
        # For unknown types, check if it's text
        if file_type == FileType.UNKNOWN and not is_binary:
            try:
                # Try to read first few bytes to check if text
                with open(path, "rb") as f:
                    chunk = f.read(512)
                    if b'\0' not in chunk:
                        # Likely text file
                        file_type = FileType.TEXT
                    else:
                        is_binary = True
            except Exception:
                pass
        
        return cls(
            path=path,
            size=size,
            file_type=file_type,
            is_binary=is_binary
        )