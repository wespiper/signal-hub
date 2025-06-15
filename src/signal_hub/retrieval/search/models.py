"""Models for semantic search."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class SearchMode(str, Enum):
    """Search mode options."""
    
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class SearchQuery:
    """Query for semantic search."""
    
    text: str
    limit: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)
    mode: SearchMode = SearchMode.SEMANTIC
    include_metadata: bool = True
    include_scores: bool = True
    boost_recent: bool = False
    language_filter: Optional[str] = None
    file_pattern: Optional[str] = None
    
    def __post_init__(self):
        """Validate query parameters."""
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.limit > 1000:
            raise ValueError("Limit cannot exceed 1000")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "limit": self.limit,
            "filters": self.filters,
            "mode": self.mode.value,
            "include_metadata": self.include_metadata,
            "include_scores": self.include_scores,
            "boost_recent": self.boost_recent,
            "language_filter": self.language_filter,
            "file_pattern": self.file_pattern
        }


@dataclass
class SearchResult:
    """Result from semantic search."""
    
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: Optional[str] = None
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    chunk_type: Optional[str] = None
    highlights: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Extract common fields from metadata."""
        if self.metadata:
            self.file_path = self.metadata.get("file_path", self.file_path)
            self.start_line = self.metadata.get("start_line", self.start_line)
            self.end_line = self.metadata.get("end_line", self.end_line)
            self.chunk_type = self.metadata.get("chunk_type", self.chunk_type)
            
    @property
    def location(self) -> str:
        """Get formatted location string."""
        if self.file_path:
            if self.start_line:
                return f"{self.file_path}:{self.start_line}"
            return self.file_path
        return "unknown"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "score": self.score,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id,
            "location": self.location,
            "highlights": self.highlights
        }


@dataclass
class SearchConfig:
    """Configuration for semantic search."""
    
    similarity_threshold: float = 0.3
    max_results: int = 100
    rerank_results: bool = True
    use_metadata_boost: bool = True
    keyword_weight: float = 0.3  # For hybrid search
    recency_weight: float = 0.1
    chunk_overlap_penalty: float = 0.5
    enable_caching: bool = True
    cache_ttl: int = 3600
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if not 0 <= self.keyword_weight <= 1:
            raise ValueError("keyword_weight must be between 0 and 1")
        if not 0 <= self.recency_weight <= 1:
            raise ValueError("recency_weight must be between 0 and 1")