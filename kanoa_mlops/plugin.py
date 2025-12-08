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
    import re

    class _FallbackConsole:
        def print(self, *args, **kwargs):
            # Strip rich markup for plain print
            text = str(args[0]) if args else ""
            text = re.sub(r"\[/?[a-z ]+\]", "", text)
            print(text, **kwargs)

    console = _FallbackConsole()  # type: ignore[assignment]


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
    # Try 'docker compose' (v2 plugin) first
    cmd = ["docker", "compose", "-f", str(compose_file), action]
    if action == "up" and detach:
        cmd.append("-d")

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        # Check if the failure was due to missing plugin
        is_plugin_missing = False
        try:
            subprocess.run(
                ["docker", "compose", "version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            is_plugin_missing = True

        if not is_plugin_missing:
            # It failed for a real reason (e.g. config error), don't retry with v1
            return False

        # Plugin is missing, print helpful message
        console.print(
            "[yellow]Warning: 'docker compose' (v2) command not found.[/yellow]"
        )
        console.print("It looks like the Docker Compose plugin is missing.")
        console.print("To install on Ubuntu/Debian:")
        console.print(
            "  [bold]sudo apt-get update && sudo apt-get install docker-compose-v2[/bold]"
        )
        console.print("")
        console.print("Attempting fallback to legacy 'docker-compose' (v1)...")

    except FileNotFoundError:
        console.print("[red]Error: docker not found. Please install Docker.[/red]")
        return False

    # Fallback: Try 'docker-compose' (standalone v1)
    cmd = ["docker-compose", "-f", str(compose_file), action]
    if action == "up" and detach:
        cmd.append("-d")

    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: Failed to run docker compose.[/red]")
        console.print("Please ensure you have Docker Compose installed:")
        console.print("  - Docker Desktop (Mac/Windows)")
        console.print("  - docker-compose-plugin (Linux)")
        console.print("  - or standalone docker-compose")
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
    service_map = get_initialized_services(mlops_path)

    if service is None:
        console.print("[bold]Available Services:[/bold]")
        for name in service_map:
            console.print(f"  • {name}")
        console.print("")
        console.print("Run [bold]kanoa serve <service>[/bold] to start one.")
        console.print("Run [bold]kanoa serve all[/bold] to start everything.")
        return

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
            console.print(f"[red]Error: Service '{service}' not found.[/red]")
            console.print("Available services:")
            for s in service_map:
                console.print(f"  - {s}")
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

    service = getattr(args, "service", None)
    service_map = get_initialized_services(mlops_path)

    if service is None:
        console.print("[bold]Available Services to Stop:[/bold]")
        for name in service_map:
            console.print(f"  • {name}")
        console.print("")
        console.print("Run [bold]kanoa stop <service>[/bold] to stop one.")
        console.print("Run [bold]kanoa stop all[/bold] to stop everything.")
        return

    if service == "all":
        for name, compose_file in service_map.items():
            if compose_file.exists():
                console.print(f"[blue]Stopping {name}...[/blue]")
                run_docker_compose(compose_file, "down")
    else:
        compose_file = service_map.get(service)
        if compose_file is not None and compose_file.exists():
            console.print(f"[blue]Stopping {service}...[/blue]")
            run_docker_compose(compose_file, "down")
        else:
            console.print(f"[red]Error: Service '{service}' not found.[/red]")

    console.print("[green]✔ Services stopped.[/green]")


def handle_restart(args) -> None:
    """Handle the 'restart' command."""
    if args.service is None:
        # Reuse handle_stop's listing logic or just print help
        # Since handle_stop(args) will print help if service is None, we can just call it?
        # But handle_serve also prints help.
        # Let's just print help here to be explicit.
        mlops_path = resolve_mlops_path()
        if mlops_path:
            service_map = get_initialized_services(mlops_path)
            console.print("[bold]Available Services to Restart:[/bold]")
            for name in service_map:
                console.print(f"  • {name}")
            console.print("")
            console.print("Run [bold]kanoa restart <service>[/bold] to restart one.")
            console.print("Run [bold]kanoa restart all[/bold] to restart everything.")
        return

    # Stop then start
    handle_stop(args)
    handle_serve(args)


def get_initialized_services(mlops_path: Path) -> dict[str, Path]:
    """Return a map of {service_name: compose_file_path} for initialized services."""
    docker_dir = mlops_path / "docker"
    services = {}

    # Check known services
    candidates = {
        "ollama": docker_dir / "ollama" / "docker-compose.ollama.yml",
        "monitoring": docker_dir / "monitoring" / "docker-compose.yml",
    }

    # Check vLLM templates if present
    vllm_dir = docker_dir / "vllm"
    if vllm_dir.exists():
        for f in vllm_dir.glob("docker-compose.*.yml"):
            name = f.stem.replace("docker-compose.", "")  # e.g. 'molmo' or 'gemma'
            services[f"vllm-{name}"] = f

    for name, path in candidates.items():
        if path.exists():
            services[name] = path

    return services


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
    console.print("[bold]Running Containers:[/bold]")

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
        )

        has_running = False
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:  # Header + at least one container
            for line in lines[1:]:
                if "kanoa" in line.lower():
                    console.print(f"  {line}")
                    has_running = True

        if not has_running:
            console.print("  [dim]No kanoa services running[/dim]")

    except FileNotFoundError:
        console.print("  [yellow]Docker not available[/yellow]")


def handle_list(args) -> None:
    """List available services and models."""
    mlops_path = resolve_mlops_path()
    if not mlops_path:
        console.print("[red]Error: kanoa-mlops not initialized.[/red]")
        return

    console.print("[bold]Available Services:[/bold]")
    services = get_initialized_services(mlops_path)
    if not services:
        console.print("  [dim]No services found in docker/ directory[/dim]")
    else:
        for name, path in services.items():
            console.print(f"  • {name:<15} [dim]({path.relative_to(mlops_path)})[/dim]")

    console.print("")
    console.print("[bold]Ollama Models:[/bold]")

    # Check if Ollama is running first
    try:
        # Try to list models via docker exec
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(services["ollama"]),
                "exec",
                "ollama",
                "ollama",
                "list",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            models = result.stdout.strip().split("\n")
            if len(models) > 1:  # Header + models
                for model in models[1:]:
                    console.print(f"  • {model}")
            else:
                console.print("  [dim]No models pulled[/dim]")
        else:
            console.print(
                "  [yellow]Ollama not running (start with `kanoa serve ollama`)[/yellow]"
            )
    except (KeyError, FileNotFoundError, subprocess.CalledProcessError):
        console.print(
            "  [dim]Ollama service not configured or Docker unavailable[/dim]"
        )

    console.print("")
    console.print("[bold]vLLM Models:[/bold]")
    console.print(
        "  [dim](Check docker/vllm/docker-compose.*.yml for configured models)[/dim]"
    )


# =============================================================================
# CLI Registration
# =============================================================================


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
        "serve", help="Start local services (Ollama, Monitoring, vLLM)"
    )
    serve_parser.add_argument(
        "service",
        default=None,
        nargs="?",
        help="Service to start (ollama, monitoring, vllm-*, or all)",
    )
    serve_parser.set_defaults(func=handle_serve)

    # stop command
    stop_parser = parser.add_parser("stop", help="Stop local services")
    stop_parser.add_argument(
        "service",
        default=None,
        nargs="?",
        help="Service to stop (default: list services)",
    )
    stop_parser.set_defaults(func=handle_stop)

    # restart command
    restart_parser = parser.add_parser("restart", help="Restart local services")
    restart_parser.add_argument(
        "service",
        default=None,
        nargs="?",
        help="Service to restart (default: list services)",
    )
    restart_parser.set_defaults(func=handle_restart)

    # status command
    status_parser = parser.add_parser(
        "status", help="Show configuration and running services"
    )
    status_parser.set_defaults(func=handle_status)

    # list command
    list_parser = parser.add_parser("list", help="List available services and models")
    list_parser.set_defaults(func=handle_list)
