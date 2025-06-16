"""Minimal indexing using ChromaDB without any embeddings."""

import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict
import typer


def minimal_index(project_path: Path, signal_hub_dir: Path):
    """Ultra-minimal indexing that stores only text, no embeddings."""
    
    db_path = signal_hub_dir / "db"
    db_path.mkdir(exist_ok=True)
    
    # Store index as simple JSON for now (no ChromaDB)
    index_file = db_path / "index.json"
    
    # File scanning
    extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".java", ".cpp", ".c", ".h", ".go", ".rs"}
    ignore_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv", "target"}
    
    typer.echo("Scanning files...")
    files = []
    for ext in extensions:
        for file_path in project_path.rglob(f"*{ext}"):
            if not any(d in file_path.parts for d in ignore_dirs):
                try:
                    if file_path.stat().st_size < 500_000:  # 500KB limit
                        files.append(file_path)
                except:
                    pass
    
    typer.echo(f"Found {len(files)} files to index")
    
    if len(files) > 1000:
        if not typer.confirm(f"Index {len(files)} files?"):
            return
    
    # Build index
    index_data = {
        "version": "1.0",
        "created": time.time(),
        "project_path": str(project_path),
        "documents": []
    }
    
    indexed = 0
    errors = 0
    start_time = time.time()
    
    typer.echo("Building index...")
    
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip() or len(content) < 10:
                continue
            
            # Store full content for small files, chunks for large
            if len(content) < 5000:
                # Small file - store whole
                doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
                index_data["documents"].append({
                    "id": doc_id,
                    "path": str(file_path.relative_to(project_path)),
                    "content": content,
                    "type": "full",
                    "size": len(content)
                })
            else:
                # Large file - store chunks
                lines = content.split("\n")
                chunk_size = 100
                
                for i in range(0, len(lines), chunk_size):
                    chunk_text = "\n".join(lines[i:i + chunk_size])
                    if len(chunk_text.strip()) < 20:
                        continue
                    
                    doc_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()
                    index_data["documents"].append({
                        "id": doc_id,
                        "path": str(file_path.relative_to(project_path)),
                        "content": chunk_text,
                        "type": "chunk",
                        "start_line": i + 1,
                        "size": len(chunk_text)
                    })
            
            indexed += 1
            
            # Progress every 100 files
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
            if errors < 10:
                typer.echo(f"Error with {file_path}: {e}")
    
    # Save index
    typer.echo("\nSaving index...")
    with open(index_file, 'w') as f:
        json.dump(index_data, f)
    
    elapsed = time.time() - start_time
    typer.echo(f"\n✓ Indexing complete in {elapsed:.1f} seconds!")
    typer.echo(f"Indexed: {indexed} files")
    typer.echo(f"Total documents: {len(index_data['documents'])}")
    typer.echo(f"Index size: {index_file.stat().st_size / 1024 / 1024:.1f} MB")
    typer.echo(f"Rate: {indexed/elapsed:.1f} files/sec")
    
    # Create a marker for search to know we're using minimal index
    (db_path / "minimal_index.marker").touch()


def minimal_search(query: str, signal_hub_dir: Path, limit: int = 10):
    """Search the minimal index using simple text matching."""
    
    db_path = signal_hub_dir / "db"
    index_file = db_path / "index.json"
    
    if not index_file.exists():
        typer.echo("No index found. Run 'signal-hub index' first.")
        return
    
    typer.echo(f"Searching for: {query}")
    typer.echo("Loading index...")
    
    with open(index_file, 'r') as f:
        index_data = json.load(f)
    
    # Simple case-insensitive search
    query_lower = query.lower()
    results = []
    
    for doc in index_data["documents"]:
        if query_lower in doc["content"].lower():
            # Count occurrences for scoring
            score = doc["content"].lower().count(query_lower)
            results.append((score, doc))
    
    # Sort by score
    results.sort(key=lambda x: x[0], reverse=True)
    results = results[:limit]
    
    if not results:
        typer.echo("No results found")
        return
    
    typer.echo(f"\nFound {len(results)} results:\n")
    for i, (score, doc) in enumerate(results, 1):
        typer.echo(f"{i}. {doc['path']}", end="")
        if doc["type"] == "chunk":
            typer.echo(f":{doc.get('start_line', '')}")
        else:
            typer.echo()
        typer.echo(f"   Matches: {score}")
        
        # Show preview with match highlighted
        content_lower = doc["content"].lower()
        match_pos = content_lower.find(query_lower)
        if match_pos >= 0:
            start = max(0, match_pos - 50)
            end = min(len(doc["content"]), match_pos + len(query) + 50)
            preview = doc["content"][start:end].replace('\n', ' ')
            typer.echo(f"   ...{preview}...")
        typer.echo()