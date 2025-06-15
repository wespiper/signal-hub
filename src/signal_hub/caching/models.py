"""Data models for semantic caching."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class CacheEntryStatus(str, Enum):
    """Status of cache entries."""
    ACTIVE = "active"
    EXPIRED = "expired"
    EVICTED = "evicted"


@dataclass
class CachedResponse:
    """A cached response with metadata."""
    id: str
    query: str
    query_embedding: List[float]
    response: Dict[str, Any]
    model: str
    timestamp: datetime
    ttl_seconds: int
    hit_count: int = 0
    last_accessed: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: CacheEntryStatus = CacheEntryStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.status != CacheEntryStatus.ACTIVE:
            return True
            
        age_seconds = (datetime.utcnow() - self.timestamp).total_seconds()
        return age_seconds > self.ttl_seconds
        
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.utcnow() - self.timestamp).total_seconds()
        
    def record_hit(self):
        """Record a cache hit."""
        self.hit_count += 1
        self.last_accessed = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "query": self.query,
            "query_embedding": self.query_embedding,
            "response": self.response,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "context": self.context,
            "metadata": self.metadata,
            "status": self.status.value
        }


@dataclass
class CacheSearchResult:
    """Result from cache similarity search."""
    entry: CachedResponse
    similarity_score: float
    
    @property
    def is_valid(self) -> bool:
        """Check if result is valid (not expired)."""
        return not self.entry.is_expired


@dataclass
class CacheConfig:
    """Configuration for semantic cache."""
    enabled: bool = True
    similarity_threshold: float = 0.85
    ttl_hours: int = 24
    max_entries: int = 10000
    max_memory_mb: int = 1000
    storage_backend: str = "memory"  # or "persistent"
    context_aware: bool = True
    eviction_strategy: str = "lru"  # or "ttl", "quality"
    
    @property
    def ttl_seconds(self) -> int:
        """Get TTL in seconds."""
        return self.ttl_hours * 3600
        
    def validate(self):
        """Validate configuration."""
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between 0 and 1")
            
        if self.ttl_hours <= 0:
            raise ValueError("ttl_hours must be positive")
            
        if self.max_entries <= 0:
            raise ValueError("max_entries must be positive")
            
        if self.storage_backend not in ["memory", "persistent"]:
            raise ValueError("storage_backend must be 'memory' or 'persistent'")


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_entries: int = 0
    memory_usage_mb: float = 0.0
    evictions: int = 0
    average_similarity: float = 0.0
    average_response_time_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_queries == 0:
            return 0.0
        return (self.cache_hits / self.total_queries) * 100
        
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 100.0 - self.hit_rate
        
    def record_hit(self, similarity: float, response_time_ms: float):
        """Record a cache hit."""
        self.total_queries += 1
        self.cache_hits += 1
        self._update_averages(similarity, response_time_ms)
        
    def record_miss(self, response_time_ms: float):
        """Record a cache miss."""
        self.total_queries += 1
        self.cache_misses += 1
        self._update_response_time(response_time_ms)
        
    def _update_averages(self, similarity: float, response_time_ms: float):
        """Update running averages."""
        # Update similarity average
        if self.cache_hits == 1:
            self.average_similarity = similarity
        else:
            total = self.average_similarity * (self.cache_hits - 1)
            self.average_similarity = (total + similarity) / self.cache_hits
            
        self._update_response_time(response_time_ms)
        
    def _update_response_time(self, response_time_ms: float):
        """Update average response time."""
        if self.total_queries == 1:
            self.average_response_time_ms = response_time_ms
        else:
            total = self.average_response_time_ms * (self.total_queries - 1)
            self.average_response_time_ms = (total + response_time_ms) / self.total_queries