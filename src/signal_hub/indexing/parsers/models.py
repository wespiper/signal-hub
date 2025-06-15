"""Data models for parsed code chunks."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path


class ChunkType(Enum):
    """Types of code chunks that can be extracted."""
    
    # Code structures
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    
    # Documentation
    DOCSTRING = "docstring"
    COMMENT = "comment"
    
    # Markdown
    HEADING = "heading"
    SECTION = "section"
    CODE_BLOCK = "code_block"
    
    # Generic
    BLOCK = "block"
    IMPORT = "import"
    EXPORT = "export"
    VARIABLE = "variable"


@dataclass
class Chunk:
    """A meaningful chunk of code or documentation."""
    
    type: ChunkType
    name: str
    content: str
    start_line: int
    end_line: int
    file_path: Optional[Path] = None
    language: Optional[str] = None
    parent: Optional[str] = None  # Parent chunk name (e.g., class for methods)
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def line_count(self) -> int:
        """Number of lines in the chunk."""
        return self.end_line - self.start_line + 1
    
    @property
    def identifier(self) -> str:
        """Unique identifier for the chunk."""
        parts = []
        
        if self.file_path:
            parts.append(str(self.file_path))
        
        if self.parent:
            parts.append(self.parent)
        
        parts.append(self.name)
        parts.append(f"L{self.start_line}")
        
        return "::".join(parts)
    
    def to_context_string(self) -> str:
        """Convert chunk to a context string for embedding."""
        lines = []
        
        # Add file context
        if self.file_path:
            lines.append(f"File: {self.file_path}")
        
        # Add location context  
        lines.append(f"Lines {self.start_line}-{self.end_line}")
        
        # Add type and name
        if self.parent:
            lines.append(f"{self.type.value}: {self.parent}.{self.name}")
        else:
            lines.append(f"{self.type.value}: {self.name}")
        
        # Add content
        lines.append("")
        lines.append(self.content)
        
        return "\n".join(lines)
    
    def overlaps(self, other: "Chunk") -> bool:
        """Check if this chunk overlaps with another."""
        if self.file_path != other.file_path:
            return False
        
        return not (self.end_line < other.start_line or 
                   self.start_line > other.end_line)