"""Base metadata extractor interface."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Type

from signal_hub.indexing.metadata.models import CodeMetadata, FileMetadata, MetadataType

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for language-specific metadata extractors."""
    
    @abstractmethod
    def can_extract(self, file_path: Path) -> bool:
        """Check if this extractor can handle the file."""
        pass
        
    @abstractmethod
    def extract(self, file_path: Path, content: str, metadata_type: MetadataType) -> CodeMetadata:
        """Extract metadata from file content."""
        pass


class MetadataExtractor:
    """Main metadata extraction coordinator."""
    
    def __init__(self):
        """Initialize metadata extractor."""
        self._extractors: Dict[str, BaseExtractor] = {}
        self._register_extractors()
        
    def _register_extractors(self):
        """Register language-specific extractors."""
        # Import here to avoid circular imports
        from signal_hub.indexing.metadata.extractors.python import PythonExtractor
        from signal_hub.indexing.metadata.extractors.javascript import JavaScriptExtractor
        
        self._extractors["python"] = PythonExtractor()
        self._extractors["javascript"] = JavaScriptExtractor()
        
    def extract(self, file_path: Path, metadata_type: MetadataType = MetadataType.FULL) -> CodeMetadata:
        """Extract metadata from a file.
        
        Args:
            file_path: Path to the file
            metadata_type: Level of metadata extraction
            
        Returns:
            Extracted code metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode {file_path} as UTF-8, trying latin-1")
            content = file_path.read_text(encoding="latin-1")
            
        # Get file metadata
        stat = file_path.stat()
        file_metadata = FileMetadata(
            path=file_path,
            language=self._detect_language(file_path),
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            encoding="utf-8",
            line_count=content.count('\n') + 1
        )
        
        # Find appropriate extractor
        for lang, extractor in self._extractors.items():
            if extractor.can_extract(file_path):
                try:
                    return extractor.extract(file_path, content, metadata_type)
                except Exception as e:
                    logger.error(f"Failed to extract metadata from {file_path}: {e}")
                    # Fall through to create basic metadata
                    break
                    
        # Return basic file metadata if no extractor matches or extraction fails
        return CodeMetadata(
            file=file_metadata,
            metadata_type=MetadataType.MINIMAL
        )
        
    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        extension_map = {
            ".py": "python",
            ".pyi": "python",
            ".js": "javascript",
            ".mjs": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".m": "matlab",
            ".jl": "julia",
            ".lua": "lua",
            ".pl": "perl",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".fish": "shell",
            ".ps1": "powershell",
            ".md": "markdown",
            ".rst": "restructuredtext",
            ".tex": "latex",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, "unknown")