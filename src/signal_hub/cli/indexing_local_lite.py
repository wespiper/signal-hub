"""Local embedding indexing using lightweight models without onnxruntime dependency."""

import asyncio
import hashlib
import time
import signal
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

import typer

# We'll use a different approach that doesn't require onnxruntime


class LocalLiteIndexer:
    """Lightweight local indexer without heavy dependencies."""
    
    def __init__(self, db_path: Path, project_path: Path):
        self.db_path = db_path
        self.project_path = project_path
        
        # Settings
        self.chunk_size = 100  # Lines per chunk
        self.max_file_size = 500_000  # 500KB
        
        # File extensions
        self.extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".java", ".go", ".rs"}
        self.ignore_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv"}
        
        # Simple TF-IDF based approach for now
        self.index_path = db_path / "local_lite_index.json"
        self.tfidf_path = db_path / "tfidf_data.json"
    
    def scan_files(self) -> List[Path]:
        """Scan for files to index."""
        files = []
        for ext in self.extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                if not any(d in file_path.parts for d in self.ignore_dirs):
                    try:
                        if file_path.stat().st_size < self.max_file_size:
                            files.append(file_path)
                    except:
                        pass
        return files
    
    def extract_tokens(self, text: str) -> List[str]:
        """Simple tokenization for code."""
        import re
        # Split on non-alphanumeric, keep meaningful tokens
        tokens = re.findall(r'\b[a-zA-Z_]\w*\b', text.lower())
        # Filter out very short tokens
        return [t for t in tokens if len(t) > 2]
    
    async def index_files(self, files: List[Path]):
        """Index files with simple TF-IDF approach."""
        typer.echo(f"\nIndexing {len(files)} files with lightweight local method...")
        
        documents = []
        doc_tokens = []
        total_chunks = 0
        indexed_files = 0
        errors = 0
        start_time = time.time()
        
        # Build document collection
        for file_idx, file_path in enumerate(files):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if not content.strip():
                    continue
                
                # Chunk the file
                lines = content.split("\n")
                
                for i in range(0, len(lines), self.chunk_size):
                    chunk_lines = lines[i:i + self.chunk_size]
                    chunk_text = "\n".join(chunk_lines).strip()
                    
                    if len(chunk_text) < 20:
                        continue
                    
                    # Extract tokens
                    tokens = self.extract_tokens(chunk_text)
                    if not tokens:
                        continue
                    
                    # Store document
                    doc_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()
                    doc_info = {
                        "id": doc_id,
                        "content": chunk_text,
                        "tokens": tokens,
                        "metadata": {
                            "file_path": str(file_path.relative_to(self.project_path)),
                            "start_line": i + 1,
                            "end_line": min(i + self.chunk_size, len(lines)),
                            "language": file_path.suffix
                        }
                    }
                    documents.append(doc_info)
                    doc_tokens.append(set(tokens))
                    total_chunks += 1
                
                indexed_files += 1
                
                # Progress update
                if indexed_files % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = indexed_files / elapsed
                    eta = (len(files) - indexed_files) / rate if rate > 0 else 0
                    
                    typer.echo(
                        f"Progress: {indexed_files}/{len(files)} files "
                        f"({indexed_files/len(files)*100:.1f}%) - "
                        f"{rate:.1f} files/sec - "
                        f"ETA: {eta:.0f}s"
                    )
                    
            except Exception as e:
                errors += 1
                if errors <= 5:
                    typer.echo(f"Error with {file_path}: {e}")
        
        # Build TF-IDF index
        typer.echo("\nBuilding search index...")
        
        # Calculate document frequencies with progress
        typer.echo("Calculating token frequencies...")
        all_tokens = set()
        for i, tokens in enumerate(doc_tokens):
            all_tokens.update(tokens)
            if i % 1000 == 0:
                typer.echo(f"  Processed {i}/{len(doc_tokens)} documents...")
        
        typer.echo(f"Found {len(all_tokens)} unique tokens")
        
        # Limit vocabulary size for performance
        if len(all_tokens) > 50000:
            typer.echo(f"Large vocabulary detected. Limiting to top 50k tokens...")
            # Calculate token frequencies
            token_counts = {}
            for tokens in doc_tokens:
                for token in tokens:
                    token_counts[token] = token_counts.get(token, 0) + 1
            # Keep only top 50k most frequent tokens
            sorted_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)
            all_tokens = set(token for token, _ in sorted_tokens[:50000])
        
        typer.echo("Calculating document frequencies...")
        doc_freq = {}
        for i, token in enumerate(all_tokens):
            doc_freq[token] = sum(1 for tokens in doc_tokens if token in tokens)
            if i % 5000 == 0:
                typer.echo(f"  Processed {i}/{len(all_tokens)} tokens...")
        
        # Calculate TF-IDF vectors (simplified)
        typer.echo("\nCalculating TF-IDF scores...")
        import math
        n_docs = len(documents)
        
        for doc_idx, doc in enumerate(documents):
            # Calculate TF-IDF for this document
            token_counts = {}
            for token in doc["tokens"]:
                if token in all_tokens:  # Only use tokens in our vocabulary
                    token_counts[token] = token_counts.get(token, 0) + 1
            
            # Simplified TF-IDF
            tfidf = {}
            max_count = max(token_counts.values()) if token_counts else 1
            for token, count in token_counts.items():
                tf = count / max_count  # Normalized term frequency
                idf = math.log(n_docs / (doc_freq.get(token, 1) + 1))
                tfidf[token] = tf * idf
            
            doc["tfidf"] = tfidf
            # Remove tokens to save space
            del doc["tokens"]
            
            if doc_idx % 1000 == 0:
                typer.echo(f"  Processed {doc_idx}/{n_docs} documents...")
        
        # Save index
        typer.echo("Saving index...")
        index_data = {
            "version": "1.0",
            "created": time.time(),
            "project_path": str(self.project_path),
            "total_docs": len(documents),
            "doc_freq": doc_freq,
            "documents": documents
        }
        
        with open(self.index_path, 'w') as f:
            json.dump(index_data, f)
        
        # Summary
        elapsed = time.time() - start_time
        typer.echo(f"\n✓ Indexing complete in {elapsed:.1f} seconds!")
        typer.echo(f"Indexed: {indexed_files} files, {total_chunks} chunks")
        typer.echo(f"Rate: {indexed_files/elapsed:.1f} files/sec")
        typer.echo(f"Index size: {self.index_path.stat().st_size / 1024 / 1024:.1f} MB")
        if errors > 0:
            typer.echo(f"Errors: {errors}")
        
        # Mark as local lite index
        (self.db_path / "local_lite_index.marker").touch()


