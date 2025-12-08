"""
Plugin for kanoa CLI to manage local MLOps services.
"""

import contextlib
import subprocess
import sys
from pathlib import Path
from typing import List

# We don't want to depend on rich if kanoa-mlops is installed standalone,
# but since it's a plugin for kanoa, rich should be available.
try:
    from rich.console import Console
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args, **kwargs)
    console = Console()


def get_kanoa_mlops_path() -> Path:
    """
    Locate the kanoa-mlops repository root.
    
    Since this file is at kanoa_mlops/plugin.py, the repo root is 2 levels up.
    """
    return Path(__file__).resolve().parent.parent


def run_command(command: List[str], cwd: Path, description: str) -> None:
    """Run a shell command in the specified directory."""
    console.print(f"[bold blue]ℹ {description}...[/bold blue]")
    try:
        subprocess.run(command, cwd=cwd, check=True)
        console.print("[bold green]✔ Done.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]✘ Failed:[/bold red] {e}")
        sys.exit(1)


def serve_ollama(mlops_path: Path) -> None:
    """Start Ollama service."""
    run_command(
        ["make", "serve-ollama"],
        cwd=mlops_path,
        description="Starting Ollama service"
    )


def serve_monitoring(mlops_path: Path) -> None:
    """Start Monitoring stack."""
    run_command(
        ["make", "serve-monitoring"],
        cwd=mlops_path,
        description="Starting Monitoring stack"
    )


def stop_all(mlops_path: Path) -> None:
    """Stop all known services."""
    console.print("[bold yellow]Stopping all kanoa-mlops services...[/bold yellow]")

    # Stop Ollama
    with contextlib.suppress(Exception):
        run_command(
            ["docker", "compose", "-f", "docker/ollama/docker-compose.ollama.yml", "down"],
            cwd=mlops_path,
            description="Stopping Ollama"
        )

    # Stop Monitoring
    with contextlib.suppress(Exception):
         run_command(
            ["docker", "compose", "-f", "docker-compose.monitoring.yml", "down"],
            cwd=mlops_path,
            description="Stopping Monitoring"
        )

    console.print("[bold green]✔ All services stopped.[/bold green]")


def handle_serve(args) -> None:
    """Handle the 'serve' command."""
    mlops_path = get_kanoa_mlops_path()
    service = args.service

    if service == "ollama":
        serve_ollama(mlops_path)
    elif service == "monitoring":
        serve_monitoring(mlops_path)
    elif service == "all":
        serve_ollama(mlops_path)
        serve_monitoring(mlops_path)
    else:
        console.print(f"[red]Unknown service: {service}[/red]")


def handle_stop(args) -> None:
    """Handle the 'stop' command."""
    mlops_path = get_kanoa_mlops_path()
    stop_all(mlops_path)


def register(parser) -> None:
    """Register CLI subcommands."""
    # Add 'serve' command
    serve_parser = parser.add_parser("serve", help="Start local services (vLLM/Ollama/Monitoring)")
    serve_parser.add_argument(
        "service",
        choices=["ollama", "monitoring", "all"],
        default="all",
        nargs="?",
        help="Service to start"
    )
    serve_parser.set_defaults(func=handle_serve)

    # Add 'stop' command
    stop_parser = parser.add_parser("stop", help="Stop all local services")
    stop_parser.set_defaults(func=handle_stop)
