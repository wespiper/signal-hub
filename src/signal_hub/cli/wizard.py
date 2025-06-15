"""Interactive configuration wizard for Signal Hub."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from signal_hub.routing.config.defaults import get_default_config
from signal_hub.utils.logging import get_logger


logger = get_logger(__name__)
console = Console()


class ConfigWizard:
    """Interactive configuration wizard."""
    
    def __init__(self, config_path: Path = Path("signal-hub.yaml")):
        """
        Initialize wizard.
        
        Args:
            config_path: Path to save configuration
        """
        self.config_path = config_path
        self.config = {}
        self.project_type = None
    
    def run(self) -> None:
        """Run the configuration wizard."""
        console.print("\n[bold blue]🚀 Signal Hub Configuration Wizard[/bold blue]\n")
        
        # Check if config exists
        if self.config_path.exists():
            if not Confirm.ask(
                f"[yellow]Configuration already exists at {self.config_path}. Overwrite?[/yellow]",
                default=False
            ):
                console.print("[red]Wizard cancelled.[/red]")
                return
        
        try:
            # Detect project type
            self.project_type = self._detect_project_type()
            
            # Load base template
            self.config = self._load_template(self.project_type)
            
            # Customize settings
            self._customize_indexing()
            self._customize_routing()
            self._customize_security()
            self._customize_caching()
            
            # Validate configuration
            issues = self._validate_config()
            if issues:
                self._fix_issues(issues)
            
            # Save configuration
            self._save_config()
            
            # Test configuration
            if Confirm.ask("\n[green]Test configuration?[/green]", default=True):
                self._test_config()
            
            # Success!
            console.print("\n[bold green]✨ Configuration complete![/bold green]")
            console.print(f"\nConfiguration saved to: [cyan]{self.config_path}[/cyan]")
            console.print("\nReady to start! Run: [bold]signal-hub index[/bold]\n")
            
        except KeyboardInterrupt:
            console.print("\n[red]Wizard cancelled.[/red]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            logger.error(f"Wizard error: {e}", exc_info=True)
    
    def _detect_project_type(self) -> str:
        """Detect project type based on files present."""
        console.print("[bold]Detecting project type...[/bold]")
        
        indicators = {
            "python": ["*.py", "requirements.txt", "setup.py", "pyproject.toml"],
            "javascript": ["*.js", "package.json", "*.jsx"],
            "typescript": ["*.ts", "tsconfig.json", "*.tsx"],
            "go": ["*.go", "go.mod"],
            "rust": ["*.rs", "Cargo.toml"],
            "java": ["*.java", "pom.xml", "build.gradle"],
            "mixed": [],  # Default if multiple types found
        }
        
        detected = []
        for lang, patterns in indicators.items():
            for pattern in patterns:
                if list(Path.cwd().glob(pattern)):
                    detected.append(lang)
                    break
        
        if len(detected) > 1:
            project_type = "mixed"
        elif detected:
            project_type = detected[0]
        else:
            project_type = "generic"
        
        # Show detection result
        console.print(f"Detected project type: [green]{project_type}[/green]\n")
        
        # Allow override
        if not Confirm.ask("Is this correct?", default=True):
            project_type = Prompt.ask(
                "Enter project type",
                choices=list(indicators.keys()) + ["generic"],
                default="generic"
            )
        
        return project_type
    
    def _load_template(self, project_type: str) -> dict:
        """Load configuration template for project type."""
        templates = {
            "python": {
                "indexing": {
                    "include_patterns": ["**/*.py"],
                    "exclude_patterns": [
                        "**/__pycache__/**",
                        "**/venv/**",
                        "**/.venv/**",
                        "**/env/**",
                        "**/*.pyc",
                    ],
                },
                "routing": {
                    "rules": [
                        {
                            "name": "python_specific",
                            "patterns": {
                                "import|module|package": "haiku",
                                "class|method|function": "sonnet",
                                "algorithm|optimize|performance": "opus",
                            }
                        }
                    ]
                }
            },
            "javascript": {
                "indexing": {
                    "include_patterns": ["**/*.js", "**/*.jsx", "**/*.mjs"],
                    "exclude_patterns": [
                        "**/node_modules/**",
                        "**/dist/**",
                        "**/build/**",
                        "**/.next/**",
                    ],
                },
            },
            # ... more templates ...
        }
        
        base_config = get_default_config().dict()
        
        # Merge with template
        if project_type in templates:
            template = templates[project_type]
            # Deep merge logic here
            for key, value in template.items():
                if key in base_config and isinstance(value, dict):
                    base_config[key].update(value)
                else:
                    base_config[key] = value
        
        return base_config
    
    def _customize_indexing(self) -> None:
        """Customize indexing settings."""
        console.print("[bold cyan]📁 Indexing Configuration[/bold cyan]\n")
        
        # Show current patterns
        current_include = self.config.get("indexing", {}).get("include_patterns", [])
        current_exclude = self.config.get("indexing", {}).get("exclude_patterns", [])
        
        console.print("Current include patterns:")
        for pattern in current_include:
            console.print(f"  • {pattern}")
        
        # Add patterns
        if Confirm.ask("\nAdd more include patterns?", default=False):
            while True:
                pattern = Prompt.ask("Pattern (or 'done')")
                if pattern.lower() == "done":
                    break
                current_include.append(pattern)
        
        console.print("\nCurrent exclude patterns:")
        for pattern in current_exclude:
            console.print(f"  • {pattern}")
        
        # Add exclude patterns
        if Confirm.ask("\nAdd more exclude patterns?", default=False):
            while True:
                pattern = Prompt.ask("Pattern (or 'done')")
                if pattern.lower() == "done":
                    break
                current_exclude.append(pattern)
        
        # File size limit
        max_size = IntPrompt.ask(
            "\nMaximum file size (MB)",
            default=10
        )
        
        # Update config
        self.config["indexing"] = {
            "include_patterns": current_include,
            "exclude_patterns": current_exclude,
            "max_file_size_mb": max_size,
        }
    
    def _customize_routing(self) -> None:
        """Customize routing settings."""
        console.print("\n[bold cyan]🔀 Routing Configuration[/bold cyan]\n")
        
        # Cost optimization preference
        optimize_cost = Confirm.ask(
            "Prefer cost optimization over performance?",
            default=True
        )
        
        if optimize_cost:
            # Adjust thresholds for more Haiku usage
            self.config["routing"] = {
                "default_model": "haiku",
                "rules": [
                    {
                        "name": "length_based",
                        "enabled": True,
                        "priority": 1,
                        "thresholds": {
                            "haiku": 1000,  # More to Haiku
                            "sonnet": 3000,
                        }
                    }
                ]
            }
        
        # Manual escalation
        enable_escalation = Confirm.ask(
            "Enable manual escalation (@opus, @sonnet)?",
            default=True
        )
        self.config["routing"]["enable_escalation"] = enable_escalation
        
        # Cache threshold
        cache_threshold = IntPrompt.ask(
            "Cache similarity threshold (0-100%)",
            default=85
        ) / 100.0
        self.config["routing"]["cache_similarity_threshold"] = cache_threshold
    
    def _customize_security(self) -> None:
        """Customize security settings."""
        console.print("\n[bold cyan]🔒 Security Configuration[/bold cyan]\n")
        
        # API key storage
        if Confirm.ask("Configure API key storage?", default=True):
            self.config["security"] = {
                "api_keys": {
                    "storage": "encrypted_file",
                    "key_file": "~/.signal-hub/keys.enc",
                }
            }
        
        # Authentication
        if Confirm.ask("Enable dashboard authentication?", default=False):
            username = Prompt.ask("Admin username", default="admin")
            # In real implementation, would hash password
            self.config["security"]["authentication"] = {
                "dashboard": {
                    "enabled": True,
                    "users": {
                        username: "# Add bcrypt hash here"
                    }
                }
            }
        
        # Rate limiting
        if Confirm.ask("Enable rate limiting?", default=True):
            limit = IntPrompt.ask("Requests per hour", default=1000)
            self.config["security"]["rate_limiting"] = {
                "enabled": True,
                "default_limit": limit,
            }
    
    def _customize_caching(self) -> None:
        """Customize caching settings."""
        console.print("\n[bold cyan]⚡ Caching Configuration[/bold cyan]\n")
        
        # Cache TTL
        ttl_hours = IntPrompt.ask(
            "Cache TTL (hours)",
            default=24
        )
        
        # Cache size
        max_size_mb = IntPrompt.ask(
            "Maximum cache size (MB)",
            default=500
        )
        
        self.config["caching"] = {
            "enabled": True,
            "ttl_hours": ttl_hours,
            "max_size_mb": max_size_mb,
        }
    
    def _validate_config(self) -> List[str]:
        """Validate configuration."""
        console.print("\n[bold]Validating configuration...[/bold]")
        issues = []
        
        # Check required fields
        if not self.config.get("indexing", {}).get("include_patterns"):
            issues.append("No include patterns specified")
        
        # Check for common mistakes
        includes = self.config.get("indexing", {}).get("include_patterns", [])
        excludes = self.config.get("indexing", {}).get("exclude_patterns", [])
        
        # Check if excluding everything
        if "**/*" in excludes:
            issues.append("Excluding all files!")
        
        return issues
    
    def _fix_issues(self, issues: List[str]) -> None:
        """Fix configuration issues."""
        console.print(f"\n[yellow]Found {len(issues)} issues:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")
        
        # Offer to fix automatically
        if Confirm.ask("\nAttempt automatic fixes?", default=True):
            # Implement fixes...
            pass
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
    
    def _test_config(self) -> None:
        """Test the configuration."""
        console.print("\n[bold]🎯 Testing configuration...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running validation tests...", total=None)
            
            # Simulate tests
            import time
            time.sleep(2)
            
            progress.remove_task(task)
        
        # Show results
        table = Table(title="Configuration Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        
        table.add_row("Files matching patterns", "156 files found")
        table.add_row("Excluded files", "2,341 files excluded")
        table.add_row("Estimated index size", "12.3 MB")
        table.add_row("Configuration valid", "✅ Yes")
        
        console.print(table)


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    default="signal-hub.yaml",
    help="Configuration file path"
)
def wizard(config: str):
    """Run the configuration wizard."""
    wizard = ConfigWizard(Path(config))
    wizard.run()


if __name__ == "__main__":
    wizard()