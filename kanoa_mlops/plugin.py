"""
Plugin for kanoa CLI to manage local MLOps services.

All operations delegate to docker-compose for single source of truth.
Supports both:
  1. Development mode (running from cloned repo)
  2. PyPI install mode (templates copied via `kanoa init mlops`)
"""

import shutil
import subprocess
import sys
from pathlib import Path

from kanoa_mlops.config import get_mlops_path, set_mlops_path

# Rich for CLI output (graceful fallback if not available)
try:
    from rich.console import Console

    console = Console()
except ImportError:

    class Console:
        def print(self, *args, **kwargs):
            # Strip rich markup for plain print
            text = str(args[0]) if args else ""
            import re

            text = re.sub(r"\[/?[a-z ]+\]", "", text)
            print(text, **kwargs)

    console = Console()


def get_templates_path() -> Path:
    """Get the path to bundled templates in the package."""
    return Path(__file__).parent / "templates"


def resolve_mlops_path() -> Path | None:
    """
    Resolve the kanoa-mlops working directory.

    Priority:
      1. User config (~/.config/kanoa/mlops.toml)
      2. Development mode (running from cloned repo)
      3. None (not initialized)
    """
    # Check user config first
    config_path = get_mlops_path()
    if config_path:
        return config_path

    # Check if running from development repo
    repo_root = Path(__file__).resolve().parent.parent
    if (repo_root / "docker" / "ollama").exists():
        return repo_root

    return None


def run_docker_compose(
    compose_file: Path, action: str = "up", detach: bool = True
) -> bool:
    """
    Run docker-compose command.

    Args:
        compose_file: Path to docker-compose.yml
        action: 'up' or 'down'
        detach: Run in detached mode (for 'up')

    Returns:
        True on success, False on failure.
    """
    cmd = ["docker", "compose", "-f", str(compose_file), action]
    if action == "up" and detach:
        cmd.append("-d")

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        console.print("[red]Error: docker not found. Please install Docker.[/red]")
        return False


# =============================================================================
# Command Handlers
# =============================================================================


def handle_init(args) -> None:
    """Initialize kanoa-mlops in a directory by copying templates."""
    target_dir = Path(args.directory).resolve()

    # Get bundled templates
    templates_dir = get_templates_path()
    if not templates_dir.exists():
        console.print(
            "[red]Error: Templates not found. Package may be corrupted.[/red]"
        )
        sys.exit(1)

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy templates
    console.print(f"[blue]Initializing kanoa-mlops in {target_dir}...[/blue]")

    docker_src = templates_dir / "docker"
    docker_dst = target_dir / "docker"

    if docker_dst.exists() and not args.force:
        console.print(
            f"[yellow]Warning: {docker_dst} already exists. Use --force to overwrite.[/yellow]"
        )
        sys.exit(1)

    shutil.copytree(docker_src, docker_dst, dirs_exist_ok=True)

    # Save to user config
    set_mlops_path(target_dir)

    console.print(f"[green]✔ Initialized kanoa-mlops in {target_dir}[/green]")
    console.print("")
    console.print("Next steps:")
    console.print("  kanoa serve ollama      # Start Ollama server")
    console.print("  kanoa serve monitoring  # Start Prometheus + Grafana")
    console.print("  kanoa stop              # Stop all services")


def handle_serve(args) -> None:
    """Handle the 'serve' command by starting docker-compose services."""
    mlops_path = resolve_mlops_path()

    if not mlops_path:
        console.print("[red]Error: kanoa-mlops not initialized.[/red]")
        console.print("Run: kanoa init mlops --dir ./my-project")
        sys.exit(1)

    service = args.service
    docker_dir = mlops_path / "docker"

    service_map = {
        "ollama": docker_dir / "ollama" / "docker-compose.ollama.yml",
        "monitoring": docker_dir / "monitoring" / "docker-compose.yml",
    }

    if service == "all":
        for name, compose_file in service_map.items():
            if compose_file.exists():
                console.print(f"[blue]Starting {name}...[/blue]")
                run_docker_compose(compose_file, "up")
            else:
                console.print(
                    f"[yellow]Skipping {name}: compose file not found[/yellow]"
                )
    else:
        compose_file = service_map.get(service)
        if not compose_file or not compose_file.exists():
            console.print(f"[red]Error: {service} compose file not found.[/red]")
            sys.exit(1)

        console.print(f"[blue]Starting {service}...[/blue]")
        if not run_docker_compose(compose_file, "up"):
            console.print(f"[red]Failed to start {service}[/red]")
            sys.exit(1)

    # Print helpful info
    if service in ("ollama", "all"):
        console.print("[green]Ollama running at http://localhost:11434[/green]")
    if service in ("monitoring", "all"):
        console.print(
            "[green]Grafana running at http://localhost:3000 (admin/admin)[/green]"
        )


