"""Tests for batch processor."""

import asyncio
import pytest
import time
from typing import List

from signal_hub.indexing.embeddings.batch import (
    BatchRequest,
    BatchProcessor,
    SmartBatcher,
    BatchEmbeddingProcessor,
    ProcessingProgress
)


class TestBatchProcessor:
    """Test basic batch processor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create batch processor for testing."""
        return BatchProcessor(
            batch_size=5,
            max_wait_time=0.1
        )
        
    @pytest.mark.asyncio
    async def test_batch_collection(self, processor):
        """Test batch collection logic."""
        processed_batches = []
        
        async def process_func(texts):
            processed_batches.append(texts)
            return type('Result', (), {'embeddings': [[0.1] * 10 for _ in texts]})()
            
        # Start processor
        await processor.start(process_func)
        
        try:
            # Add requests
            for i in range(7):
                request = BatchRequest(texts=[f"text_{i}"])
                await processor.add_request(request)
                
            # Wait for processing
            await asyncio.sleep(0.3)
            
            # Should have processed in two batches (5 + 2)
            assert len(processed_batches) == 2
            assert len(processed_batches[0]) == 5
            assert len(processed_batches[1]) == 2
            
        finally:
            await processor.stop()
            
    @pytest.mark.asyncio
    async def test_max_wait_time(self, processor):
        """Test that batches are processed after max wait time."""
        process_times = []
        
        async def process_func(texts):
            process_times.append(time.time())
            return type('Result', (), {'embeddings': [[0.1] * 10 for _ in texts]})()
            
        await processor.start(process_func)
        
        try:
            # Add only 2 requests (less than batch size)
            start_time = time.time()
            for i in range(2):
                request = BatchRequest(texts=[f"text_{i}"])
                await processor.add_request(request)
                
            # Wait for processing
            await asyncio.sleep(0.3)
            
            # Should have processed after max_wait_time
            assert len(process_times) == 1
            elapsed = process_times[0] - start_time
            assert 0.1 <= elapsed <= 0.2  # Around max_wait_time
            
        finally:
            await processor.stop()
            
    @pytest.mark.asyncio
    async def test_queue_full_error(self, processor):
        """Test queue full error."""
        processor.max_queue_size = 2
        
        # Fill queue
        for i in range(2):
            request = BatchRequest(texts=[f"text_{i}"])
            await processor.add_request(request)
            
        # Should raise on next add
        with pytest.raises(RuntimeError, match="Queue full"):
            request = BatchRequest(texts=["overflow"])
            await processor.add_request(request)
            
    @pytest.mark.asyncio
    async def test_callback_execution(self, processor):
        """Test that callbacks are executed."""
        callback_results = []
        
        async def callback(embedding, metadata, error=None):
            callback_results.append((embedding, metadata, error))
            
        async def process_func(texts):
            return type('Result', (), {'embeddings': [[i] for i in range(len(texts))]})()
            
        await processor.start(process_func)
        
        try:
            # Add requests with callbacks
            for i in range(3):
                request = BatchRequest(
                    texts=[f"text_{i}"],
                    callback=callback,
                    metadata={"index": i}
                )
                await processor.add_request(request)
                
            # Wait for processing
            await asyncio.sleep(0.3)
            
            # Check callbacks were called
            assert len(callback_results) == 3
            for i, (embedding, metadata, error) in enumerate(callback_results):
                assert embedding == [i]
                assert metadata["index"] == i
                assert error is None
                
        finally:
            await processor.stop()


