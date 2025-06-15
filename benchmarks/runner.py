"""Benchmark runner for Signal Hub performance testing."""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

from signal_hub.utils.logging import get_logger
from .metrics import PerformanceMetrics


logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    
    name: str
    category: str
    metrics: Dict[str, Any]
    duration_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "category": self.category,
            "metrics": self.metrics,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BenchmarkRunner:
    """Runs and manages performance benchmarks."""
    
    def __init__(self, output_dir: Path = Path("benchmark_results")):
        """
        Initialize benchmark runner.
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.benchmarks: Dict[str, Callable] = {}
        self.results: List[BenchmarkResult] = []
        
    def register(self, name: str, category: str = "general"):
        """
        Decorator to register a benchmark function.
        
        Args:
            name: Benchmark name
            category: Benchmark category
        """
        def decorator(func: Callable) -> Callable:
            self.benchmarks[name] = (func, category)
            return func
        return decorator
    
    async def run_benchmark(
        self,
        name: str,
        func: Callable,
        category: str,
        **kwargs
    ) -> BenchmarkResult:
        """
        Run a single benchmark.
        
        Args:
            name: Benchmark name
            func: Benchmark function
            category: Benchmark category
            **kwargs: Arguments for benchmark function
            
        Returns:
            Benchmark result
        """
        logger.info(f"Running benchmark: {name}")
        
        # Record system state before
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run benchmark
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(func):
                metrics = await func(**kwargs)
            else:
                metrics = func(**kwargs)
        except Exception as e:
            logger.error(f"Benchmark {name} failed: {e}")
            metrics = {"error": str(e)}
        
        duration = time.time() - start_time
        
        # Record system state after
        cpu_after = process.cpu_percent()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Add system metrics
        metrics.update({
            "cpu_usage_avg": (cpu_before + cpu_after) / 2,
            "memory_used_mb": memory_after - memory_before,
            "memory_peak_mb": memory_after,
        })
        
        result = BenchmarkResult(
            name=name,
            category=category,
            metrics=metrics,
            duration_seconds=duration,
            metadata={
                "python_version": psutil.version_info,
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            }
        )
        
        self.results.append(result)
        logger.info(f"Completed {name} in {duration:.2f}s")
        
        return result
    
    async def run_all(self, pattern: Optional[str] = None) -> List[BenchmarkResult]:
        """
        Run all registered benchmarks.
        
        Args:
            pattern: Optional pattern to filter benchmarks
            
        Returns:
            List of results
        """
        self.results.clear()
        
        for name, (func, category) in self.benchmarks.items():
            if pattern and pattern not in name:
                continue
                
            await self.run_benchmark(name, func, category)
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self) -> Path:
        """
        Save benchmark results to file.
        
        Returns:
            Path to saved results
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"benchmark_{timestamp}.json"
        
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": [r.to_dict() for r in self.results],
            "summary": self._generate_summary(),
        }
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved results to {output_file}")
        return output_file
    
    def _generate_summary(self) -> dict:
        """Generate summary statistics."""
        if not self.results:
            return {}
        
        summary = {
            "total_benchmarks": len(self.results),
            "total_duration": sum(r.duration_seconds for r in self.results),
            "by_category": {},
        }
        
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Summarize each category
        for category, results in categories.items():
            summary["by_category"][category] = {
                "count": len(results),
                "total_duration": sum(r.duration_seconds for r in results),
                "metrics": self._aggregate_metrics(results),
            }
        
        return summary
    
    def _aggregate_metrics(self, results: List[BenchmarkResult]) -> dict:
        """Aggregate metrics across results."""
        if not results:
            return {}
        
        # Collect all metric keys
        all_keys = set()
        for r in results:
            all_keys.update(r.metrics.keys())
        
        aggregated = {}
        for key in all_keys:
            values = []
            for r in results:
                if key in r.metrics and isinstance(r.metrics[key], (int, float)):
                    values.append(r.metrics[key])
            
            if values:
                aggregated[key] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
        
        return aggregated
    
    def compare_results(
        self,
        baseline_file: Path,
        current_file: Optional[Path] = None
    ) -> dict:
        """
        Compare benchmark results against baseline.
        
        Args:
            baseline_file: Path to baseline results
            current_file: Path to current results (uses latest if None)
            
        Returns:
            Comparison data
        """
        # Load baseline
        with open(baseline_file) as f:
            baseline = json.load(f)
        
        # Load current (or use latest)
        if current_file is None:
            current_files = sorted(self.output_dir.glob("benchmark_*.json"))
            if not current_files:
                raise ValueError("No benchmark results found")
            current_file = current_files[-1]
        
        with open(current_file) as f:
            current = json.load(f)
        
        # Compare results
        comparison = {
            "baseline_date": baseline["timestamp"],
            "current_date": current["timestamp"],
            "improvements": [],
            "regressions": [],
            "unchanged": [],
        }
        
        # Match results by name
        baseline_by_name = {r["name"]: r for r in baseline["results"]}
        current_by_name = {r["name"]: r for r in current["results"]}
        
        for name, current_result in current_by_name.items():
            if name not in baseline_by_name:
                continue
            
            baseline_result = baseline_by_name[name]
            
            # Compare key metrics
            for metric, current_value in current_result["metrics"].items():
                if metric not in baseline_result["metrics"]:
                    continue
                
                baseline_value = baseline_result["metrics"][metric]
                
                if isinstance(current_value, (int, float)) and isinstance(baseline_value, (int, float)):
                    change_pct = ((current_value - baseline_value) / baseline_value) * 100
                    
                    comparison_entry = {
                        "benchmark": name,
                        "metric": metric,
                        "baseline": baseline_value,
                        "current": current_value,
                        "change_pct": change_pct,
                    }
                    
                    # Categorize change
                    if abs(change_pct) < 5:
                        comparison["unchanged"].append(comparison_entry)
                    elif change_pct < 0:  # Lower is better for most metrics
                        comparison["improvements"].append(comparison_entry)
                    else:
                        comparison["regressions"].append(comparison_entry)
        
        return comparison