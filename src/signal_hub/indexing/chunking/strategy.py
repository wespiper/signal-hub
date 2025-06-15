"""Base chunking strategy interface and models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class ChunkType(str, Enum):
    """Type of code chunk."""
    
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    BLOCK = "block"
    DOCUMENTATION = "documentation"
    COMMENT = "comment"
    IMPORT = "import"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    
    content: str
    start_line: int
    end_line: int
    chunk_type: ChunkType = ChunkType.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional[str] = None
    overlap_with_previous: int = 0
    overlap_with_next: int = 0
    is_valid_syntax: Optional[bool] = None
    
    def __post_init__(self):
        """Validate chunk after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("Chunk content cannot be empty")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
            
    @property
    def size(self) -> int:
        """Get chunk size in characters."""
        return len(self.content)
        
    @property
    def line_count(self) -> int:
        """Get number of lines in chunk."""
        return self.end_line - self.start_line + 1
        
    def get_full_context(self) -> str:
        """Get full context including parent."""
        if self.parent_context:
            # Extract the main identifier from content
            if self.chunk_type in [ChunkType.FUNCTION, ChunkType.METHOD]:
                # Try to extract function/method name
                import re
                match = re.search(r'def\s+(\w+)', self.content)
                if match:
                    return f"{self.parent_context} > {match.group(1)}"
            elif self.chunk_type == ChunkType.CLASS:
                match = re.search(r'class\s+(\w+)', self.content)
                if match:
                    return f"{self.parent_context} > {match.group(1)}"
                    
        return self.parent_context or ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type.value,
            "metadata": self.metadata,
            "parent_context": self.parent_context,
            "size": self.size,
            "line_count": self.line_count
        }


@dataclass
class ChunkingContext:
    """Configuration for chunking strategy."""
    
    max_chunk_size: int = 1000
    min_chunk_size: int = 50
    overlap_size: int = 100
    preserve_context: bool = True
    include_imports: bool = True
    include_docstrings: bool = True
    syntax_validation: bool = True
    target_chunk_lines: int = 50
    
    def validate(self):
        """Validate configuration."""
        if self.max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")
        if self.min_chunk_size < 0:
            raise ValueError("min_chunk_size must be non-negative")
        if self.overlap_size < 0:
            raise ValueError("overlap_size must be non-negative")
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError("min_chunk_size cannot exceed max_chunk_size")


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    def __init__(self, context: Optional[ChunkingContext] = None):
        """Initialize chunking strategy.
        
        Args:
            context: Chunking configuration
        """
        self.context = context or ChunkingContext()
        self.context.validate()
        
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this strategy can handle the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if strategy can handle this file type
        """
        pass
        
    @abstractmethod
    def chunk_file(self, file_path: Path, content: Optional[str] = None) -> List[CodeChunk]:
        """Chunk a file into logical pieces.
        
        Args:
            file_path: Path to the file
            content: File content (if not provided, will be read)
            
        Returns:
            List of code chunks
        """
        pass
        
    @abstractmethod
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CodeChunk]:
        """Chunk text into logical pieces.
        
        Args:
            text: Text content to chunk
            metadata: Optional metadata about the text
            
        Returns:
            List of code chunks
        """
        pass
        
    def apply_overlap(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Apply overlap between chunks for context preservation.
        
        Args:
            chunks: Original chunks
            
        Returns:
            Chunks with overlap applied
        """
        if not self.context.preserve_context or self.context.overlap_size <= 0:
            return chunks
            
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Add overlap from previous chunk
            if i > 0 and self.context.overlap_size > 0:
                prev_lines = chunks[i-1].content.split('\n')
                overlap_lines = prev_lines[-self.context.overlap_size:]
                if overlap_lines:
                    chunk.content = '\n'.join(overlap_lines) + '\n' + chunk.content
                    chunk.overlap_with_previous = len('\n'.join(overlap_lines))
                    
            # Note overlap with next chunk
            if i < len(chunks) - 1 and self.context.overlap_size > 0:
                curr_lines = chunk.content.split('\n')
                overlap_size = min(len(curr_lines), self.context.overlap_size)
                chunk.overlap_with_next = len('\n'.join(curr_lines[-overlap_size:]))
                
            overlapped_chunks.append(chunk)
            
        return overlapped_chunks
        
    @staticmethod
    def for_language(language: str, context: Optional[ChunkingContext] = None) -> "ChunkingStrategy":
        """Factory method to get appropriate strategy for a language.
        
        Args:
            language: Programming language
            context: Chunking configuration
            
        Returns:
            Appropriate chunking strategy
        """
        from signal_hub.indexing.chunking.strategies import (
            PythonChunkingStrategy,
            JavaScriptChunkingStrategy,
            MarkdownChunkingStrategy,
            FallbackChunkingStrategy
        )
        
        strategies = {
            "python": PythonChunkingStrategy,
            "javascript": JavaScriptChunkingStrategy,
            "typescript": JavaScriptChunkingStrategy,
            "markdown": MarkdownChunkingStrategy,
        }
        
        strategy_class = strategies.get(language.lower(), FallbackChunkingStrategy)
        return strategy_class(context)