def handle_stop(args) -> None:
    """Handle the 'stop' command by stopping docker-compose services."""
    mlops_path = resolve_mlops_path()

    if not mlops_path:
        console.print("[yellow]No mlops path configured. Nothing to stop.[/yellow]")
        return

    service = getattr(args, "service", "all")
    docker_dir = mlops_path / "docker"

    service_map = {
        "ollama": docker_dir / "ollama" / "docker-compose.ollama.yml",
        "monitoring": docker_dir / "monitoring" / "docker-compose.yml",
    }

    if service == "all":
        for name, compose_file in service_map.items():
            if compose_file.exists():
                console.print(f"[blue]Stopping {name}...[/blue]")
                run_docker_compose(compose_file, "down")
    else:
        compose_file = service_map.get(service)
        if compose_file and compose_file.exists():
            console.print(f"[blue]Stopping {service}...[/blue]")
            run_docker_compose(compose_file, "down")

    console.print("[green]✔ Services stopped.[/green]")


def handle_restart(args) -> None:
    """Handle the 'restart' command."""
    # Stop then start
    handle_stop(args)
    handle_serve(args)


def handle_status(args) -> None:
    """Show current configuration and running services."""
    mlops_path = resolve_mlops_path()

    console.print("[bold]kanoa-mlops Status[/bold]")
    console.print("")

    if mlops_path:
        console.print(f"[green]✔ Configured path:[/green] {mlops_path}")
    else:
        console.print("[yellow]✘ Not initialized[/yellow]")
        console.print("  Run: kanoa init mlops --dir ./my-project")
        return

    # Check docker services
    console.print("")
    console.print("[bold]Services:[/bold]")

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.strip().split("\n"):
            if line and "kanoa" in line.lower():
                console.print(f"  {line}")
    except FileNotFoundError:
        console.print("  [yellow]Docker not available[/yellow]")


# =============================================================================
# CLI Registration
# =============================================================================

SERVICE_CHOICES = ["ollama", "monitoring", "all"]


def register(parser) -> None:
    """Register CLI subcommands with the kanoa CLI."""
    # init command
    init_parser = parser.add_parser(
        "init", help="Initialize kanoa-mlops in a directory"
    )
    init_parser.add_argument(
        "target",
        choices=["mlops"],
        help="What to initialize (currently only 'mlops')",
    )
    init_parser.add_argument(
        "--dir",
        "-d",
        dest="directory",
        default=".",
        help="Target directory (default: current directory)",
    )
    init_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files",
    )
    init_parser.set_defaults(func=handle_init)

    # serve command
    serve_parser = parser.add_parser(
        "serve", help="Start local services (Ollama, Monitoring)"
    )
    serve_parser.add_argument(
        "service",
        choices=SERVICE_CHOICES,
        default="all",
        nargs="?",
        help="Service to start (default: all)",
    )
    serve_parser.set_defaults(func=handle_serve)

    # stop command
    stop_parser = parser.add_parser("stop", help="Stop local services")
    stop_parser.add_argument(
        "service",
        choices=SERVICE_CHOICES,
        default="all",
        nargs="?",
        help="Service to stop (default: all)",
    )
    stop_parser.set_defaults(func=handle_stop)

    # restart command
    restart_parser = parser.add_parser("restart", help="Restart local services")
    restart_parser.add_argument(
        "service",
        choices=SERVICE_CHOICES,
        default="all",
        nargs="?",
        help="Service to restart (default: all)",
    )
    restart_parser.set_defaults(func=handle_restart)

    # status command
    status_parser = parser.add_parser(
        "status", help="Show kanoa-mlops configuration and service status"
    )
    status_parser.set_defaults(func=handle_status)