async def index_with_local_lite(project_path: Path, signal_hub_dir: Path):
    """Run lightweight local indexing."""
    db_path = signal_hub_dir / "db"
    db_path.mkdir(exist_ok=True)
    
    typer.echo("🚀 Signal Hub Lightweight Local Indexer")
    typer.echo("(No heavy dependencies required!)")
    typer.echo("=" * 50)
    
    # Initialize indexer
    indexer = LocalLiteIndexer(db_path, project_path)
    
    # Scan files
    typer.echo(f"\nScanning {project_path}...")
    files = indexer.scan_files()
    typer.echo(f"Found {len(files)} files to index")
    
    if not files:
        typer.echo("No files to index")
        return
    
    # Confirm for large codebases
    if len(files) > 1000:
        if not typer.confirm(f"\nIndex {len(files)} files?"):
            return
    
    # Run indexing
    await indexer.index_files(files)
    
    typer.echo("\n✨ Ready for similarity search!")
    typer.echo("Try: signal-hub search 'user authentication'")


def search_with_local_lite(query: str, signal_hub_dir: Path, limit: int = 10):
    """Search using lightweight local index."""
    db_path = signal_hub_dir / "db"
    index_path = db_path / "local_lite_index.json"
    
    if not index_path.exists():
        typer.echo("No local index found. Run 'signal-hub index --local' first.")
        return
    
    typer.echo(f"🔍 Searching for: {query}")
    
    # Load index
    with open(index_path, 'r') as f:
        index_data = json.load(f)
    
    # Tokenize query
    import re
    query_tokens = re.findall(r'\b[a-zA-Z_]\w*\b', query.lower())
    query_tokens = [t for t in query_tokens if len(t) > 2]
    
    if not query_tokens:
        typer.echo("No valid search tokens")
        return
    
    # Score documents
    scores = []
    for doc in index_data["documents"]:
        score = 0
        # TF-IDF similarity
        for token in query_tokens:
            score += doc["tfidf"].get(token, 0)
        
        # Boost exact matches
        if query.lower() in doc["content"].lower():
            score *= 2
        
        if score > 0:
            scores.append((score, doc))
    
    # Sort by score
    scores.sort(key=lambda x: x[0], reverse=True)
    results = scores[:limit]
    
    if not results:
        typer.echo("No results found")
        return
    
    typer.echo(f"\n✨ Found {len(results)} results:\n")
    
    for i, (score, doc) in enumerate(results, 1):
        metadata = doc["metadata"]
        typer.echo(f"{i}. {metadata.get('file_path', 'Unknown')}:{metadata.get('start_line', '')}")
        typer.echo(f"   📊 Score: {score:.3f}")
        
        # Show preview with query highlight
        content = doc["content"]
        preview = content.replace('\n', ' ')
        
        # Try to show relevant part
        query_lower = query.lower()
        if query_lower in preview.lower():
            idx = preview.lower().find(query_lower)
            start = max(0, idx - 50)
            end = min(len(preview), idx + len(query) + 50)
            preview = f"...{preview[start:end]}..."
        else:
            preview = preview[:150] + "..."
        
        typer.echo(f"   📝 {preview}")
        typer.echo()