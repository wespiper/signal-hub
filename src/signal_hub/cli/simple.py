"""Simplified Signal Hub CLI to diagnose issues."""

import os
import sys
from pathlib import Path
from typing import Optional
import asyncio

# Simple version handling without Typer first
if len(sys.argv) == 2 and sys.argv[1] in ["--version", "-v"]:
    try:
        from signal_hub import get_version_string
        print(get_version_string())
    except ImportError:
        print("Signal Hub 0.1.0")
    sys.exit(0)

# Now import Typer and disable Rich
try:
    import typer
    # Disable Rich formatting entirely to avoid compatibility issues
    import os
    os.environ["_TYPER_STANDARD_TRACEBACK"] = "1"
    os.environ["_TYPER_COMPLETE_DISABLE_RICH"] = "1"
except ImportError:
    print("Error: Typer not installed. Please run: pip install typer")
    sys.exit(1)

# Create app without any callbacks first
app = typer.Typer(
    name="signal-hub",
    help="Signal Hub - Intelligent MCP server for RAG-enhanced development",
    add_completion=False,
    pretty_exceptions_enable=False,  # Disable rich exceptions
    rich_markup_mode=None,  # Disable rich markup
)


@app.command()
def version():
    """Show Signal Hub version and edition."""
    try:
        from signal_hub import get_version_string
        typer.echo(get_version_string())
    except ImportError:
        typer.echo("Signal Hub 0.1.0")


@app.command()
def serve(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
    host: Optional[str] = typer.Option(None, "--host", help="Server host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Server port"),
):
    """Start the Signal Hub MCP server."""
    typer.echo(f"Starting Signal Hub server...")
    typer.echo(f"Config: {config}")
    typer.echo(f"Host: {host or 'localhost'}")
    typer.echo(f"Port: {port or 3333}")
    
    # Import server only when needed
    try:
        from signal_hub.core.server import run_server
        import asyncio
        asyncio.run(run_server(str(config) if config else None, host, port))
    except ImportError as e:
        typer.echo(f"Error: Missing dependencies - {e}")
        typer.echo("Please ensure all dependencies are installed")
        sys.exit(1)
    except KeyboardInterrupt:
        typer.echo("\nServer stopped by user")
    except Exception as e:
        typer.echo(f"Error: {e}")
        sys.exit(1)