class TestSmartBatcher:
    """Test smart batching functionality."""
    
    def test_create_batches_by_tokens(self):
        """Test creating batches based on token limits."""
        batcher = SmartBatcher(max_tokens=100)
        
        # Create texts with known token counts
        texts = [
            "short text",  # ~2 words = ~3 tokens
            "a bit longer text here",  # ~5 words = ~7 tokens
            "this is a much longer text with many words " * 10,  # ~90 words = ~117 tokens
            "another short one",  # ~3 words = ~4 tokens
        ]
        
        batches = batcher.create_batches(texts)
        
        # Should create 3 batches due to token limits
        assert len(batches) >= 2
        # Long text should be in its own batch
        assert any(len(batch) == 1 and "much longer" in batch[0] for batch in batches)
        
    def test_empty_texts(self):
        """Test handling empty text list."""
        batcher = SmartBatcher()
        batches = batcher.create_batches([])
        assert batches == []
        
    def test_custom_token_estimator(self):
        """Test using custom token estimator."""
        batcher = SmartBatcher(max_tokens=10)
        
        # Custom estimator that counts characters
        def char_counter(text):
            return len(text)
            
        texts = ["12345", "123456789", "12", "123"]
        batches = batcher.create_batches(texts, estimate_tokens=char_counter)
        
        # Should batch based on character count
        assert len(batches) >= 2
        # "123456789" should be alone (9 chars)
        assert any(len(batch) == 1 and "123456789" in batch[0] for batch in batches)


class TestBatchEmbeddingProcessor:
    """Test the enhanced batch embedding processor."""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        class MockService:
            async def generate_embeddings(self, texts: List[str]):
                # Simulate processing delay
                await asyncio.sleep(0.01)
                
                result = type('Result', (), {
                    'embeddings': [[i * 0.1] * 10 for i in range(len(texts))],
                    'model': 'test-model',
                    'usage': {'tokens': len(texts) * 10}
                })()
                return result
                
        return MockService()
        
    @pytest.mark.asyncio
    async def test_process_with_progress(self, mock_embedding_service):
        """Test processing with progress tracking."""
        processor = BatchEmbeddingProcessor(
            embedding_service=mock_embedding_service,
            batch_size=3,
            max_retries=2
        )
        
        # Create test chunks
        chunks = [f"chunk_{i}" for i in range(10)]
        
        # Track progress updates
        progress_updates = []
        
        async for progress in processor.process_with_progress(chunks):
            progress_updates.append(progress.model_copy())
            
        # Verify progress tracking
        assert len(progress_updates) > 0
        final_progress = progress_updates[-1]
        assert final_progress.completed == 10
        assert final_progress.total == 10
        assert final_progress.failed == 0
        
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, mock_embedding_service):
        """Test retry mechanism on failures."""
        # Create service that fails first time
        call_count = 0
        
        class FailingService:
            async def generate_embeddings(self, texts):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("API error")
                return type('Result', (), {
                    'embeddings': [[0.1] * 10 for _ in texts],
                    'model': 'test-model',
                    'usage': {'tokens': len(texts) * 10}
                })()
                
        processor = BatchEmbeddingProcessor(
            embedding_service=FailingService(),
            batch_size=5,
            max_retries=3,
            retry_delay=0.1
        )
        
        chunks = ["chunk_1", "chunk_2", "chunk_3"]
        
        embeddings = await processor.process_chunks(chunks)
        
        # Should succeed after retry
        assert len(embeddings) == 3
        assert call_count == 2  # First attempt failed, second succeeded
        
    @pytest.mark.asyncio
    async def test_concurrent_batches(self, mock_embedding_service):
        """Test concurrent batch processing."""
        processor = BatchEmbeddingProcessor(
            embedding_service=mock_embedding_service,
            batch_size=2,
            max_concurrent_batches=3
        )
        
        # Create many chunks
        chunks = [f"chunk_{i}" for i in range(20)]
        
        start_time = time.time()
        embeddings = await processor.process_chunks(chunks)
        elapsed = time.time() - start_time
        
        # Should process faster with concurrency
        assert len(embeddings) == 20
        # With concurrency, should be faster than sequential
        assert elapsed < 0.5  # Rough estimate
        
    @pytest.mark.asyncio
    async def test_progress_calculation(self):
        """Test progress calculation accuracy."""
        progress = ProcessingProgress(
            total=100,
            completed=25,
            failed=5,
            start_time=time.time() - 10  # Started 10 seconds ago
        )
        
        # Test rate calculation
        assert progress.rate > 0
        assert progress.rate == (25 + 5) / 10  # 30 items in 10 seconds
        
        # Test ETA calculation
        assert progress.eta > 0
        # Should be around 23.3 seconds (70 remaining / 3 per second)
        assert 20 <= progress.eta <= 30
        
        # Test percentage
        assert progress.percentage == 25.0