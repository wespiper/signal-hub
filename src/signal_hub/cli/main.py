"""Signal Hub CLI interface."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from signal_hub import get_version_string
from signal_hub.core.features import get_edition, is_feature_enabled, Feature

def version_callback(value: bool):
    """Show version when --version is passed."""
    if value:
        version_str = get_version_string()
        typer.echo(version_str)
        raise typer.Exit()


app = typer.Typer(
    name="signal-hub",
    help="Signal Hub - Intelligent MCP server for RAG-enhanced development",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Signal Hub - Intelligent MCP server for RAG-enhanced development."""
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def version():
    """Show Signal Hub version and edition."""
    print(f"[bold blue]{get_version_string()}[/bold blue]")
    
    # Show enabled features
    edition = get_edition()
    print(f"\nEdition: [bold]{edition.value.title()}[/bold]")
    
    if os.getenv("SIGNAL_HUB_EARLY_ACCESS", "false").lower() == "true":
        print("[yellow]Early Access Mode: All features enabled![/yellow]")
    
    # Display feature availability
    table = Table(title="Feature Availability")
    table.add_column("Feature", style="cyan")
    table.add_column("Status", style="green")
    
    features = [
        ("Basic RAG & Search", Feature.BASIC_SEARCH),
        ("Rule-based Routing", Feature.BASIC_ROUTING),
        ("Semantic Caching", Feature.BASIC_CACHING),
        ("ML-powered Routing", Feature.ML_ROUTING),
        ("Learning Algorithms", Feature.LEARNING_ALGORITHMS),
        ("Advanced Analytics", Feature.ADVANCED_ANALYTICS),
        ("Team Management", Feature.TEAM_MANAGEMENT),
        ("SSO Integration", Feature.SSO_INTEGRATION),
    ]
    
    for name, feature in features:
        status = "✅ Enabled" if is_feature_enabled(feature) else "❌ Disabled"
        table.add_row(name, status)
    
    console.print(table)


@app.command()
def serve(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    host: Optional[str] = typer.Option(
        None,
        "--host",
        help="Server host (overrides config)",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Server port (overrides config)",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development",
    ),
):
    """Start the Signal Hub MCP server."""
    print(f"[bold blue]{get_version_string()}[/bold blue]")
    print("\n[yellow]Starting Signal Hub server...[/yellow]")
    
    # Check if MCP is available
    try:
        from signal_hub.core.server import run_server
        import mcp
    except ImportError:
        print("\n[red]Error: MCP SDK not installed![/red]")
        print("Please install the MCP SDK:")
        print("  pip install mcp")
        print("\nOr install all dependencies:")
        print("  poetry install")
        return
    
    # Run the server
    try:
        import asyncio
        
        config_path = str(config) if config else None
        
        if reload:
            print("[yellow]Note: Auto-reload not yet implemented[/yellow]")
        
        # Run the async server
        asyncio.run(run_server(config_path, host, port))
        
    except KeyboardInterrupt:
        print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        print(f"\n[red]Error: {str(e)}[/red]")
        console.print_exception()


@app.command()
def index(
    path: Path = typer.Argument(
        ...,
        help="Path to codebase to index",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        help="Recursively index subdirectories",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-indexing of all files",
    ),
):
    """Index a codebase for semantic search."""
    print(f"[bold blue]Indexing codebase at: {path}[/bold blue]")
    
    # This will be implemented in SH-S01-004
    print("\n[red]Error: Indexing not yet implemented (SH-S01-004)[/red]")
    print("Codebase scanning will be implemented in a future ticket.")


@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search query",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results",
    ),
):
    """Search indexed codebase."""
    print(f"[bold blue]Searching for: {query}[/bold blue]")
    
    # This will be implemented in Sprint 2
    print("\n[red]Error: Search not yet implemented (Sprint 2)[/red]")
    print("Semantic search will be implemented in Sprint 2.")


@app.command()
def init(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Project path to initialize"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinitialization"
    ),
):
    """Initialize Signal Hub for a project."""
    project_path = path.resolve()
    signal_hub_dir = project_path / ".signal-hub"
    config_file = signal_hub_dir / "config.yaml"
    
    # Check if already initialized
    if signal_hub_dir.exists() and not force:
        print(f"[yellow]Signal Hub already initialized at {project_path}[/yellow]")
        print("Use --force to reinitialize")
        return
    
    # Create directories
    print(f"[bold blue]Initializing Signal Hub at {project_path}[/bold blue]")
    signal_hub_dir.mkdir(exist_ok=True)
    (signal_hub_dir / "db").mkdir(exist_ok=True)
    (signal_hub_dir / "logs").mkdir(exist_ok=True)
    
    # Create default config
    default_config = """# Signal Hub Configuration
project:
  name: {project_name}
  path: {project_path}

edition: basic  # basic, pro, or enterprise
early_access: false  # Set to true to enable all features

server:
  host: localhost
  port: 3333

indexing:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.jsx"
    - "**/*.tsx"
    - "**/*.md"
  exclude:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/__pycache__/**"
    - "**/dist/**"
    - "**/build/**"

vector_store:
  type: chromadb
  persist_directory: .signal-hub/db

logging:
  level: INFO
  file: .signal-hub/logs/signal-hub.log
""".format(
        project_name=project_path.name,
        project_path=str(project_path)
    )
    
    config_file.write_text(default_config)
    
    # Create .gitignore
    gitignore = signal_hub_dir / ".gitignore"
    gitignore.write_text("db/\nlogs/\n")
    
    print("[green]✓[/green] Created .signal-hub directory")
    print("[green]✓[/green] Created default configuration")
    print("\nNext steps:")
    print("1. Index your codebase: [cyan]signal-hub index .[/cyan]")
    print("2. Start the server: [cyan]signal-hub serve[/cyan]")
    print("3. Configure Claude Code to use Signal Hub")
    

@app.command()
def config():
    """Show current configuration."""
    edition = get_edition()
    
    table = Table(title="Signal Hub Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Basic configuration
    table.add_row("Edition", edition.value.title())
    table.add_row("Early Access", os.getenv("SIGNAL_HUB_EARLY_ACCESS", "false"))
    table.add_row("Environment", os.getenv("SIGNAL_HUB_ENV", "development"))
    table.add_row("Log Level", os.getenv("SIGNAL_HUB_LOG_LEVEL", "INFO"))
    
    # Server settings
    table.add_row("Host", os.getenv("SIGNAL_HUB_HOST", "localhost"))
    table.add_row("Port", os.getenv("SIGNAL_HUB_PORT", "3333"))
    
    # Vector store
    table.add_row("Vector Store", os.getenv("SIGNAL_HUB_VECTOR_STORE", "chromadb"))
    
    console.print(table)


if __name__ == "__main__":
    app()