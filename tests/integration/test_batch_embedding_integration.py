"""Integration tests for batch embedding processing."""

import asyncio
import pytest
import time
from typing import List

from signal_hub.indexing.embeddings import (
    EmbeddingService,
    BatchEmbeddingProcessor,
    ProcessingProgress
)
from signal_hub.indexing.embeddings.providers import LocalEmbeddingProvider


class TestBatchEmbeddingIntegration:
    """Test batch embedding processing integration."""
    
    @pytest.fixture
    async def embedding_service(self):
        """Create embedding service with local provider."""
        service = EmbeddingService()
        # Use local provider for testing
        provider = LocalEmbeddingProvider()
        service.set_provider(provider)
        return service
        
    @pytest.mark.asyncio
    async def test_large_batch_processing(self, embedding_service):
        """Test processing large number of chunks."""
        # Create 1000 test chunks
        chunks = [f"This is test chunk number {i} with some content." for i in range(1000)]
        
        # Create batch processor
        processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            batch_size=100,
            max_concurrent_batches=3
        )
        
        # Track progress
        progress_updates = []
        
        start_time = time.time()
        
        async for progress in processor.process_with_progress(chunks):
            progress_updates.append({
                "completed": progress.completed,
                "failed": progress.failed,
                "rate": progress.rate,
                "percentage": progress.percentage
            })
            
        elapsed = time.time() - start_time
        
        # Verify results
        final_progress = progress_updates[-1]
        assert final_progress["completed"] == 1000
        assert final_progress["failed"] == 0
        assert final_progress["percentage"] == 100.0
        
        # Should process 1000 chunks in batches
        assert len(progress_updates) == 10  # 1000 / 100 = 10 batches
        
        # Verify performance improvement
        print(f"Processed 1000 chunks in {elapsed:.2f} seconds")
        print(f"Rate: {final_progress['rate']:.2f} chunks/second")
        
        # Should achieve significant throughput
        assert final_progress["rate"] > 100  # At least 100 chunks/second
        
    @pytest.mark.asyncio
    async def test_progress_tracking_accuracy(self, embedding_service):
        """Test accuracy of progress tracking."""
        chunks = [f"chunk_{i}" for i in range(50)]
        
        processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            batch_size=10
        )
        
        progress_history = []
        
        async for progress in processor.process_with_progress(chunks):
            progress_history.append(progress.model_copy())
            
        # Should have 5 progress updates (50 / 10)
        assert len(progress_history) == 5
        
        # Verify progressive completion
        for i, progress in enumerate(progress_history):
            expected_completed = (i + 1) * 10
            assert progress.completed == expected_completed
            assert progress.batches_processed == i + 1
            
        # Verify ETA calculation
        for progress in progress_history[1:-1]:  # Skip first and last
            assert progress.eta > 0
            assert progress.rate > 0
            
    @pytest.mark.asyncio
    async def test_concurrent_vs_sequential_performance(self, embedding_service):
        """Compare concurrent vs sequential processing."""
        chunks = [f"chunk_{i}" for i in range(200)]
        
        # Sequential processing (max_concurrent_batches=1)
        sequential_processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            batch_size=50,
            max_concurrent_batches=1
        )
        
        start = time.time()
        async for _ in sequential_processor.process_with_progress(chunks):
            pass
        sequential_time = time.time() - start
        
        # Concurrent processing (max_concurrent_batches=4)
        concurrent_processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            batch_size=50,
            max_concurrent_batches=4
        )
        
        start = time.time()
        async for _ in concurrent_processor.process_with_progress(chunks):
            pass
        concurrent_time = time.time() - start
        
        print(f"Sequential time: {sequential_time:.2f}s")
        print(f"Concurrent time: {concurrent_time:.2f}s")
        print(f"Speedup: {sequential_time / concurrent_time:.2f}x")
        
        # Concurrent should be faster
        assert concurrent_time < sequential_time
        
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, embedding_service):
        """Test memory efficiency with large batches."""
        # Create very large chunks
        large_chunks = [
            f"This is a very large chunk {i} " * 100  # ~500 words each
            for i in range(500)
        ]
        
        processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            batch_size=50,  # Process in smaller batches
            max_concurrent_batches=2  # Limit concurrency
        )
        
        # Process should complete without memory issues
        completed = 0
        async for progress in processor.process_with_progress(large_chunks):
            completed = progress.completed
            
        assert completed == 500
        
    @pytest.mark.asyncio
    async def test_real_world_scenario(self, embedding_service):
        """Test realistic codebase indexing scenario."""
        # Simulate indexing a codebase with various file types
        code_chunks = []
        
        # Python files (typically more chunks)
        for i in range(50):
            code_chunks.extend([
                f"# Python file {i}\nimport os\nimport sys",
                f"class MyClass{i}:\n    def __init__(self):\n        pass",
                f"def function_{i}(arg1, arg2):\n    return arg1 + arg2",
            ])
            
        # JavaScript files
        for i in range(30):
            code_chunks.extend([
                f"// JavaScript file {i}\nconst module = require('module');",
                f"function jsFunction{i}(param) {{ return param * 2; }}",
            ])
            
        # Documentation files
        for i in range(20):
            code_chunks.extend([
                f"# Documentation {i}\nThis module provides functionality for...",
                f"## API Reference\nThe following functions are available:",
            ])
            
        total_chunks = len(code_chunks)
        print(f"Total chunks to process: {total_chunks}")
        
        # Configure for optimal performance
        processor = BatchEmbeddingProcessor(
            embedding_service=embedding_service,
            batch_size=100,
            max_concurrent_batches=5
        )
        
        start_time = time.time()
        final_progress = None
        
        async for progress in processor.process_with_progress(code_chunks):
            if progress.completed % 100 == 0:
                print(f"Progress: {progress.completed}/{progress.total} "
                      f"({progress.percentage:.1f}%) - "
                      f"Rate: {progress.rate:.1f} chunks/s - "
                      f"ETA: {progress.eta:.1f}s")
            final_progress = progress
            
        total_time = time.time() - start_time
        
        print(f"\nIndexing complete!")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average rate: {final_progress.rate:.2f} chunks/second")
        print(f"Batches processed: {final_progress.batches_processed}")
        
        # Verify all chunks processed
        assert final_progress.completed == total_chunks
        assert final_progress.failed == 0
        
        # Calculate improvement vs non-batched
        estimated_non_batched_time = total_chunks * 0.1  # ~0.1s per chunk
        improvement = estimated_non_batched_time / total_time
        print(f"Estimated {improvement:.1f}x improvement over non-batched processing")