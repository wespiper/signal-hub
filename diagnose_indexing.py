#!/usr/bin/env python3
"""Diagnose indexing performance issues."""

import time
import sys
from pathlib import Path
import psutil
import traceback

def diagnose():
    """Run diagnostic tests to find the bottleneck."""
    
    print("=== Signal Hub Indexing Diagnostics ===\n")
    
    # 1. Check Python version
    print(f"1. Python version: {sys.version}")
    
    # 2. Check ChromaDB
    print("\n2. Testing ChromaDB:")
    try:
        import chromadb
        print(f"   ✓ ChromaDB version: {chromadb.__version__}")
        
        # Test creating a collection
        client = chromadb.Client()
        test_collection = client.create_collection("test")
        print("   ✓ Can create collection")
        
        # Test adding documents WITHOUT embedding function
        print("\n3. Testing document addition speed:")
        
        # Test 1: With default embedding (this might be slow)
        start = time.time()
        test_collection.add(
            documents=["test document"],
            ids=["test1"]
        )
        elapsed = time.time() - start
        print(f"   - With embeddings: {elapsed:.3f} seconds")
        
        # Test 2: Multiple documents
        docs = [f"document {i}" for i in range(20)]
        ids = [f"id{i}" for i in range(20)]
        
        start = time.time()
        test_collection.add(documents=docs, ids=ids)
        elapsed = time.time() - start
        print(f"   - 20 docs with embeddings: {elapsed:.3f} seconds")
        
        # Test 3: Check what embedding function is being used
        print(f"\n4. Embedding function: {test_collection._embedding_function}")
        
    except Exception as e:
        print(f"   ✗ ChromaDB error: {e}")
        traceback.print_exc()
    
    # 3. Check onnxruntime
    print("\n5. Testing onnxruntime:")
    try:
        import onnxruntime
        print(f"   ✓ onnxruntime version: {onnxruntime.__version__}")
        providers = onnxruntime.get_available_providers()
        print(f"   ✓ Available providers: {providers}")
    except Exception as e:
        print(f"   ✗ onnxruntime error: {e}")
    
    # 4. Check system resources
    print("\n6. System resources:")
    print(f"   - CPU count: {psutil.cpu_count()}")
    print(f"   - CPU usage: {psutil.cpu_percent(interval=1)}%")
    print(f"   - Memory: {psutil.virtual_memory().percent}% used")
    print(f"   - Disk I/O: {psutil.disk_io_counters()}")
    
    # 5. Test file reading speed
    print("\n7. Testing file I/O speed:")
    test_dir = Path(".")
    files = list(test_dir.rglob("*.py"))[:50]
    
    start = time.time()
    total_size = 0
    for f in files:
        try:
            content = f.read_text()
            total_size += len(content)
        except:
            pass
    elapsed = time.time() - start
    print(f"   - Read {len(files)} files ({total_size/1024:.1f} KB) in {elapsed:.3f} seconds")
    print(f"   - Rate: {len(files)/elapsed:.1f} files/sec")
    
    # 6. Test the actual indexing code path
    print("\n8. Testing actual indexing code:")
    try:
        # Import the actual indexing code
        sys.path.insert(0, "src")
        from signal_hub.cli.indexing_minimal import minimal_index
        from signal_hub.cli.indexing_fast import fast_index
        
        print("   ✓ Indexing modules imported successfully")
        
        # Check which one is being used
        with open("src/signal_hub/cli/simple.py", "r") as f:
            content = f.read()
            if "minimal_index" in content and "# For large codebases" in content:
                print("   ✓ Using minimal_index (good!)")
            elif "fast_index" in content:
                print("   ! Using fast_index (might use ChromaDB embeddings)")
            else:
                print("   ? Unknown indexing method")
                
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== Diagnosis Complete ===")
    
    # Recommendations
    print("\nRecommendations:")
    print("1. If ChromaDB embedding generation is slow, we need to ensure")
    print("   the minimal indexing is actually being used")
    print("2. Check if onnxruntime is using CPU instead of optimized provider")
    print("3. Monitor CPU usage during indexing to see if it spikes")


if __name__ == "__main__":
    diagnose()