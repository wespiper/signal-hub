"""Optimized indexing implementation for Signal Hub CLI."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import List, Set, Tuple
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

import typer
import chromadb


class OptimizedIndexer:
    """Optimized indexer with batching and concurrency control."""
    
    def __init__(self, db_path: Path, project_path: Path, fast_mode: bool = False, custom_extensions: Set[str] = None):
        self.db_path = db_path
        self.project_path = project_path
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self._get_or_create_collection()
        
        # Performance settings (adjusted for fast mode)
        if fast_mode:
            self.batch_size = 200  # Larger batches
            self.chunk_size = 100  # Larger chunks (less precision)
            self.max_file_size = 2_000_000  # 2MB max
            self.concurrent_files = min(8, multiprocessing.cpu_count())  # More concurrency
            typer.echo("Using fast mode: larger chunks, higher concurrency")
        else:
            self.batch_size = 100  # ChromaDB batch size
            self.chunk_size = 50   # Lines per chunk
            self.max_file_size = 1_000_000  # 1MB max file size
            self.concurrent_files = min(4, multiprocessing.cpu_count())  # Limit concurrency
        
        # File extensions to index
        if custom_extensions:
            self.extensions = custom_extensions
            typer.echo(f"Using custom extensions: {', '.join(sorted(self.extensions))}")
        else:
            self.extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php"}
        
        # Directories to ignore
        self.ignore_dirs = {
            "node_modules", ".git", "__pycache__", "dist", "build", 
            ".venv", "venv", "env", ".env", "target", "out", ".idea",
            ".vscode", ".pytest_cache", ".mypy_cache", "coverage",
            ".next", ".nuxt", "vendor", "bower_components"
        }
        
        # Binary and large file patterns to skip
        self.skip_patterns = {
            ".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe", ".bin",
            ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".webp",
            ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".pdf", ".zip",
            ".tar", ".gz", ".rar", ".7z", ".db", ".sqlite", ".log"
        }
    
    def _get_or_create_collection(self):
        """Get or create the ChromaDB collection."""
        try:
            return self.client.get_collection("signal_hub_index")
        except:
            return self.client.create_collection(
                name="signal_hub_index",
                metadata={"hnsw:space": "cosine"}
            )
    
    def should_index_file(self, file_path: Path) -> bool:
        """Check if a file should be indexed."""
        # Check extension
        if file_path.suffix.lower() not in self.extensions:
            return False
            
        # Check if it's a binary file type
        if file_path.suffix.lower() in self.skip_patterns:
            return False
            
        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size:
                return False
        except:
            return False
            
        # Check if in ignored directory
        for parent in file_path.parents:
            if parent.name in self.ignore_dirs:
                return False
                
        return True
    
    def scan_files(self) -> List[Path]:
        """Scan for files to index with smart filtering."""
        typer.echo("Scanning for files...")
        
        files = []
        total_scanned = 0
        
        for ext in self.extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                total_scanned += 1
                if self.should_index_file(file_path):
                    files.append(file_path)
                    
        typer.echo(f"Found {len(files)} indexable files out of {total_scanned} scanned")
        return files
    
    def chunk_file(self, file_path: Path) -> List[Tuple[str, dict]]:
        """Chunk a file and return (content, metadata) tuples."""
        chunks = []
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                return chunks
                
            lines = content.split("\n")
            
            for i in range(0, len(lines), self.chunk_size):
                chunk_lines = lines[i:i + self.chunk_size]
                chunk_content = "\n".join(chunk_lines).strip()
                
                if len(chunk_content) < 10:  # Skip tiny chunks
                    continue
                    
                metadata = {
                    "file_path": str(file_path.relative_to(self.project_path)),
                    "start_line": i + 1,
                    "end_line": min(i + self.chunk_size, len(lines)),
                    "language": file_path.suffix.lstrip('.'),
                }
                
                chunks.append((chunk_content, metadata))
                
        except Exception as e:
            typer.echo(f"Error processing {file_path}: {e}")
            
        return chunks
    
    async def index_files_batch(self, files: List[Path], progress_callback=None):
        """Index files in batches with progress tracking."""
        total_files = len(files)
        indexed_files = 0
        total_chunks = 0
        errors = 0
        
        # Prepare batches
        all_documents = []
        all_metadatas = []
        all_ids = []
        
        start_time = time.time()
        
        # Process files with controlled concurrency
        for i in range(0, len(files), self.concurrent_files):
            batch_files = files[i:i + self.concurrent_files]
            
            # Process batch of files
            for file_path in batch_files:
                chunks = self.chunk_file(file_path)
                
                for chunk_content, metadata in chunks:
                    # Generate unique ID
                    chunk_id = hashlib.md5(
                        f"{metadata['file_path']}:{metadata['start_line']}".encode()
                    ).hexdigest()
                    
                    all_documents.append(chunk_content)
                    all_metadatas.append(metadata)
                    all_ids.append(chunk_id)
                    
                    # Add to ChromaDB in batches
                    if len(all_documents) >= self.batch_size:
                        try:
                            self.collection.add(
                                documents=all_documents,
                                metadatas=all_metadatas,
                                ids=all_ids
                            )
                            total_chunks += len(all_documents)
                            all_documents = []
                            all_metadatas = []
                            all_ids = []
                        except Exception as e:
                            typer.echo(f"Error adding batch to ChromaDB: {e}")
                            errors += 1
                
                indexed_files += 1
                
                # Progress update
                if indexed_files % 10 == 0 or indexed_files == total_files:
                    elapsed = time.time() - start_time
                    rate = indexed_files / elapsed if elapsed > 0 else 0
                    eta = (total_files - indexed_files) / rate if rate > 0 else 0
                    
                    typer.echo(
                        f"Progress: {indexed_files}/{total_files} files "
                        f"({indexed_files/total_files*100:.1f}%) - "
                        f"{rate:.1f} files/sec - "
                        f"ETA: {eta:.0f}s"
                    )
        
        # Add remaining documents
        if all_documents:
            try:
                self.collection.add(
                    documents=all_documents,
                    metadatas=all_metadatas,
                    ids=all_ids
                )
                total_chunks += len(all_documents)
            except Exception as e:
                typer.echo(f"Error adding final batch: {e}")
                errors += 1
        
        elapsed = time.time() - start_time
        typer.echo(f"\n✓ Indexing complete in {elapsed:.1f} seconds!")
        typer.echo(f"Indexed: {indexed_files} files, {total_chunks} chunks")
        typer.echo(f"Rate: {indexed_files/elapsed:.1f} files/sec")
        if errors > 0:
            typer.echo(f"Errors: {errors}")
        
        return indexed_files, total_chunks, errors


async def run_optimized_indexing(project_path: Path, signal_hub_dir: Path, fast_mode: bool = False, custom_extensions: str = None, force: bool = False):
    """Run the optimized indexing process."""
    db_path = signal_hub_dir / "db"
    db_path.mkdir(exist_ok=True)
    
    # Clear existing index if force is True
    if force:
        typer.echo("Clearing existing index...")
        import shutil
        if db_path.exists():
            shutil.rmtree(db_path)
        db_path.mkdir(exist_ok=True)
    
    # Check for onnxruntime
    try:
        import onnxruntime
    except ImportError:
        typer.echo("Error: onnxruntime not installed (required by ChromaDB)")
        typer.echo("Please run: pip install onnxruntime")
        raise typer.Exit(1)
    
    # Parse custom extensions if provided
    extensions_set = None
    if custom_extensions:
        extensions_set = set(ext.strip() if ext.startswith('.') else f'.{ext.strip()}' 
                            for ext in custom_extensions.split(','))
    
    indexer = OptimizedIndexer(db_path, project_path, fast_mode=fast_mode, custom_extensions=extensions_set)
    
    # Scan files
    files = indexer.scan_files()
    if not files:
        typer.echo("No files to index")
        return
    
    # Confirm with user for large codebases
    if len(files) > 1000:
        typer.echo(f"\nWarning: Large codebase detected ({len(files)} files)")
        if not typer.confirm("Continue with indexing?"):
            typer.echo("Indexing cancelled")
            return
    
    # Run indexing
    await indexer.index_files_batch(files)
    
    # Show collection stats
    try:
        count = indexer.collection.count()
        typer.echo(f"\nTotal documents in index: {count}")
    except:
        pass