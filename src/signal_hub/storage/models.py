"""Data models for vector storage."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class Document:
    """Document to store in vector database."""
    
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> "Document":
        """Create a new document.
        
        Args:
            content: Document content
            embedding: Embedding vector
            metadata: Optional metadata
            doc_id: Optional document ID
            
        Returns:
            New Document instance
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        if metadata is None:
            metadata = {}
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        return cls(
            id=doc_id,
            content=content,
            embedding=embedding,
            metadata=metadata
        )


@dataclass
class QueryResult:
    """Result from a vector query."""
    
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float
    score: Optional[float] = None
    
    @property
    def similarity(self) -> float:
        """Get similarity score (1 - distance for cosine)."""
        if self.score is not None:
            return self.score
        # Convert distance to similarity
        # For cosine distance, similarity = 1 - distance
        return max(0.0, 1.0 - self.distance)


@dataclass
class CollectionMetadata:
    """Metadata for a collection."""
    
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    document_count: int = 0
    dimension: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "document_count": self.document_count,
            "dimension": self.dimension,
            **self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollectionMetadata":
        """Create from dictionary."""
        # Extract known fields
        name = data.pop("name")
        description = data.pop("description", None)
        created_at = data.pop("created_at", None)
        updated_at = data.pop("updated_at", None)
        document_count = data.pop("document_count", 0)
        dimension = data.pop("dimension", None)
        
        # Parse dates
        if created_at:
            created_at = datetime.fromisoformat(created_at)
        if updated_at:
            updated_at = datetime.fromisoformat(updated_at)
        
        # Remaining fields go to metadata
        return cls(
            name=name,
            description=description,
            created_at=created_at,
            updated_at=updated_at,
            document_count=document_count,
            dimension=dimension,
            metadata=data
        )


@dataclass
class QueryFilter:
    """Filter for vector queries."""
    
    where: Optional[Dict[str, Any]] = None
    where_document: Optional[Dict[str, Any]] = None
    
    def to_chroma_format(self) -> Dict[str, Any]:
        """Convert to ChromaDB query format."""
        result = {}
        
        if self.where:
            result["where"] = self.where
        
        if self.where_document:
            result["where_document"] = self.where_document
        
        return result