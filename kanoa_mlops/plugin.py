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

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console

from kanoa_mlops.arch_detect import detect_architecture
from kanoa_mlops.config import get_mlops_path, get_templates_path, set_mlops_path

import re

console = Console()


# Detect which compose client is available and cache it
def _detect_compose_client() -> list[str] | None:
    """Return the base command for docker compose: either ['docker','compose'] or ['docker-compose'].

    Returns None if no compose client is available.
    """
    try:
        # Prefer 'docker compose' (plugin)
        rc = subprocess.run(["docker", "compose", "version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc.returncode == 0:
            return ["docker", "compose"]
    except FileNotFoundError:
        pass

    try:
        rc = subprocess.run(["docker-compose", "--version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc.returncode == 0:
            return ["docker-compose"]
    except FileNotFoundError:
        pass

    return None


# Cached compose command used across functions
COMPOSE_CMD = _detect_compose_client()


def _parse_images_from_compose(compose_file: Path) -> list[str]:
    """Naively parse `image:` lines from a docker-compose YAML file.

    This is intentionally lightweight (regex) to avoid adding PyYAML runtime dependency.
    """
    images: list[str] = []
    try:
        text = compose_file.read_text()
    except Exception:
        return images

    for m in re.finditer(r"^\s*image:\s*(\S+)", text, flags=re.MULTILINE):
        images.append(m.group(1).strip())
    return images


def _image_exists(image: str) -> bool:
    """Return True if a Docker image with this name:tag exists locally."""
    try:
        result = subprocess.run(["docker", "images", "-q", image], capture_output=True, text=True)
        return bool(result.stdout.strip())
    except FileNotFoundError:
        return False

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
        # Normalize to Path and ensure it exists; ignore invalid config values
        try:
            p = Path(config_path)
        except Exception:
            return None
        if p.exists():
            return p.resolve()
        else:
            console.print(f"[yellow]Warning: configured mlops path does not exist: {p}[/yellow]")
            # fall through to dev-mode detection

    # Check if running from development repo
    repo_root = Path(__file__).resolve().parent.parent
    templates_docker = repo_root / "kanoa_mlops" / "templates" / "docker"
    if (templates_docker / "ollama").exists():
        return templates_docker.parent  # Return templates/ directory

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
    # Build the command using the detected compose client
    if COMPOSE_CMD is None:
        console.print("[red]Error: No Docker Compose client found (docker compose or docker-compose)[/red]")
        return False

    cmd = COMPOSE_CMD + ["-f", str(compose_file), action]
    if action == "up" and detach:
        cmd.append("-d")

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        # DIAGNOSTIC: Check for permission issues (docker group)
        try:
            subprocess.run(
                ["docker", "info"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            err_msg = None
            if getattr(e, "stderr", None):
                try:
                    err_msg = e.stderr.decode().lower()
                except Exception:
                    err_msg = str(e)
            else:
                err_msg = str(e).lower()

            if "permission denied" in err_msg and "docker.sock" in err_msg:
                console.print(
                    "[red]Error: Permission denied accessing Docker daemon.[/red]"
                )
                console.print("You need to add your user to the 'docker' group:")
                console.print("  [bold]sudo usermod -aG docker $USER[/bold]")
                console.print(
                    "  [dim](You may need to log out and back in for this to take effect)[/dim]"
                )
                return False

        console.print("[red]Error: docker compose command failed.[/red]")
        return False
    except FileNotFoundError:
        console.print("[red]Error: docker not found. Please install Docker.[/red]")
        return False


def _ignore_jinja_templates(dir, files):
    """Ignore .j2 template files during copytree."""
    return [f for f in files if f.endswith('.j2')]


def _render_templates(templates_dir: Path, target_dir: Path, arch_config):
    """
    Render Jinja2 templates with architecture-specific values.
    
    Args:
        templates_dir: Source templates directory
        target_dir: Target output directory
        arch_config: ArchConfig from arch_detect
    """
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    # Find all .j2 template files
    for template_file in templates_dir.rglob("*.j2"):
        rel_path = template_file.relative_to(templates_dir)
        output_path = target_dir / str(rel_path).rstrip('.j2')
        
        # Render template
        template = env.get_template(str(rel_path))
        rendered = template.render(arch_config=arch_config)
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
        console.print(f"  [dim]→ Rendered {rel_path} → {output_path.name}[/dim]")


# =============================================================================
# Command Handlers
# =============================================================================


def handle_init(args) -> None:
    """Initialize kanoa-mlops in a directory by copying templates."""
    target_dir = Path(args.directory).resolve()

    # Detect hardware architecture
    arch_config = detect_architecture()
    console.print(f"[cyan]Detected: {arch_config.description}[/cyan]")

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

    # Ensure the templates actually include the expected `docker/` subtree
    if not docker_src.exists():
        console.print(
            f"[red]Error: bundled templates do not include 'docker' directory: {docker_src}[/red]"
        )
        sys.exit(1)

    try:
        # Copy static files (non-.j2)
        shutil.copytree(docker_src, docker_dst, dirs_exist_ok=True, ignore=_ignore_jinja_templates)
        
        # Render Jinja2 templates
        _render_templates(templates_dir, target_dir, arch_config)
        
    except PermissionError:
        console.print(f"[red]Error: Permission denied copying templates to {docker_dst}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: Failed to copy templates: {e}[/red]")
        sys.exit(1)

    # Save to user config
    set_mlops_path(target_dir)

    console.print(f"[green]✔ Initialized kanoa-mlops in {target_dir}[/green]")
    console.print(f"[green]  Platform: {arch_config.platform_name}[/green]")
    console.print(f"[green]  vLLM Image: {arch_config.vllm_image}[/green]")
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
            if not compose_file.exists():
                console.print(f"[yellow]Skipping {name}: compose file not found[/yellow]")
                continue

            console.print(f"[blue]Starting {name}...[/blue]")

            # Auto-build missing images referenced by this compose file
            images = _parse_images_from_compose(compose_file)
            missing = [img for img in images if not _image_exists(img)]
            if missing:
                console.print(
                    f"[yellow]Detected missing images for {name}: {', '.join(missing)}. Building first...[/yellow]"
                )
                if COMPOSE_CMD is None:
                    console.print("[red]Error: No Docker Compose client available to build images.[/red]")
                    continue
                try:
                    subprocess.run(COMPOSE_CMD + ["-f", str(compose_file), "build"], check=True)
                except subprocess.CalledProcessError:
                    console.print(f"[red]Failed to build images for {name}, skipping start.[/red]")
                    continue

            run_docker_compose(compose_file, "up")
    else:
        compose_file = service_map.get(service)
        if not compose_file or not compose_file.exists():
            console.print(f"[red]Error: Service '{service}' not found.[/red]")
            console.print("Available services:")
            for s in service_map:
                console.print(f"  - {s}")
            sys.exit(1)

        console.print(f"[blue]Starting {service}...[/blue]")
        # Auto-build missing images for this service before starting
        images = _parse_images_from_compose(compose_file)
        missing = [img for img in images if not _image_exists(img)]
        if missing:
            console.print(f"[yellow]Detected missing images: {', '.join(missing)}. Building first...[/yellow]")
            if COMPOSE_CMD is None:
                console.print("[red]Error: No Docker Compose client available to build images.[/red]")
                sys.exit(1)
            try:
                subprocess.run(COMPOSE_CMD + ["-f", str(compose_file), "build"], check=True)
            except subprocess.CalledProcessError:
                console.print(f"[red]Failed to build images for {service}[/red]")
                sys.exit(1)

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
        # Ensure Ollama compose file is configured
        ollama_compose = services.get("ollama")
        if not ollama_compose or not ollama_compose.exists():
            console.print("  [dim]Ollama service not configured[/dim]")
            return

        if COMPOSE_CMD is None:
            console.print("  [dim]Docker Compose not available to query Ollama[/dim]")
            return

        # Try to list models via docker exec
        result = subprocess.run(
            COMPOSE_CMD + ["-f", str(ollama_compose), "exec", "ollama", "ollama", "list"],
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
