"""Base parser interface for all language parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union
import logging

from signal_hub.indexing.parsers.models import Chunk


logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Error during parsing."""
    pass


class Parser(ABC):
    """Abstract base class for all file parsers."""
    
    # Language(s) this parser handles
    languages: List[str] = []
    
    # File extensions this parser handles
    extensions: List[str] = []
    
    def __init__(self, max_chunk_size: int = 1500):
        """Initialize the parser.
        
        Args:
            max_chunk_size: Maximum size of a chunk in characters
        """
        self.max_chunk_size = max_chunk_size
    
    @abstractmethod
    def parse(self, content: str, file_path: Optional[Path] = None) -> List[Chunk]:
        """Parse file content into chunks.
        
        Args:
            content: File content to parse
            file_path: Optional path for context
            
        Returns:
            List of extracted chunks
            
        Raises:
            ParseError: If parsing fails
        """
        pass
    
    def parse_file(self, file_path: Union[str, Path]) -> List[Chunk]:
        """Parse a file by reading its content.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            List of extracted chunks
            
        Raises:
            ParseError: If parsing fails
            IOError: If file cannot be read
        """
        file_path = Path(file_path)
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
        
        return self.parse(content, file_path)
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if parser can handle this file
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        return extension in self.extensions
    
    def split_large_chunk(self, chunk: Chunk) -> List[Chunk]:
        """Split a large chunk into smaller pieces if needed.
        
        Args:
            chunk: Chunk to potentially split
            
        Returns:
            List of chunks (original if small enough, split otherwise)
        """
        if len(chunk.content) <= self.max_chunk_size:
            return [chunk]
        
        # Split by lines while respecting max size
        lines = chunk.content.split('\n')
        chunks = []
        current_lines = []
        current_size = 0
        current_start = chunk.start_line
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > self.max_chunk_size and current_lines:
                # Create chunk from accumulated lines
                content = '\n'.join(current_lines)
                chunks.append(Chunk(
                    type=chunk.type,
                    name=f"{chunk.name}_part_{len(chunks) + 1}",
                    content=content,
                    start_line=current_start,
                    end_line=current_start + len(current_lines) - 1,
                    file_path=chunk.file_path,
                    language=chunk.language,
                    parent=chunk.parent,
                    metadata={**chunk.metadata, "split": True, "original": chunk.name}
                ))
                
                # Reset for next chunk
                current_lines = []
                current_size = 0
                current_start = chunk.start_line + i
            
            current_lines.append(line)
            current_size += line_size
        
        # Add remaining lines
        if current_lines:
            content = '\n'.join(current_lines)
            chunks.append(Chunk(
                type=chunk.type,
                name=f"{chunk.name}_part_{len(chunks) + 1}",
                content=content,
                start_line=current_start,
                end_line=chunk.end_line,
                file_path=chunk.file_path,
                language=chunk.language,
                parent=chunk.parent,
                metadata={**chunk.metadata, "split": True, "original": chunk.name}
            ))
        
        return chunks
    
    def clean_content(self, content: str) -> str:
        """Clean and normalize content.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        # Remove trailing whitespace from lines
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]
        
        # Remove excessive blank lines
        cleaned_lines = []
        blank_count = 0
        
        for line in lines:
            if not line:
                blank_count += 1
                if blank_count <= 2:  # Allow max 2 consecutive blank lines
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()