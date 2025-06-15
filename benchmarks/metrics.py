"""Performance metrics definitions."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    # Indexing metrics
    files_per_minute: float = 0.0
    chunks_per_second: float = 0.0
    embeddings_per_second: float = 0.0
    indexing_memory_mb: float = 0.0
    
    # Search metrics
    search_latency_p50_ms: float = 0.0
    search_latency_p95_ms: float = 0.0
    search_latency_p99_ms: float = 0.0
    queries_per_second: float = 0.0
    search_accuracy: float = 0.0
    
    # Routing metrics
    routing_decision_us: float = 0.0  # microseconds
    cache_hit_rate: float = 0.0
    model_distribution: Dict[str, float] = None
    routing_accuracy: float = 0.0
    
    # Resource usage
    cpu_usage_avg: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_mb_per_sec: float = 0.0
    api_calls_count: int = 0
    
    # Cost metrics
    total_cost_usd: float = 0.0
    cost_per_query_usd: float = 0.0
    savings_percentage: float = 0.0
    cache_savings_usd: float = 0.0
    
    def __post_init__(self):
        if self.model_distribution is None:
            self.model_distribution = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "indexing": {
                "files_per_minute": self.files_per_minute,
                "chunks_per_second": self.chunks_per_second,
                "embeddings_per_second": self.embeddings_per_second,
                "memory_mb": self.indexing_memory_mb,
            },
            "search": {
                "latency_p50_ms": self.search_latency_p50_ms,
                "latency_p95_ms": self.search_latency_p95_ms,
                "latency_p99_ms": self.search_latency_p99_ms,
                "qps": self.queries_per_second,
                "accuracy": self.search_accuracy,
            },
            "routing": {
                "decision_us": self.routing_decision_us,
                "cache_hit_rate": self.cache_hit_rate,
                "model_distribution": self.model_distribution,
                "accuracy": self.routing_accuracy,
            },
            "resources": {
                "cpu_avg": self.cpu_usage_avg,
                "memory_mb": self.memory_usage_mb,
                "disk_io_mb_sec": self.disk_io_mb_per_sec,
                "api_calls": self.api_calls_count,
            },
            "costs": {
                "total_usd": self.total_cost_usd,
                "per_query_usd": self.cost_per_query_usd,
                "savings_pct": self.savings_percentage,
                "cache_savings_usd": self.cache_savings_usd,
            },
        }
    
    def validate_targets(self) -> Dict[str, bool]:
        """
        Validate against performance targets.
        
        Returns:
            Dict of metric -> pass/fail
        """
        targets = {
            "indexing_speed": self.files_per_minute >= 1000,
            "search_latency": self.search_latency_p95_ms < 2000,
            "embedding_rate": self.embeddings_per_second >= 16.67,  # 1000/min
            "cache_hit_rate": self.cache_hit_rate >= 0.4,
            "memory_usage": self.memory_usage_mb < 1000,
            "concurrent_queries": self.queries_per_second >= 100,
        }
        
        return targets
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        passed = self.validate_targets()
        pass_count = sum(1 for v in passed.values() if v)
        
        summary = f"""
Performance Summary
==================

Indexing Performance:
- Files/minute: {self.files_per_minute:.1f} {'✅' if passed['indexing_speed'] else '❌'}
- Embeddings/second: {self.embeddings_per_second:.1f} {'✅' if passed['embedding_rate'] else '❌'}

Search Performance:
- P95 Latency: {self.search_latency_p95_ms:.0f}ms {'✅' if passed['search_latency'] else '❌'}
- Queries/second: {self.queries_per_second:.1f} {'✅' if passed['concurrent_queries'] else '❌'}

Caching & Routing:
- Cache Hit Rate: {self.cache_hit_rate*100:.1f}% {'✅' if passed['cache_hit_rate'] else '❌'}
- Routing Decision: {self.routing_decision_us:.0f}μs

Resource Usage:
- Memory: {self.memory_usage_mb:.0f}MB {'✅' if passed['memory_usage'] else '❌'}
- CPU: {self.cpu_usage_avg:.1f}%

Cost Optimization:
- Savings: {self.savings_percentage:.1f}%
- Cost/query: ${self.cost_per_query_usd:.4f}

Overall: {pass_count}/{len(passed)} targets met
"""
        return summary.strip()