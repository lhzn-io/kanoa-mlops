"""
Plugin for kanoa CLI to manage local MLOps services.

All operations delegate to Makefile targets for single source of truth.
"""

import subprocess
import sys
from pathlib import Path

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


def run_make(target: str, mlops_path: Path) -> bool:
    """Run a make target. Returns True on success."""
    try:
        subprocess.run(["make", target], cwd=mlops_path, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def handle_serve(args) -> None:
    """Handle the 'serve' command by delegating to Makefile."""
    mlops_path = get_kanoa_mlops_path()
    service = args.service

    if service == "all":
        run_make("serve-ollama", mlops_path)
        run_make("serve-monitoring", mlops_path)
    else:
        target = f"serve-{service}"
        if not run_make(target, mlops_path):
            console.print(f"[red]Failed to start {service}[/red]")
            sys.exit(1)


def handle_stop(args) -> None:
    """Handle the 'stop' command by delegating to Makefile."""
    mlops_path = get_kanoa_mlops_path()
    service = getattr(args, "service", "all")

    if service == "all":
        run_make("stop-all", mlops_path)
    else:
        target = f"stop-{service}"
        if not run_make(target, mlops_path):
            console.print(f"[red]Failed to stop {service}[/red]")
            sys.exit(1)


def handle_restart(args) -> None:
    """Handle the 'restart' command by delegating to Makefile."""
    mlops_path = get_kanoa_mlops_path()
    service = args.service

    if service == "all":
        run_make("restart-ollama", mlops_path)
        run_make("restart-monitoring", mlops_path)
    else:
        target = f"restart-{service}"
        if not run_make(target, mlops_path):
            console.print(f"[red]Failed to restart {service}[/red]")
            sys.exit(1)


SERVICE_CHOICES = ["ollama", "monitoring", "all"]


def register(parser) -> None:
    """Register CLI subcommands."""
    # Add 'serve' command (alias: up)
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

    # Add 'stop' command (alias: down)
    stop_parser = parser.add_parser("stop", help="Stop local services")
    stop_parser.add_argument(
        "service",
        choices=SERVICE_CHOICES,
        default="all",
        nargs="?",
        help="Service to stop (default: all)",
    )
    stop_parser.set_defaults(func=handle_stop)

    # Add 'restart' command
    restart_parser = parser.add_parser("restart", help="Restart local services")
    restart_parser.add_argument(
        "service",
        choices=SERVICE_CHOICES,
        default="all",
        nargs="?",
        help="Service to restart (default: all)",
    )
    restart_parser.set_defaults(func=handle_restart)
