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
):
    """Index a codebase for semantic search."""
    project_path = path.resolve()
    typer.echo(f"Indexing codebase at: {project_path}")
    
    # Check if Signal Hub is initialized
    signal_hub_dir = project_path / ".signal-hub"
    if not signal_hub_dir.exists():
        typer.echo("Error: Signal Hub not initialized in this directory")
        typer.echo("Run 'signal-hub init' first")
        raise typer.Exit(1)
    
    try:
        # Import indexing components
        from signal_hub.indexing.scanner import DirectoryScanner
        from signal_hub.indexing.pipeline import IndexingPipeline
        from signal_hub.storage.chromadb_store import ChromaDBStore
        from signal_hub.config.settings import Settings
        import asyncio
        
        # Load config
        config_file = signal_hub_dir / "config.yaml"
        settings = Settings()
        
        # Create pipeline
        async def run_indexing():
            # Initialize components
            store = ChromaDBStore(settings.vector_store)
            await store.initialize()
            
            scanner = DirectoryScanner()
            pipeline = IndexingPipeline(store, settings.indexing)
            
            # Scan directory
            typer.echo(f"Scanning {project_path}...")
            files = await scanner.scan_directory(project_path)
            typer.echo(f"Found {len(files)} files")
            
            # Index files
            typer.echo("Indexing files...")
            with typer.progressbar(files) as progress:
                for file_path in progress:
                    await pipeline.process_file(file_path)
            
            typer.echo("\n✓ Indexing complete!")
            stats = await store.get_stats()
            typer.echo(f"Total documents: {stats.get('total_documents', 0)}")
            typer.echo(f"Total chunks: {stats.get('total_chunks', 0)}")
        
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
        from signal_hub.retrieval.search import SearchEngine
        from signal_hub.storage.chromadb_store import ChromaDBStore
        from signal_hub.config.settings import Settings
        import asyncio
        
        async def run_search():
            settings = Settings()
            store = ChromaDBStore(settings.vector_store)
            await store.initialize()
            
            search_engine = SearchEngine(store)
            results = await search_engine.search(query, limit=limit)
            
            if not results:
                typer.echo("No results found")
                return
            
            typer.echo(f"\nFound {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                typer.echo(f"{i}. {result['file_path']}:{result.get('line_number', '')}")
                typer.echo(f"   Score: {result['score']:.3f}")
                typer.echo(f"   {result['content'][:100]}...")
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