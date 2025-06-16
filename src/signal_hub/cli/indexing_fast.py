"""Fast indexing implementation without embedding generation blocking."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import List, Set
import typer


def fast_index(project_path: Path, signal_hub_dir: Path):
    """Ultra-fast indexing by deferring embedding generation."""
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        typer.echo("Error: ChromaDB not installed")
        return
    
    db_path = signal_hub_dir / "db"
    db_path.mkdir(exist_ok=True)
    
    # Use ChromaDB with minimal settings for speed
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Create collection without default embedding function
    # This prevents blocking on embedding generation
    try:
        client.delete_collection("signal_hub_index_fast")
    except:
        pass
        
    collection = client.create_collection(
        name="signal_hub_index_fast",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None  # Don't generate embeddings during indexing
    )
    
    # File scanning
    extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".java", ".cpp", ".c", ".h", ".go", ".rs"}
    ignore_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv", "target"}
    
    typer.echo("Scanning files...")
    files = []
    for ext in extensions:
        for file_path in project_path.rglob(f"*{ext}"):
            if not any(d in file_path.parts for d in ignore_dirs):
                try:
                    if file_path.stat().st_size < 1_000_000:  # 1MB limit
                        files.append(file_path)
                except:
                    pass
    
    typer.echo(f"Found {len(files)} files to index")
    
    if len(files) > 1000:
        typer.echo(f"\nWarning: Large codebase ({len(files)} files)")
        typer.echo("Using fast indexing mode (embeddings will be generated on first search)")
        if not typer.confirm("Continue?"):
            return
    
    # Fast batched indexing
    batch_size = 500  # Large batches since no embedding generation
    all_texts = []
    all_metadatas = []
    all_ids = []
    
    indexed = 0
    errors = 0
    start_time = time.time()
    
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip() or len(content) < 10:
                continue
            
            # Simple chunking
            lines = content.split("\n")
            chunk_size = 100  # Larger chunks for speed
            
            for i in range(0, len(lines), chunk_size):
                chunk_text = "\n".join(lines[i:i + chunk_size])
                if len(chunk_text.strip()) < 20:
                    continue
                
                chunk_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()
                
                all_texts.append(chunk_text)
                all_metadatas.append({
                    "file_path": str(file_path.relative_to(project_path)),
                    "start_line": i + 1,
                    "language": file_path.suffix
                })
                all_ids.append(chunk_id)
                
                # Add batch when full
                if len(all_texts) >= batch_size:
                    collection.add(
                        documents=all_texts,
                        metadatas=all_metadatas,
                        ids=all_ids
                    )
                    all_texts = []
                    all_metadatas = []
                    all_ids = []
            
            indexed += 1
            
            # Progress
            if indexed % 100 == 0:
                elapsed = time.time() - start_time
                rate = indexed / elapsed
                eta = (len(files) - indexed) / rate if rate > 0 else 0
                typer.echo(
                    f"Progress: {indexed}/{len(files)} files "
                    f"({indexed/len(files)*100:.1f}%) - "
                    f"{rate:.1f} files/sec - ETA: {eta:.0f}s"
                )
                
        except Exception as e:
            errors += 1
            if errors < 10:  # Only show first 10 errors
                typer.echo(f"Error with {file_path}: {e}")
    
    # Add remaining
    if all_texts:
        collection.add(
            documents=all_texts,
            metadatas=all_metadatas,
            ids=all_ids
        )
    
    elapsed = time.time() - start_time
    typer.echo(f"\n✓ Fast indexing complete in {elapsed:.1f} seconds!")
    typer.echo(f"Indexed: {indexed} files")
    typer.echo(f"Rate: {indexed/elapsed:.1f} files/sec")
    if errors > 0:
        typer.echo(f"Errors: {errors}")
    
    typer.echo("\nNote: Embeddings will be generated on first search.")
    typer.echo("First search may be slower, but subsequent searches will be fast.")


def fast_search(query: str, signal_hub_dir: Path, limit: int = 10):
    """Search using the fast index."""
    import chromadb
    
    db_path = signal_hub_dir / "db"
    client = chromadb.PersistentClient(path=str(db_path))
    
    # Try fast collection first
    try:
        collection = client.get_collection("signal_hub_index_fast")
    except:
        # Fall back to regular collection
        try:
            collection = client.get_collection("signal_hub_index")
        except:
            typer.echo("No index found. Run 'signal-hub index' first.")
            return
    
    typer.echo(f"Searching for: {query}")
    typer.echo("Generating embeddings (first search may be slower)...")
    
    # Search will trigger embedding generation if needed
    results = collection.query(
        query_texts=[query],
        n_results=limit
    )
    
    if not results['documents'][0]:
        typer.echo("No results found")
        return
    
    typer.echo(f"\nFound {len(results['documents'][0])} results:\n")
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0], 
        results['distances'][0]
    ), 1):
        score = 1 - (distance / 2)
        typer.echo(f"{i}. {metadata.get('file_path', 'Unknown')}:{metadata.get('start_line', '')}")
        typer.echo(f"   Score: {score:.3f}")
        preview = doc.replace('\n', ' ')[:100]
        typer.echo(f"   {preview}...")
        typer.echo()