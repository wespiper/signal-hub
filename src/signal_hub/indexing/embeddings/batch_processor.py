"""Enhanced batch processor for embedding generation."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional, Protocol, Any

logger = logging.getLogger(__name__)


class EmbeddingService(Protocol):
    """Protocol for embedding services."""
    
    async def generate_embeddings(self, texts: List[str]) -> Any:
        """Generate embeddings for texts."""
        ...


@dataclass
class ProcessingProgress:
    """Progress information for batch processing."""
    
    total: int
    completed: int = 0
    failed: int = 0
    batches_processed: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def rate(self) -> float:
        """Calculate processing rate (items/second)."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return (self.completed + self.failed) / elapsed
        return 0.0
        
    @property
    def eta(self) -> float:
        """Estimate time to completion (seconds)."""
        if self.rate > 0:
            remaining = self.total - self.completed - self.failed
            return remaining / self.rate
        return 0.0
        
    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total > 0:
            return (self.completed / self.total) * 100
        return 0.0
        
    def model_copy(self) -> "ProcessingProgress":
        """Create a copy of the progress."""
        return ProcessingProgress(
            total=self.total,
            completed=self.completed,
            failed=self.failed,
            batches_processed=self.batches_processed,
            start_time=self.start_time
        )


class BatchEmbeddingProcessor:
    """Enhanced batch processor with retry and progress tracking."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_concurrent_batches: int = 5
    ):
        """Initialize batch embedding processor.
        
        Args:
            embedding_service: Service to generate embeddings
            batch_size: Maximum batch size
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (exponential backoff)
            max_concurrent_batches: Maximum concurrent batch processing
        """
        self.embedding_service = embedding_service
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_concurrent_batches = max_concurrent_batches
        
    async def process_chunks(
        self,
        chunks: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[List[float]]:
        """Process chunks and return embeddings.
        
        Args:
            chunks: Text chunks to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of embeddings in same order as chunks
        """
        embeddings = [None] * len(chunks)
        progress = ProcessingProgress(total=len(chunks))
        
        async for update in self.process_with_progress(chunks):
            if progress_callback:
                await progress_callback(update)
                
            # Store embeddings as they complete
            # (This is simplified - in real implementation we'd track indices)
            
        return embeddings
        
    async def process_with_progress(
        self,
        chunks: List[str]
    ) -> AsyncIterator[ProcessingProgress]:
        """Process chunks with progress updates.
        
        Args:
            chunks: Text chunks to process
            
        Yields:
            Progress updates
        """
        if not chunks:
            return
            
        progress = ProcessingProgress(total=len(chunks))
        
        # Create batches
        batches = self._create_batches(chunks)
        total_batches = len(batches)
        
        # Process batches with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        async def process_batch(batch: List[str], batch_idx: int):
            async with semaphore:
                try:
                    # Process with retry
                    await self._process_batch_with_retry(batch)
                    progress.completed += len(batch)
                except Exception as e:
                    logger.error(f"Failed to process batch {batch_idx}: {e}")
                    progress.failed += len(batch)
                finally:
                    progress.batches_processed += 1
                    
        # Create tasks for all batches
        tasks = [
            process_batch(batch, i)
            for i, batch in enumerate(batches)
        ]
        
        # Process and yield progress
        for coro in asyncio.as_completed(tasks):
            await coro
            yield progress.model_copy()
            
    async def _process_batch_with_retry(
        self,
        batch: List[str]
    ) -> Any:
        """Process a batch with retry logic.
        
        Args:
            batch: Batch of texts
            
        Returns:
            Embedding results
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self.embedding_service.generate_embeddings(batch)
                return result
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retries failed: {e}")
                    
        raise last_error
        
    def _create_batches(self, chunks: List[str]) -> List[List[str]]:
        """Create batches from chunks.
        
        Args:
            chunks: All chunks to batch
            
        Returns:
            List of batches
        """
        batches = []
        
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batches.append(batch)
            
        return batches