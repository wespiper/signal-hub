"""Metrics collection for Signal Hub monitoring."""

import time
from typing import Dict, Optional, List, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import threading
import asyncio
from contextlib import contextmanager


@dataclass
class Metric:
    """Base metric class."""
    
    name: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: float = field(default_factory=time.time)


class Counter:
    """A metric that only increases."""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def inc(self, amount: float = 1.0, **label_values) -> None:
        """Increment the counter."""
        if amount < 0:
            raise ValueError("Counter can only increase")
        
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            self._values[labels_key] += amount
    
    def get(self, **label_values) -> float:
        """Get current value."""
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            return self._values[labels_key]
    
    def _make_labels_key(self, label_values: Dict[str, str]) -> str:
        """Create a key from label values."""
        return ",".join(f"{k}={v}" for k, v in sorted(label_values.items()))
    
    def collect(self) -> List[Metric]:
        """Collect all metrics."""
        metrics = []
        with self._lock:
            for labels_key, value in self._values.items():
                labels = dict(item.split("=") for item in labels_key.split(",")) if labels_key else {}
                metrics.append(Metric(name=self.name, labels=labels, value=value))
        return metrics


class Gauge:
    """A metric that can go up or down."""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def set(self, value: float, **label_values) -> None:
        """Set the gauge value."""
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            self._values[labels_key] = value
    
    def inc(self, amount: float = 1.0, **label_values) -> None:
        """Increment the gauge."""
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            self._values[labels_key] += amount
    
    def dec(self, amount: float = 1.0, **label_values) -> None:
        """Decrement the gauge."""
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            self._values[labels_key] -= amount
    
    def get(self, **label_values) -> float:
        """Get current value."""
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            return self._values[labels_key]
    
    def _make_labels_key(self, label_values: Dict[str, str]) -> str:
        """Create a key from label values."""
        return ",".join(f"{k}={v}" for k, v in sorted(label_values.items()))
    
    def collect(self) -> List[Metric]:
        """Collect all metrics."""
        metrics = []
        with self._lock:
            for labels_key, value in self._values.items():
                labels = dict(item.split("=") for item in labels_key.split(",")) if labels_key else {}
                metrics.append(Metric(name=self.name, labels=labels, value=value))
        return metrics


class Histogram:
    """A metric that tracks distributions."""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None,
                 buckets: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._values: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def observe(self, value: float, **label_values) -> None:
        """Record an observation."""
        labels_key = self._make_labels_key(label_values)
        with self._lock:
            self._values[labels_key].append(value)
    
    @contextmanager
    def time(self, **label_values):
        """Context manager to time an operation."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe(duration, **label_values)
    
    def _make_labels_key(self, label_values: Dict[str, str]) -> str:
        """Create a key from label values."""
        return ",".join(f"{k}={v}" for k, v in sorted(label_values.items()))
    
    def collect(self) -> List[Metric]:
        """Collect all metrics."""
        metrics = []
        with self._lock:
            for labels_key, values in self._values.items():
                if not values:
                    continue
                
                labels = dict(item.split("=") for item in labels_key.split(",")) if labels_key else {}
                sorted_values = sorted(values)
                
                # Calculate statistics
                count = len(values)
                sum_value = sum(values)
                
                # Bucket counts
                bucket_counts = []
                for bucket in self.buckets:
                    bucket_count = sum(1 for v in values if v <= bucket)
                    bucket_counts.append((bucket, bucket_count))
                
                # Add metrics
                metrics.append(Metric(name=f"{self.name}_count", labels=labels, value=count))
                metrics.append(Metric(name=f"{self.name}_sum", labels=labels, value=sum_value))
                
                # Add bucket metrics
                for bucket, count in bucket_counts:
                    bucket_labels = labels.copy()
                    bucket_labels["le"] = str(bucket)
                    metrics.append(Metric(name=f"{self.name}_bucket", labels=bucket_labels, value=count))
        
        return metrics


class MetricsCollector:
    """Central metrics collector."""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def register(self, metric: Any) -> None:
        """Register a metric."""
        with self._lock:
            self._metrics[metric.name] = metric
    
    def unregister(self, name: str) -> None:
        """Unregister a metric."""
        with self._lock:
            self._metrics.pop(name, None)
    
    def collect_all(self) -> List[Metric]:
        """Collect all metrics."""
        all_metrics = []
        with self._lock:
            for metric in self._metrics.values():
                if hasattr(metric, "collect"):
                    all_metrics.extend(metric.collect())
        return all_metrics
    
    def format_prometheus(self) -> str:
        """Format metrics in Prometheus format."""
        lines = []
        metrics = self.collect_all()
        
        # Group by metric name
        grouped = defaultdict(list)
        for metric in metrics:
            grouped[metric.name].append(metric)
        
        for name, metric_list in grouped.items():
            # Add help and type (simplified)
            lines.append(f"# HELP {name} {name}")
            lines.append(f"# TYPE {name} gauge")
            
            # Add metric values
            for metric in metric_list:
                labels_str = ""
                if metric.labels:
                    label_parts = [f'{k}="{v}"' for k, v in metric.labels.items()]
                    labels_str = "{" + ",".join(label_parts) + "}"
                
                lines.append(f"{name}{labels_str} {metric.value}")
        
        return "\n".join(lines)


# Global metrics collector
_collector = MetricsCollector()


# Pre-defined metrics
request_counter = Counter(
    "signal_hub_requests_total",
    "Total number of requests",
    labels=["method", "status"]
)
_collector.register(request_counter)

request_duration = Histogram(
    "signal_hub_request_duration_seconds",
    "Request duration in seconds",
    labels=["method", "status"]
)
_collector.register(request_duration)

active_connections = Gauge(
    "signal_hub_active_connections",
    "Number of active connections"
)
_collector.register(active_connections)

embeddings_generated = Counter(
    "signal_hub_embeddings_generated_total",
    "Total embeddings generated",
    labels=["provider", "model"]
)
_collector.register(embeddings_generated)

embedding_duration = Histogram(
    "signal_hub_embedding_duration_seconds",
    "Embedding generation duration",
    labels=["provider", "model"]
)
_collector.register(embedding_duration)

vector_queries = Counter(
    "signal_hub_vector_queries_total",
    "Total vector queries",
    labels=["collection", "status"]
)
_collector.register(vector_queries)

query_duration = Histogram(
    "signal_hub_query_duration_seconds",
    "Query duration in seconds",
    labels=["collection", "operation"]
)
_collector.register(query_duration)

cache_hits = Counter(
    "signal_hub_cache_hits_total",
    "Total cache hits",
    labels=["cache_type"]
)
_collector.register(cache_hits)

cache_misses = Counter(
    "signal_hub_cache_misses_total",
    "Total cache misses",
    labels=["cache_type"]
)
_collector.register(cache_misses)

error_counter = Counter(
    "signal_hub_errors_total",
    "Total errors",
    labels=["type", "operation"]
)
_collector.register(error_counter)


def get_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _collector


def track_request(method: str, status: int) -> None:
    """Track a request."""
    request_counter.inc(method=method, status=str(status))


def track_error(error_type: str, operation: str) -> None:
    """Track an error."""
    error_counter.inc(type=error_type, operation=operation)


async def export_metrics() -> str:
    """Export metrics in Prometheus format."""
    return _collector.format_prometheus()