"""Local embedding indexing optimized for Apple Silicon."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging

import typer
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class LocalEmbeddingIndexer:
    """Indexer using local embeddings optimized for Apple Silicon."""
    
    def __init__(self, db_path: Path, project_path: Path):
        self.db_path = db_path
        self.project_path = project_path
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(db_path))
        
        # Use a fast, small model optimized for Apple Silicon
        # BGE-small is a good balance of speed and quality
        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-small-en-v1.5",  # 33M params, fast
                device="mps"  # Metal Performance Shaders for Apple Silicon
            )
            typer.echo("✓ Using Apple Silicon GPU acceleration (MPS)")
        except:
            # Fallback to CPU if MPS not available
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-small-en-v1.5"
            )
            typer.echo("! Using CPU (MPS not available)")
        
        # Create or get collection
        self.collection = self._get_or_create_collection()
        
        # Settings
        self.batch_size = 50  # Smaller batches for local model
        self.chunk_size = 100  # Lines per chunk
        self.max_file_size = 500_000  # 500KB
        
        # File extensions
        self.extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".java", ".go", ".rs"}
        self.ignore_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv"}
    
    def _get_or_create_collection(self):
        """Get or create the ChromaDB collection."""
        collection_name = "signal_hub_local"
        try:
            # Delete existing to start fresh
            self.client.delete_collection(collection_name)
        except:
            pass
        
        return self.client.create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
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
    
    async def index_files(self, files: List[Path]):
        """Index files with local embeddings."""
        typer.echo(f"\nIndexing {len(files)} files with local embeddings...")
        typer.echo("First time model loading may take 30-60 seconds...\n")
        
        total_chunks = 0
        indexed_files = 0
        errors = 0
        start_time = time.time()
        
        # Process in batches
        batch_documents = []
        batch_metadatas = []
        batch_ids = []
        
        # First document will trigger model download if needed
        first_doc_time = None
        
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
                    
                    # Add to batch
                    doc_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()
                    batch_documents.append(chunk_text)
                    batch_metadatas.append({
                        "file_path": str(file_path.relative_to(self.project_path)),
                        "start_line": i + 1,
                        "end_line": min(i + self.chunk_size, len(lines)),
                        "language": file_path.suffix
                    })
                    batch_ids.append(doc_id)
                    
                    # Process batch when full
                    if len(batch_documents) >= self.batch_size:
                        if first_doc_time is None:
                            typer.echo("Generating first embeddings (model loading)...")
                            batch_start = time.time()
                        
                        self.collection.add(
                            documents=batch_documents,
                            metadatas=batch_metadatas,
                            ids=batch_ids
                        )
                        
                        if first_doc_time is None:
                            first_doc_time = time.time() - batch_start
                            typer.echo(f"First batch took {first_doc_time:.1f}s (includes model loading)")
                            typer.echo("Subsequent batches will be much faster...\n")
                        
                        total_chunks += len(batch_documents)
                        batch_documents = []
                        batch_metadatas = []
                        batch_ids = []
                
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
        
        # Process remaining batch
        if batch_documents:
            self.collection.add(
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            total_chunks += len(batch_documents)
        
        # Summary
        elapsed = time.time() - start_time
        typer.echo(f"\n✓ Indexing complete in {elapsed:.1f} seconds!")
        typer.echo(f"Indexed: {indexed_files} files, {total_chunks} chunks")
        typer.echo(f"Rate: {indexed_files/elapsed:.1f} files/sec")
        if errors > 0:
            typer.echo(f"Errors: {errors}")
        
        # Test embedding quality
        typer.echo("\n📊 Embedding Statistics:")
        typer.echo(f"Collection size: {self.collection.count()} chunks")
        typer.echo(f"Embedding dimensions: 384")  # BGE-small uses 384 dimensions
        typer.echo(f"Model: BAAI/bge-small-en-v1.5")
        typer.echo(f"Device: {'Apple Silicon GPU (MPS)' if 'mps' in str(self.embedding_function) else 'CPU'}")


async def index_with_local_embeddings(project_path: Path, signal_hub_dir: Path):
    """Run local embedding indexing."""
    db_path = signal_hub_dir / "db"
    db_path.mkdir(exist_ok=True)
    
    typer.echo("🚀 Signal Hub Local Embeddings Indexer")
    typer.echo("=" * 50)
    
    # Check dependencies
    try:
        import sentence_transformers
        typer.echo("✓ sentence-transformers installed")
    except ImportError:
        typer.echo("❌ Missing dependency: sentence-transformers")
        typer.echo("Please install: pip install sentence-transformers")
        raise typer.Exit(1)
    
    try:
        import torch
        if torch.backends.mps.is_available():
            typer.echo("✓ Apple Silicon GPU (MPS) available")
        else:
            typer.echo("! MPS not available, will use CPU")
    except:
        typer.echo("! PyTorch not optimized for Apple Silicon")
    
    # Initialize indexer
    indexer = LocalEmbeddingIndexer(db_path, project_path)
    
    # Scan files
    typer.echo(f"\nScanning {project_path}...")
    files = indexer.scan_files()
    typer.echo(f"Found {len(files)} files to index")
    
    if not files:
        typer.echo("No files to index")
        return
    
    # Confirm for large codebases
    if len(files) > 1000:
        if not typer.confirm(f"\nIndex {len(files)} files with local embeddings?"):
            return
    
    # Run indexing
    await indexer.index_files(files)
    
    typer.echo("\n✨ Ready for semantic search!")
    typer.echo("Try: signal-hub search 'user authentication'")


def search_with_local_embeddings(query: str, signal_hub_dir: Path, limit: int = 10):
    """Search using local embeddings."""
    db_path = signal_hub_dir / "db"
    client = chromadb.PersistentClient(path=str(db_path))
    
    try:
        collection = client.get_collection("signal_hub_local")
    except:
        typer.echo("No local embedding index found. Run 'signal-hub index' first.")
        return
    
    typer.echo(f"🔍 Searching for: {query}")
    typer.echo("Generating query embedding...")
    
    # Search with semantic similarity
    results = collection.query(
        query_texts=[query],
        n_results=limit
    )
    
    if not results['documents'][0]:
        typer.echo("No results found")
        return
    
    typer.echo(f"\n✨ Found {len(results['documents'][0])} results:\n")
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ), 1):
        # Convert distance to similarity score
        similarity = 1 - (distance / 2)
        
        typer.echo(f"{i}. {metadata.get('file_path', 'Unknown')}:{metadata.get('start_line', '')}")
        typer.echo(f"   📊 Similarity: {similarity:.2%}")
        
        # Show preview with context
        preview = doc.replace('\n', ' ')
        if len(preview) > 150:
            preview = preview[:150] + "..."
        typer.echo(f"   📝 {preview}")
        typer.echo()