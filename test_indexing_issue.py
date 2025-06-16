#!/usr/bin/env python3
"""Test to reproduce the indexing slowdown issue."""

import time
import tempfile
from pathlib import Path

def test_chromadb_performance():
    """Test ChromaDB performance with increasing document counts."""
    
    print("Testing ChromaDB performance...\n")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test 1: Default ChromaDB (might auto-load embedding model)
            print("Test 1: Default ChromaDB client")
            client = chromadb.PersistentClient(path=tmpdir)
            collection = client.create_collection("test")
            
            times = []
            batch_size = 10
            
            for i in range(10):
                docs = [f"document {j}" for j in range(i*batch_size, (i+1)*batch_size)]
                ids = [f"id{j}" for j in range(i*batch_size, (i+1)*batch_size)]
                
                start = time.time()
                collection.add(documents=docs, ids=ids)
                elapsed = time.time() - start
                times.append(elapsed)
                
                rate = batch_size / elapsed
                print(f"Batch {i+1}: {elapsed:.3f}s ({rate:.1f} docs/sec)")
                
                # Check if performance degrades
                if i > 0 and elapsed > times[0] * 5:
                    print(f"⚠️  Performance degraded by {elapsed/times[0]:.1f}x!")
            
            # Test 2: ChromaDB without embedding function
            print("\n\nTest 2: ChromaDB with embedding_function=None")
            client2 = chromadb.PersistentClient(
                path=tmpdir + "2",
                settings=Settings(anonymized_telemetry=False)
            )
            collection2 = client2.create_collection(
                "test2", 
                embedding_function=None
            )
            
            # This should fail without embeddings
            try:
                collection2.add(documents=["test"], ids=["1"])
                print("✗ Unexpectedly succeeded without embeddings")
            except Exception as e:
                print(f"✓ Expected error: {type(e).__name__}")
            
            # Test 3: Add with explicit embeddings
            print("\n\nTest 3: ChromaDB with manual embeddings")
            import random
            
            times2 = []
            for i in range(10):
                docs = [f"document {j}" for j in range(i*batch_size, (i+1)*batch_size)]
                ids = [f"id{j}" for j in range(i*batch_size, (i+1)*batch_size)]
                # Fake embeddings
                embeddings = [[random.random() for _ in range(384)] for _ in docs]
                
                start = time.time()
                collection2.add(
                    documents=docs, 
                    ids=ids,
                    embeddings=embeddings
                )
                elapsed = time.time() - start
                times2.append(elapsed)
                
                rate = batch_size / elapsed
                print(f"Batch {i+1}: {elapsed:.3f}s ({rate:.1f} docs/sec)")
            
            print("\n\nSummary:")
            print(f"With auto embeddings: {sum(times):.1f}s total")
            print(f"With manual embeddings: {sum(times2):.1f}s total")
            print(f"Speedup: {sum(times)/sum(times2):.1f}x")
            
    except ImportError:
        print("ChromaDB not installed")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_file_processing():
    """Test file processing to see where slowdown occurs."""
    
    print("\n\nTesting file processing speed...")
    
    # Create test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create 100 test files
        print("Creating test files...")
        for i in range(100):
            (tmppath / f"test{i}.py").write_text(f"# Test file {i}\n" * 100)
        
        files = list(tmppath.glob("*.py"))
        
        # Test reading speed
        print("\nReading files:")
        times = []
        for i in range(0, len(files), 10):
            batch = files[i:i+10]
            start = time.time()
            for f in batch:
                content = f.read_text()
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"Files {i}-{i+10}: {elapsed:.3f}s ({10/elapsed:.1f} files/sec)")
        
        print(f"\nTotal: {sum(times):.1f}s for {len(files)} files")


if __name__ == "__main__":
    print("=== Signal Hub Indexing Performance Test ===\n")
    test_chromadb_performance()
    test_file_processing()
    print("\n=== Test Complete ===")