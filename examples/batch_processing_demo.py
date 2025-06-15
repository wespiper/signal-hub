#!/usr/bin/env python3
"""Demonstration of batch processing performance improvements."""

import asyncio
import time
from pathlib import Path

from signal_hub.indexing.embeddings import (
    EmbeddingService,
    BatchEmbeddingProcessor,
    SmartBatcher
)
from signal_hub.indexing.scanner import CodebaseScanner
from signal_hub.indexing.parsers import ParserRegistry


async def demonstrate_batch_processing():
    """Demonstrate batch processing capabilities."""
    print("=== Signal Hub Batch Processing Demo ===\n")
    
    # Initialize components
    embedding_service = EmbeddingService()
    scanner = CodebaseScanner()
    parser_registry = ParserRegistry()
    
    # Scan a sample codebase
    print("1. Scanning codebase...")
    codebase_path = Path(".")  # Current directory
    files = await scanner.scan_directory(codebase_path)
    print(f"   Found {len(files)} files")
    
    # Parse files and extract chunks
    print("\n2. Parsing files and extracting chunks...")
    all_chunks = []
    
    for file_path in files[:50]:  # Limit to first 50 files for demo
        try:
            parser = parser_registry.get_parser(file_path)
            if parser:
                parsed = await parser.parse(file_path)
                chunks = parsed.chunks
                all_chunks.extend([chunk.content for chunk in chunks])
        except Exception as e:
            continue
            
    print(f"   Extracted {len(all_chunks)} chunks")
    
    if not all_chunks:
        print("   No chunks found. Using sample data...")
        all_chunks = [f"Sample chunk {i}: This is a test chunk with some code content." 
                     for i in range(1000)]
    
    # Demonstrate smart batching
    print("\n3. Smart Batching Demo")
    smart_batcher = SmartBatcher(max_tokens=2000)
    batches = smart_batcher.create_batches(all_chunks[:100])
    print(f"   Created {len(batches)} batches from 100 chunks")
    for i, batch in enumerate(batches[:3]):
        print(f"   Batch {i}: {len(batch)} chunks")
    
    # Compare processing methods
    print("\n4. Performance Comparison")
    
    # Method 1: Non-batched (simulated)
    print("\n   a) Non-batched processing (simulated):")
    non_batched_time = len(all_chunks) * 0.05  # Assume 50ms per chunk
    print(f"      Estimated time: {non_batched_time:.2f} seconds")
    print(f"      Estimated rate: {len(all_chunks) / non_batched_time:.2f} chunks/second")
    
    # Method 2: Basic batching
    print("\n   b) Basic batch processing:")
    processor = BatchEmbeddingProcessor(
        embedding_service=embedding_service,
        batch_size=100,
        max_concurrent_batches=1
    )
    
    start_time = time.time()
    progress = None
    async for progress in processor.process_with_progress(all_chunks[:200]):
        pass
    basic_time = time.time() - start_time
    
    print(f"      Actual time: {basic_time:.2f} seconds")
    print(f"      Actual rate: {progress.rate:.2f} chunks/second")
    
    # Method 3: Optimized concurrent batching
    print("\n   c) Optimized concurrent batch processing:")
    optimized_processor = BatchEmbeddingProcessor(
        embedding_service=embedding_service,
        batch_size=100,
        max_concurrent_batches=5,
        max_retries=3
    )
    
    start_time = time.time()
    progress_updates = []
    
    async for progress in optimized_processor.process_with_progress(all_chunks):
        progress_updates.append(progress)
        
        # Show progress every 20%
        if len(progress_updates) % max(1, len(all_chunks) // 500) == 0:
            print(f"      Progress: {progress.percentage:.1f}% - "
                  f"Rate: {progress.rate:.1f} chunks/s - "
                  f"ETA: {progress.eta:.1f}s")
    
    optimized_time = time.time() - start_time
    final_progress = progress_updates[-1]
    
    print(f"\n      Final Results:")
    print(f"      Total time: {optimized_time:.2f} seconds")
    print(f"      Average rate: {final_progress.rate:.2f} chunks/second")
    print(f"      Total processed: {final_progress.completed}")
    print(f"      Failed: {final_progress.failed}")
    
    # Summary
    print("\n5. Performance Summary")
    print("=" * 50)
    
    if basic_time > 0:
        basic_improvement = non_batched_time / basic_time
        print(f"   Basic batching: {basic_improvement:.1f}x faster than non-batched")
    
    if optimized_time > 0:
        optimized_improvement = non_batched_time / optimized_time
        concurrent_improvement = basic_time / optimized_time if basic_time > 0 else 1
        
        print(f"   Optimized batching: {optimized_improvement:.1f}x faster than non-batched")
        print(f"   Optimized batching: {concurrent_improvement:.1f}x faster than basic batching")
    
    print(f"\n   Throughput achieved: {final_progress.rate:.0f} chunks/second")
    print(f"   Time saved: {non_batched_time - optimized_time:.1f} seconds")
    
    # Cost estimation
    print("\n6. Cost Savings Estimation")
    # Assume OpenAI pricing: $0.0004 per 1K tokens
    avg_tokens_per_chunk = 100
    total_tokens = len(all_chunks) * avg_tokens_per_chunk
    
    # Non-batched: individual API calls
    non_batched_calls = len(all_chunks)
    non_batched_cost = non_batched_calls * 0.0001  # Overhead per call
    
    # Batched: fewer API calls
    batched_calls = final_progress.batches_processed
    batched_cost = batched_calls * 0.0001
    
    print(f"   Non-batched API calls: {non_batched_calls}")
    print(f"   Batched API calls: {batched_calls}")
    print(f"   API calls reduced by: {((non_batched_calls - batched_calls) / non_batched_calls * 100):.1f}%")
    print(f"   Estimated cost savings: ${non_batched_cost - batched_cost:.4f}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(demonstrate_batch_processing())