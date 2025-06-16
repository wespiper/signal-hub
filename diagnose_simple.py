#!/usr/bin/env python3
"""Simple diagnostic for indexing issues - no external deps."""

import time
import sys
from pathlib import Path

def diagnose():
    """Run simple diagnostics."""
    
    print("=== Signal Hub Indexing Diagnostics (Simple) ===\n")
    
    # 1. Check Python version
    print(f"1. Python version: {sys.version}")
    
    # 2. Check ChromaDB
    print("\n2. Testing ChromaDB:")
    try:
        import chromadb
        print(f"   ✓ ChromaDB version: {chromadb.__version__}")
        
        # Test creating a collection
        print("\n3. Testing document addition speed:")
        client = chromadb.Client()
        collection = client.create_collection("test")
        
        # Test adding documents in batches
        print("\n   Testing batch performance:")
        for batch_num in range(5):
            docs = [f"test doc {i}" for i in range(10)]
            ids = [f"id_{batch_num}_{i}" for i in range(10)]
            
            start = time.time()
            collection.add(documents=docs, ids=ids)
            elapsed = time.time() - start
            
            print(f"   Batch {batch_num + 1} (10 docs): {elapsed:.3f}s = {10/elapsed:.1f} docs/sec")
            
            # The issue: does it slow down after batch 4-5?
            if batch_num == 4:
                print("\n   Testing single additions after 50 docs:")
                for i in range(5):
                    start = time.time()
                    collection.add(
                        documents=[f"single doc {i}"],
                        ids=[f"single_{i}"]
                    )
                    elapsed = time.time() - start
                    print(f"   Single doc {i+1}: {elapsed:.3f}s")
        
        # Check embedding function
        print(f"\n4. Embedding function type: {type(collection._embedding_function)}")
        
    except Exception as e:
        print(f"   ✗ ChromaDB error: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Check onnxruntime
    print("\n5. Testing onnxruntime:")
    try:
        import onnxruntime
        print(f"   ✓ onnxruntime version: {onnxruntime.__version__}")
        
        # This is key for Apple Silicon
        providers = onnxruntime.get_available_providers()
        print(f"   ✓ Available providers: {providers}")
        
        if 'CoreMLExecutionProvider' in providers:
            print("   ✓ CoreML provider available (good for Apple Silicon)")
        else:
            print("   ⚠️  No CoreML provider - might be using slow CPU provider")
            
    except Exception as e:
        print(f"   ✗ onnxruntime error: {e}")
    
    print("\n=== Key Question ===")
    print("Does ChromaDB slow down after ~40-50 documents?")
    print("If yes, it's likely loading the embedding model into memory.")
    

if __name__ == "__main__":
    diagnose()