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

app = typer.Typer(
    name="signal-hub",
    help="Signal Hub - Intelligent MCP server for RAG-enhanced development",
    add_completion=False,
)
console = Console()


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
    
    # This will be implemented in SH-S01-003
    print("\n[red]Error: Server implementation not yet complete (SH-S01-003)[/red]")
    print("The MCP server will be implemented in the next ticket.")
    
    # Show what would happen
    config_path = config or Path("config/dev.yaml")
    print(f"\nWould start server with:")
    print(f"  Config: {config_path}")
    if host:
        print(f"  Host: {host}")
    if port:
        print(f"  Port: {port}")
    if reload:
        print(f"  Auto-reload: Enabled")


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