@app.command()
def init(
    path: Path = typer.Argument(".", help="Project path to initialize"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinitialization"),
):
    """Initialize Signal Hub for a project."""
    project_path = path.resolve()
    signal_hub_dir = project_path / ".signal-hub"
    
    if signal_hub_dir.exists() and not force:
        typer.echo(f"Signal Hub already initialized at {project_path}")
        typer.echo("Use --force to reinitialize")
        return
    
    typer.echo(f"Initializing Signal Hub at {project_path}")
    signal_hub_dir.mkdir(exist_ok=True)
    (signal_hub_dir / "db").mkdir(exist_ok=True)
    (signal_hub_dir / "logs").mkdir(exist_ok=True)
    
    config_file = signal_hub_dir / "config.yaml"
    config_content = f"""# Signal Hub Configuration
project:
  name: {project_path.name}
  path: {project_path}

edition: basic
early_access: false

server:
  host: localhost
  port: 3333

vector_store:
  type: chromadb
  persist_directory: .signal-hub/db
"""
    
    config_file.write_text(config_content)
    
    typer.echo("✓ Created .signal-hub directory")
    typer.echo("✓ Created default configuration")
    typer.echo("\nNext steps:")
    typer.echo("1. Index your codebase: signal-hub index .")
    typer.echo("2. Start the server: signal-hub serve")


@app.command()
def index(
    path: Path = typer.Argument(".", help="Path to codebase to index"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Recursively index subdirectories"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-indexing of all files"),
    fast: bool = typer.Option(False, "--fast", help="Fast mode: larger chunks, less precision"),
    local: bool = typer.Option(False, "--local", "-l", help="Use local embeddings for semantic search"),
    extensions: str = typer.Option(None, "--extensions", "-e", help="Comma-separated list of file extensions to index (e.g., '.py,.js')"),
):
    """Index a codebase for semantic search.
    
    Examples:
        signal-hub index .                    # Fast exact-match indexing
        signal-hub index . --local            # Semantic search with local embeddings
        signal-hub index . --fast             # Fast indexing with larger chunks
        signal-hub index . -e ".py,.js,.md"   # Only index specific file types
    """
    project_path = path.resolve()
    typer.echo(f"Indexing codebase at: {project_path}")
    
    # Check if Signal Hub is initialized
    signal_hub_dir = project_path / ".signal-hub"
    if not signal_hub_dir.exists():
        typer.echo("Error: Signal Hub not initialized in this directory")
        typer.echo("Run 'signal-hub init' first")
        raise typer.Exit(1)
    
    try:
        # Import indexing components with fallback
        import asyncio
        try:
            from signal_hub.indexing.scanner import CodebaseScanner
            from signal_hub.indexing.embeddings.service import EmbeddingService
            from signal_hub.indexing.chunking.strategy import ChunkingStrategy
            from signal_hub.indexing.parsers.registry import ParserRegistry
            from signal_hub.storage.adapters.chromadb import ChromaDBAdapter
            from signal_hub.config.settings import Settings
        except (ImportError, Exception) as e:
            # Fallback for simpler demo
            if "onnxruntime" not in str(e):
                typer.echo(f"Import error: {e}")
            # Don't mention the error if it's just onnxruntime
            pass
            
            # Use optimized indexing implementation
            typer.echo("Using fallback indexing (some components not available)")
            
            # Check if user wants local embeddings
            if local:
                typer.echo("Using local embeddings for semantic search")
                # Check if onnxruntime is available before importing
                try:
                    import onnxruntime
                    # If successful, use full embeddings
                    from signal_hub.cli.indexing_local import index_with_local_embeddings
                    asyncio.run(index_with_local_embeddings(project_path, signal_hub_dir))
                except (ImportError, Exception) as e:
                    if "onnxruntime" in str(e) or "dlopen" in str(e) or isinstance(e, ImportError):
                        typer.echo("\n⚠️  ONNXRuntime not available or incompatible with your system.")
                        typer.echo("Using lightweight TF-IDF search instead...\n")
                        from signal_hub.cli.indexing_local_lite import index_with_local_lite
                        asyncio.run(index_with_local_lite(project_path, signal_hub_dir))
                    else:
                        typer.echo(f"\nError: {e}")
                        raise
            else:
                # For large codebases, use minimal indexing (no embeddings)
                from signal_hub.cli.indexing_minimal import minimal_index
                minimal_index(project_path, signal_hub_dir)
            return
        
        # Load config
        config_file = signal_hub_dir / "config.yaml"
        settings = Settings()
        
        # Create indexing pipeline
        async def run_indexing():
            # Initialize components
            store = ChromaDBAdapter(settings.vector_store)
            await store.initialize()
            
            scanner = CodebaseScanner()
            embedding_service = EmbeddingService(settings.embeddings)
            parser_registry = ParserRegistry()
            
            # Scan directory
            typer.echo(f"Scanning {project_path}...")
            files = await scanner.scan(project_path)
            typer.echo(f"Found {len(files)} files")
            
            if not files:
                typer.echo("No files to index")
                return
            
            # Process files
            indexed = 0
            errors = 0
            
            for file_info in files:
                try:
                    # Parse file
                    parser = parser_registry.get_parser(file_info.path)
                    if not parser:
                        continue
                    
                    content = file_info.path.read_text(encoding='utf-8')
                    parsed = await parser.parse(content, str(file_info.path))
                    
                    # Chunk content
                    chunks = ChunkingStrategy.chunk_code(
                        parsed.content,
                        language=file_info.extension.lstrip('.'),
                        max_chunk_size=1000
                    )
                    
                    # Generate embeddings and store
                    for chunk in chunks:
                        embedding = await embedding_service.embed(chunk.content)
                        await store.add_documents([
                            {
                                'id': f"{file_info.path}:{chunk.start_line}",
                                'content': chunk.content,
                                'metadata': {
                                    'file_path': str(file_info.path),
                                    'start_line': chunk.start_line,
                                    'end_line': chunk.end_line,
                                    'language': file_info.extension,
                                },
                                'embedding': embedding
                            }
                        ])
                    
                    indexed += 1
                    if indexed % 10 == 0:
                        typer.echo(f"Indexed {indexed} files...")
                        
                except Exception as e:
                    errors += 1
                    typer.echo(f"Error indexing {file_info.path}: {e}")
            
            typer.echo(f"\n✓ Indexing complete!")
            typer.echo(f"Successfully indexed: {indexed} files")
            typer.echo(f"Errors: {errors} files")
            
            # Get stats
            stats = await store.get_stats()
            typer.echo(f"Total chunks in database: {stats.get('total_documents', 0)}")
        
        # Run the async function
        asyncio.run(run_indexing())
        
    except ImportError as e:
        typer.echo(f"Error: Missing dependencies - {e}")
        typer.echo("Some indexing components are not yet implemented")
        typer.echo("This feature will be fully available in Sprint 2")
    except Exception as e:
        typer.echo(f"Error during indexing: {e}")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
):
    """Search indexed codebase."""
    typer.echo(f"Searching for: {query}")
    
    # Check if Signal Hub is initialized
    signal_hub_dir = Path(".").resolve() / ".signal-hub"
    if not signal_hub_dir.exists():
        typer.echo("Error: Signal Hub not initialized in this directory")
        typer.echo("Run 'signal-hub init' first")
        raise typer.Exit(1)
    
    try:
        import asyncio
        import chromadb
        
        # Check if using minimal index
        db_path = signal_hub_dir / "db"
        if (db_path / "minimal_index.marker").exists():
            from signal_hub.cli.indexing_minimal import minimal_search
            minimal_search(query, signal_hub_dir, limit)
            return
        
        # Check if using lightweight local index
        if (db_path / "local_lite_index.marker").exists():
            from signal_hub.cli.indexing_local_lite import search_with_local_lite
            search_with_local_lite(query, signal_hub_dir, limit)
            return
        
        # Check if using local embeddings
        try:
            test_client = chromadb.PersistentClient(path=str(db_path))
            test_client.get_collection("signal_hub_local")
            from signal_hub.cli.indexing_local import search_with_local_embeddings
            search_with_local_embeddings(query, signal_hub_dir, limit)
            return
        except:
            pass  # Continue to other search methods
            
        async def run_search():
            # Use ChromaDB directly
            if not db_path.exists():
                typer.echo("Error: No index found. Run 'signal-hub index .' first")
                return
                
            client = chromadb.PersistentClient(path=str(db_path))
            
            try:
                # Try local embeddings first
                collection = client.get_collection("signal_hub_local")
            except:
                try:
                    # Try fast index
                    collection = client.get_collection("signal_hub_index_fast")
                except:
                    try:
                        # Fall back to regular index
                        collection = client.get_collection("signal_hub_index")
                    except:
                        typer.echo("Error: No index found. Run 'signal-hub index .' first")
                        return
            
            # Search using ChromaDB's built-in embedding
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            if not results or not results['documents'][0]:
                typer.echo("No results found")
                return
            
            typer.echo(f"\nFound {len(results['documents'][0])} results:\n")
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                score = 1 - (distance / 2)  # Convert distance to similarity score
                typer.echo(f"{i}. {metadata.get('file_path', 'Unknown')}:{metadata.get('start_line', '')}")
                typer.echo(f"   Score: {score:.3f}")
                preview = doc.replace('\n', ' ')[:100]
                typer.echo(f"   {preview}...")
                typer.echo()
        
        asyncio.run(run_search())
        
    except ImportError as e:
        typer.echo(f"Error: Search functionality not yet implemented")
        typer.echo("This feature will be available in Sprint 2")
    except Exception as e:
        typer.echo(f"Error during search: {e}")
        raise typer.Exit(1)


@app.command()
def config():
    """Show current configuration."""
    typer.echo("Signal Hub Configuration")
    typer.echo("-" * 40)
    typer.echo(f"Edition: basic")
    typer.echo(f"Early Access: {os.getenv('SIGNAL_HUB_EARLY_ACCESS', 'false')}")
    typer.echo(f"Environment: {os.getenv('SIGNAL_HUB_ENV', 'development')}")
    typer.echo(f"Host: {os.getenv('SIGNAL_HUB_HOST', 'localhost')}")
    typer.echo(f"Port: {os.getenv('SIGNAL_HUB_PORT', '3333')}")


if __name__ == "__main__":
    app()