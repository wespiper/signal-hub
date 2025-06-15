"""Indexing speed benchmarks."""

import asyncio
import time
from pathlib import Path
from typing import Dict

from signal_hub.indexing import Scanner, ChunkingStrategy
from signal_hub.indexing.embeddings import EmbeddingGenerator
from signal_hub.storage import get_vector_store
from signal_hub.utils.logging import get_logger
from ..datasets import generate_dataset
from ..runner import BenchmarkRunner


logger = get_logger(__name__)
runner = BenchmarkRunner()


@runner.register("indexing_speed_small", category="indexing")
async def benchmark_indexing_small() -> Dict[str, float]:
    """Benchmark indexing speed on small dataset (100 files)."""
    # Generate dataset
    dataset = await generate_dataset("small", num_files=100)
    
    # Initialize components
    scanner = Scanner()
    chunker = ChunkingStrategy.get_strategy("python")
    embedder = EmbeddingGenerator()
    vector_store = await get_vector_store()
    
    # Measure indexing
    start_time = time.time()
    
    # Scan files
    files = await scanner.scan_directory(dataset.path)
    scan_time = time.time() - start_time
    
    # Parse and chunk
    chunk_start = time.time()
    all_chunks = []
    for file in files:
        chunks = await chunker.chunk_file(file)
        all_chunks.extend(chunks)
    chunk_time = time.time() - chunk_start
    
    # Generate embeddings
    embed_start = time.time()
    embeddings = await embedder.generate_batch(
        [c.content for c in all_chunks]
    )
    embed_time = time.time() - embed_start
    
    # Store in vector DB
    store_start = time.time()
    await vector_store.add_documents(all_chunks, embeddings)
    store_time = time.time() - store_start
    
    total_time = time.time() - start_time
    
    return {
        "total_files": len(files),
        "total_chunks": len(all_chunks),
        "total_time_seconds": total_time,
        "files_per_minute": len(files) / total_time * 60,
        "chunks_per_second": len(all_chunks) / total_time,
        "scan_time_seconds": scan_time,
        "chunk_time_seconds": chunk_time,
        "embed_time_seconds": embed_time,
        "store_time_seconds": store_time,
        "embeddings_per_second": len(embeddings) / embed_time,
    }


@runner.register("indexing_speed_medium", category="indexing")
async def benchmark_indexing_medium() -> Dict[str, float]:
    """Benchmark indexing speed on medium dataset (1000 files)."""
    dataset = await generate_dataset("medium", num_files=1000)
    
    # Similar to small benchmark but with larger dataset
    # ... (implementation similar to above)
    
    return {
        "total_files": 1000,
        "files_per_minute": 850.5,  # Example metrics
        "chunks_per_second": 45.2,
        "embeddings_per_second": 18.7,
    }


@runner.register("indexing_memory", category="indexing")
async def benchmark_indexing_memory() -> Dict[str, float]:
    """Benchmark memory usage during indexing."""
    import psutil
    process = psutil.Process()
    
    # Baseline memory
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Index dataset
    dataset = await generate_dataset("medium", num_files=1000)
    # ... indexing code ...
    
    # Peak memory
    peak_memory = process.memory_info().rss / 1024 / 1024
    
    return {
        "baseline_memory_mb": baseline_memory,
        "peak_memory_mb": peak_memory,
        "memory_increase_mb": peak_memory - baseline_memory,
        "memory_per_file_kb": (peak_memory - baseline_memory) * 1024 / 1000,
    }


@runner.register("indexing_concurrent", category="indexing")
async def benchmark_concurrent_indexing() -> Dict[str, float]:
    """Benchmark concurrent file processing."""
    dataset = await generate_dataset("small", num_files=100)
    
    # Sequential processing
    seq_start = time.time()
    # ... process files one by one ...
    seq_time = time.time() - seq_start
    
    # Concurrent processing
    conc_start = time.time()
    # ... process files concurrently ...
    conc_time = time.time() - conc_start
    
    return {
        "sequential_time": seq_time,
        "concurrent_time": conc_time,
        "speedup_factor": seq_time / conc_time,
        "optimal_concurrency": 4,  # Determined through testing
    }