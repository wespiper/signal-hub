"""Models for context assembly."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class RelationshipType(str, Enum):
    """Types of relationships between code entities."""
    
    CALLS = "calls"
    IMPORTS = "imports"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    USES = "uses"
    DEFINES = "defines"
    REFERENCES = "references"


@dataclass
class CodeRelationship:
    """Relationship between code entities."""
    
    from_entity: str
    to_entity: str
    relationship_type: RelationshipType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.from_entity} {self.relationship_type.value} {self.to_entity}"


@dataclass
class ContextSection:
    """A section of assembled context."""
    
    content: str
    source_file: str
    start_line: int
    end_line: int
    content_type: str  # function, class, imports, etc.
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    
    @property
    def location(self) -> str:
        """Get formatted location."""
        return f"{self.source_file}:{self.start_line}-{self.end_line}"
        
    @property
    def token_estimate(self) -> int:
        """Estimate token count for this section."""
        # Rough estimate: 1 token per 4 characters
        return len(self.content) // 4


@dataclass
class AssembledContext:
    """Assembled context from search results."""
    
    sections: List[ContextSection]
    relationships: List[CodeRelationship]
    query: str
    token_count: int
    format_style: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_text(self) -> str:
        """Convert to formatted text."""
        if self.format_style == "claude_optimized":
            return self._format_claude_optimized()
        elif self.format_style == "markdown":
            return self._format_markdown()
        else:
            return self._format_plain()
            
    def _format_claude_optimized(self) -> str:
        """Format optimized for Claude."""
        parts = []
        
        # Add summary if available
        if self.summary:
            parts.append(f"## Context Summary\n{self.summary}\n")
            
        # Add relationships if any
        if self.relationships:
            parts.append("## Code Relationships")
            for rel in self.relationships:
                parts.append(f"- {rel}")
            parts.append("")
            
        # Add sections grouped by file
        file_groups = {}
        for section in self.sections:
            if section.source_file not in file_groups:
                file_groups[section.source_file] = []
            file_groups[section.source_file].append(section)
            
        for file_path, sections in file_groups.items():
            parts.append(f"## {file_path}")
            
            for section in sections:
                if section.title:
                    parts.append(f"### {section.title}")
                    
                parts.append(f"Lines {section.start_line}-{section.end_line}:")
                parts.append("```")
                parts.append(section.content)
                parts.append("```")
                parts.append("")
                
        return "\n".join(parts)
        
    def _format_markdown(self) -> str:
        """Format as markdown."""
        parts = []
        
        # Header
        parts.append(f"# Code Context for: {self.query}")
        parts.append(f"*{len(self.sections)} relevant sections found*\n")
        
        # Sections
        for i, section in enumerate(self.sections, 1):
            parts.append(f"## {i}. {section.source_file} ({section.content_type})")
            parts.append(f"*Lines {section.start_line}-{section.end_line} (relevance: {section.score:.2f})*\n")
            parts.append("```")
            parts.append(section.content)
            parts.append("```\n")
            
        return "\n".join(parts)
        
    def _format_plain(self) -> str:
        """Format as plain text."""
        parts = []
        
        for section in self.sections:
            parts.append(f"=== {section.location} ===")
            parts.append(section.content)
            parts.append("")
            
        return "\n".join(parts)


@dataclass
class AssemblyConfig:
    """Configuration for context assembly."""
    
    max_tokens: int = 8000
    dedup_threshold: float = 0.85
    preserve_relationships: bool = True
    include_imports: bool = True
    include_context_headers: bool = True
    group_by_file: bool = True
    prioritize_definitions: bool = True
    format_style: str = "claude_optimized"
    min_score_threshold: float = 0.3
    relationship_confidence_threshold: float = 0.7
    
    def validate(self):
        """Validate configuration."""
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not 0 <= self.dedup_threshold <= 1:
            raise ValueError("dedup_threshold must be between 0 and 1")
        if self.format_style not in ["claude_optimized", "markdown", "plain"]:
            raise ValueError(f"Unknown format_style: {self.format_style}")