"""
Plugin for kanoa CLI to manage local MLOps services.

All operations delegate to docker-compose for single source of truth.
Supports both:
  1. Development mode (running from cloned repo)
  2. PyPI install mode (templates copied via `kanoa mlops init`)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from kanoa_mlops.arch_detect import detect_architecture
from kanoa_mlops.config import get_mlops_path, get_templates_path, set_mlops_path

console = Console()


def _is_tty() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _run_docker_command(
    args: list[str], timeout: int = 3
) -> subprocess.CompletedProcess | None:
    """Run a docker command with a timeout to prevent hanging."""
    try:
        return subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


# Detect which compose client is available and cache it
def _detect_compose_client() -> list[str] | None:
    """Return the base command for docker compose: either ['docker','compose'] or ['docker-compose'].

    Returns None if no compose client is available.
    """
    # Prefer 'docker compose' (plugin)
    rc = _run_docker_command(["docker", "compose", "version"], timeout=2)
    if rc and rc.returncode == 0:
        return ["docker", "compose"]

    # Fallback to docker-compose
    rc = _run_docker_command(["docker-compose", "--version"], timeout=2)
    if rc and rc.returncode == 0:
        return ["docker-compose"]

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

    images.extend(
        m.group(1).strip()
        for m in re.finditer(r"^\s*image:\s*(\S+)", text, flags=re.MULTILINE)
    )
    return images


def _image_exists(image: str) -> bool:
    """Return True if a Docker image with this name:tag exists locally."""
    result = _run_docker_command(["docker", "images", "-q", image])
    return bool(result and result.stdout.strip())


# Rich for CLI output (graceful fallback if not available)
try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.table import Table

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

    # Define dummy Prompt/Table to avoid NameError if referenced
    Prompt = None  # type: ignore[assignment, misc]
    Table = None  # type: ignore[assignment, misc]

HTTP_OK = 200
MIN_OLLAMA_PATH_PARTS = 3
MIN_VLLM_PARTS = 2


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
            console.print(
                f"[yellow]Warning: configured mlops path does not exist: {p}[/yellow]"
            )
            # fall through to dev-mode detection

    # Check if running from development repo
    repo_root = Path(__file__).resolve().parent.parent
    templates_docker = repo_root / "kanoa_mlops" / "templates" / "docker"
    if (templates_docker / "ollama").exists():
        return templates_docker.parent  # Return templates/ directory

    return None


def run_docker_compose(
    compose_file: Path, action: str = "up", detach: bool = True, env: dict | None = None
) -> bool:
    """
    Run docker-compose command.

    Args:
        compose_file: Path to docker-compose.yml
        action: 'up' or 'down'
        detach: Run in detached mode (for 'up')
        env: Optional environment variables to pass to docker-compose

    Returns:
        True on success, False on failure.
    """
    # Build the command using the detected compose client
    if COMPOSE_CMD is None:
        console.print(
            "[red]Error: No Docker Compose client found (docker compose or docker-compose)[/red]"
        )
        return False

    cmd = [*COMPOSE_CMD, "-f", str(compose_file), action]
    if action == "up" and detach:
        cmd.append("-d")

    try:
        # Merge environment variables if provided
        run_env = None
        if env:
            run_env = os.environ.copy()
            run_env.update(env)
        subprocess.run(cmd, check=True, env=run_env)
        return True
    except subprocess.CalledProcessError:
        # DIAGNOSTIC: Check for permission issues (docker group)
        try:
            # Use safe wrapper to avoid hanging if daemon is totally dead
            res = _run_docker_command(["docker", "info"], timeout=3)
            if res and res.returncode != 0:
                # Capture stderr if available
                err_msg = res.stderr.lower() if res.stderr else "unknown error"
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
        except Exception:
            pass

        console.print("[red]Error: docker compose command failed.[/red]")
        return False
    except FileNotFoundError:
        console.print("[red]Error: docker not found. Please install Docker.[/red]")
        return False


def _ignore_jinja_templates(dir, files):
    """Ignore .j2 template files during copytree."""
    return [f for f in files if f.endswith(".j2")]


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
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Find all .j2 template files
    for template_file in templates_dir.rglob("*.j2"):
        rel_path = template_file.relative_to(templates_dir)
        output_path = target_dir / str(rel_path).rstrip(".j2")

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
        shutil.copytree(
            docker_src, docker_dst, dirs_exist_ok=True, ignore=_ignore_jinja_templates
        )

        # Render Jinja2 templates
        _render_templates(templates_dir, target_dir, arch_config)

    except PermissionError:
        console.print(
            f"[red]Error: Permission denied copying templates to {docker_dst}[/red]"
        )
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
    console.print("  kanoa mlops serve             # Interactive service selection")
    console.print("  kanoa mlops list              # Show available models")
    console.print("  kanoa mlops status            # Check running services")


def _check_model_cached(model_name: str) -> tuple[bool, str]:
    """
    Check if a HuggingFace model is already cached locally and fully downloaded.

    Args:
        model_name: HuggingFace model ID (e.g., 'allenai/Olmo-3-7B-Think')

    Returns:
        Tuple of (is_complete, status_message):
            - (True, "complete") if model is fully downloaded
            - (False, "incomplete") if model exists but has incomplete files
            - (False, "missing") if model directory doesn't exist
    """
    # Check HF_HOME or default cache location
    hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    model_cache_name = model_name.replace("/", "--")
    model_dir = Path(hf_home) / "hub" / f"models--{model_cache_name}"

    if not model_dir.exists():
        return False, "missing"

    # Check for incomplete downloads
    blobs_dir = model_dir / "blobs"
    if blobs_dir.exists():
        incomplete_files = list(blobs_dir.glob("*.incomplete"))
        if incomplete_files:
            return False, "incomplete"

    return True, "complete"


def _list_cached_models() -> list[dict]:
    """
    List all cached HuggingFace models.

    Returns:
        List of dicts with model info: {name, path, status, size_gb}
    """
    hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    hub_dir = Path(hf_home) / "hub"

    if not hub_dir.exists():
        return []

    models = []
    for model_dir in hub_dir.glob("models--*"):
        # Convert directory name to model ID
        model_name = model_dir.name.replace("models--", "").replace("--", "/")

        # Check completion status
        is_complete, status = _check_model_cached(model_name)

        # Calculate approximate size (excluding symlinks to avoid double-counting)
        size_bytes = sum(
            f.stat().st_size
            for f in model_dir.rglob("*")
            if f.is_file() and not f.is_symlink()
        )
        size_gb = size_bytes / (1024**3)

        models.append(
            {
                "name": model_name,
                "path": model_dir,
                "status": status,
                "size_gb": size_gb,
                "complete": is_complete,
            }
        )

    return sorted(models, key=lambda x: x["name"])


def _list_ollama_models() -> list[dict]:
    """
    List locally available Ollama models from the manifest directory.

    Returns:
        List of dicts with model info: {name, size_gb}
    """
    ollama_home = os.environ.get("OLLAMA_MODELS", os.path.expanduser("~/.ollama"))
    manifests_dir = Path(ollama_home) / "models" / "manifests"

    if not manifests_dir.exists():
        return []

    models = []

    # Iterate through registry.ollama.ai/library/ and other registries
    for registry_dir in manifests_dir.rglob("*"):
        if registry_dir.is_dir():
            continue

        # Get relative path from manifests dir to construct model name
        rel_path = registry_dir.relative_to(manifests_dir)
        parts = rel_path.parts

        # Skip if not enough path parts
        if len(parts) < MIN_OLLAMA_PATH_PARTS:
            continue

        # Construct model name (registry/namespace/model:tag)
        # For ollama.ai models: library/modelname/tag -> modelname:tag
        if "library" in parts:
            idx = parts.index("library")
            if idx + 2 < len(parts):
                model_name = f"{parts[idx + 1]}:{parts[idx + 2]}"
            else:
                continue
        else:
            # For other registries, use full path
            model_name = "/".join(parts)

        # Try to get size from manifest
        size_gb = 0
        try:
            with open(registry_dir, "r") as f:
                manifest = json.load(f)
                # Ollama manifests have layers with sizes
                if "layers" in manifest:
                    size_bytes = sum(
                        layer.get("size", 0) for layer in manifest["layers"]
                    )
                    size_gb = size_bytes / (1024**3)
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            pass

        models.append(
            {
                "name": model_name,
                "size_gb": size_gb,
            }
        )

    return sorted(models, key=lambda x: x["name"])


def _select_ollama_model_interactive(family: str | None = None) -> str | None:
    """
    Show interactive menu to select an Ollama model.

    Args:
        family: Optional family filter (e.g., 'scout', 'llama3', 'gemma3')

    Returns:
        Selected model name or None if cancelled
    """
    models = _list_ollama_models()

    # Filter by family if specified
    if family:
        family_patterns = {
            "scout": ["scout"],
            "llama3": ["llama3"],
            "gemma3": ["gemma3"],
            "qwen": ["qwen"],
            "phi": ["phi"],
        }
        patterns = family_patterns.get(family.lower(), [])
        if patterns:
            models = [
                m
                for m in models
                if any(p.lower() in m["name"].lower() for p in patterns)
            ]

    if not models:
        if family:
            console.print(
                f"[yellow]No Ollama models found for {family} family[/yellow]"
            )
            console.print(
                "\nPull a model first (via container or with Ollama installed):"
            )
            if family == "scout":
                console.print(
                    "  [bold]docker exec kanoa-ollama ollama pull ingu627/llama4-scout-q4:109b[/bold]"
                )
            else:
                console.print(f"  [bold]ollama pull {family}[/bold]")
        else:
            console.print("[yellow]No Ollama models found in ~/.ollama/models[/yellow]")
            console.print("\nPull a model first:")
            console.print("  [bold]ollama pull llama3[/bold]")
        return None

    # Show table of available models
    title = f"Ollama Models - {family}" if family else "Ollama Models"
    table = Table(title=title)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Model", style="green")
    table.add_column("Size", justify="right", style="blue")

    for idx, model in enumerate(models, 1):
        table.add_row(str(idx), model["name"], f"{model['size_gb']:.1f} GB")

    console.print(table)
    console.print("")

    # Prompt for selection
    choice = str(
        Prompt.ask(
            "Select model number (or 'q' to quit)",
            choices=[str(i) for i in range(1, len(models) + 1)] + ["q"],
            default="q",
        )
    )

    if choice == "q":
        return None

    model_name: str = models[int(choice) - 1]["name"]
    return model_name


def _download_model_if_needed(model_name: str) -> bool:
    """
    Check if model is cached and complete, error if not.

    Args:
        model_name: HuggingFace model ID (e.g., 'allenai/Olmo-3-7B-Think')

    Returns:
        True if model is available and complete, False if missing or incomplete
    """
    console.print(f"[cyan]Checking cache for model: {model_name}...[/cyan]")

    is_complete, status = _check_model_cached(model_name)

    if is_complete:
        console.print(f"[green]✔ Model {model_name} found in cache[/green]")
        return True
    elif status == "incomplete":
        console.print(f"[red]✘ Model {model_name} download is incomplete[/red]")
        console.print("")
        console.print("[yellow]Download in progress or interrupted. Please:[/yellow]")
        console.print("  [bold]1. Check if download is still running[/bold]")
        console.print(
            f"  [bold]2. Restart the download: hf download {model_name}[/bold]"
        )
        console.print("")
        console.print("The HuggingFace CLI will resume from where it left off.")
        return False
    else:  # status == "missing"
        console.print(f"[red]✘ Model {model_name} not found in cache[/red]")
        console.print("")
        console.print("[yellow]Please download the model first:[/yellow]")
        console.print(f"  [bold]hf download {model_name}[/bold]")
        console.print("")
        console.print("Or download to a specific cache directory:")
        console.print(
            f"  [bold]hf download {model_name} --cache-dir ~/.cache/huggingface[/bold]"
        )
        return False


def _select_service_interactive(service_map: dict) -> str | None:
    """
    Show interactive menu to select a service.

    Args:
        service_map: Dict of {service_name: compose_file_path}

    Returns:
        Selected service name or None if cancelled
    """
    # Categorize services
    infrastructure: list[str] = []
    ml_runtimes: list[str] = []
    agent_platforms: list[str] = []
    vllm_families: list[str] = []

    for name in service_map:
        if name == "monitoring":
            infrastructure.append(name)
        elif name == "ollama":
            ml_runtimes.append(name)
        elif name == "openhands":
            agent_platforms.append(name)
        elif name.startswith("vllm-"):
            vllm_families.append(name.replace("vllm-", ""))

    table = Table(title="Available Services")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Service", style="green")
    table.add_column("Type", style="blue")

    choices = []
    idx = 1

    if infrastructure:
        for svc in infrastructure:
            table.add_row(str(idx), svc, "infrastructure")
            choices.append((idx, svc))
            idx += 1

    if agent_platforms:
        for svc in agent_platforms:
            table.add_row(str(idx), svc, "agent platform")
            choices.append((idx, svc))
            idx += 1

    if ml_runtimes:
        for svc in ml_runtimes:
            table.add_row(str(idx), svc, "ML runtime")
            choices.append((idx, svc))
            idx += 1

    if vllm_families:
        table.add_row(str(idx), "vllm (with model selection)", "ML runtime")
        choices.append((idx, "vllm"))
        idx += 1

    console.print(table)
    choice = str(
        Prompt.ask(
            "Select service",
            choices=[str(i) for i, _ in choices] + ["q"],
            default="q",
        )
    )

    if choice == "q":
        return None

    for idx, svc in choices:
        if idx == int(choice):
            return svc

    return None


def _select_vllm_family_interactive(service_map: dict) -> str | None:
    """
    Show interactive menu to select a vLLM model family.

    Args:
        service_map: Dict of {service_name: compose_file_path}

    Returns:
        Selected family name (e.g., 'gemma3') or None if cancelled
    """
    vllm_families: list[str] = [
        k.replace("vllm-", "") for k in service_map if k.startswith("vllm-")
    ]

    if not vllm_families:
        console.print("[red]No vLLM families configured.[/red]")
        return None

    table = Table(title="vLLM Model Families")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Family", style="green")
    table.add_column("Description", style="blue")

    family_desc = {
        "olmo3": "Allen AI OLMo 3 (text)",
        "gemma3": "Google Gemma 3 (multimodal)",
        "molmo": "Allen AI Molmo (multimodal vision)",
        "llama-scout": "Meta Llama 4 Scout 17B MoE (16 experts)",
        "scout": "Meta Llama 4 Scout 17B MoE (Ollama)",
    }

    for idx, family in enumerate(sorted(vllm_families), 1):
        desc = family_desc.get(family, "Model family")
        table.add_row(str(idx), family, desc)

    console.print(table)
    choice = str(
        Prompt.ask(
            "Select model family",
            choices=[str(i) for i in range(1, len(vllm_families) + 1)] + ["q"],
            default="q",
        )
    )

    if choice == "q":
        return None

    return sorted(vllm_families)[int(choice) - 1]


def _select_model_interactive(family: str | None = None) -> str | None:
    """
    Show interactive menu to select a cached model.

    Args:
        family: Optional family filter (e.g., 'gemma3', 'molmo', 'olmo3')

    Returns:
        Selected model name or None if cancelled
    """
    models = _list_cached_models()

    # Filter by family if specified
    if family:
        family_patterns = {
            "gemma3": ["google/gemma-3", "google/gemma3"],
            "molmo": ["allenai/molmo", "allenai/Molmo"],
            "olmo3": ["allenai/olmo-3", "allenai/Olmo-3"],
            "llama-scout": ["meta-llama/llama-4-scout", "meta-llama/Llama-4-Scout"],
            "scout": ["scout", "Scout"],  # For Ollama models
        }
        patterns = family_patterns.get(family.lower(), [])
        if patterns:
            models = [
                m
                for m in models
                if any(p.lower() in m["name"].lower() for p in patterns)
            ]

    if not models:
        if family:
            console.print(
                f"[yellow]No cached models found for {family} family[/yellow]"
            )
            console.print("\nDownload a model first:")
            if family == "gemma3":
                console.print("  [bold]hf download google/gemma-3-12b-it[/bold]")
            elif family == "molmo":
                console.print("  [bold]hf download allenai/Molmo-7B-D-0924[/bold]")
            elif family == "olmo3":
                console.print("  [bold]hf download allenai/Olmo-3-7B-Think[/bold]")
            elif family == "llama-scout":
                console.print(
                    "  [bold]hf download meta-llama/Llama-4-Scout-17B-16E-Instruct[/bold]"
                )
        else:
            console.print(
                "[yellow]No cached models found in ~/.cache/huggingface/hub[/yellow]"
            )
            console.print("\nDownload a model first:")
            console.print("  [bold]hf download allenai/Olmo-3-7B-Think[/bold]")
        return None

    # Show table of available models
    title = f"Cached Models - {family}" if family else "Cached Models"
    table = Table(title=title)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Model", style="green")
    table.add_column("Size", justify="right", style="blue")
    table.add_column("Status", style="yellow")

    complete_models: list[tuple[int, str]] = []
    for idx, model in enumerate(models, 1):
        status_icon = "✔" if model["complete"] else "✘"
        status_text = f"{status_icon} {model['status']}"

        if model["complete"]:
            complete_models.append((idx, model["name"]))
            table.add_row(
                str(idx), model["name"], f"{model['size_gb']:.1f} GB", status_text
            )

    if not complete_models:
        console.print("[yellow]No complete models found[/yellow]")
        console.print("\nComplete a model download first:")
        console.print("  [bold]hf download <model-name>[/bold]")
        return None

    console.print(table)
    console.print("")

    # Prompt for selection
    choice = str(
        Prompt.ask(
            "Select model number (or 'q' to quit)",
            choices=[str(i) for i, _ in complete_models] + ["q"],
            default="q",
        )
    )

    if choice == "q":
        return None

    # Find selected model
    selected_idx = int(choice)
    for idx, model_name in complete_models:
        if idx == selected_idx:
            return model_name

    return None


def handle_serve(args) -> None:
    """Handle the 'serve' command by starting docker-compose services."""
    mlops_path = resolve_mlops_path()

    if not mlops_path:
        console.print("[red]Error: kanoa-mlops not initialized.[/red]")
        console.print("Run: kanoa mlops init --dir ./my-project")
        sys.exit(1)

    # Check docker availability early
    if not _ensure_docker_available(interactive=True):
        sys.exit(1)

    runtime = getattr(args, "runtime", None)
    model_family = getattr(args, "model_family", None)
    service_map = get_initialized_services(mlops_path)

    # If no runtime specified and TTY available, start interactive flow
    if runtime is None and _is_tty():
        console.print("")
        console.print("[bold cyan]kanoa serve[/bold cyan] - MLOps Service Manager\n")

        runtime = _select_service_interactive(service_map)
        if runtime is None:
            console.print("[yellow]Cancelled.[/yellow]")
            sys.exit(0)

        console.print("")

    # If no runtime, show help and exit
    if runtime is None:
        # Categorize services
        infrastructure = []
        vllm_families = []
        ml_runtimes = []
        agent_platforms = []

        for name in service_map:
            if name == "monitoring":
                infrastructure.append(name)
            elif name.startswith("vllm-"):
                vllm_families.append(name.replace("vllm-", ""))
            elif name == "ollama":
                ml_runtimes.append(name)
            elif name == "openhands":
                agent_platforms.append(name)
            else:
                # Fallback for unknown services
                ml_runtimes.append(name)

        # Display categorized help
        console.print("[bold cyan]kanoa serve[/bold cyan] - MLOps Service Manager\n")

        if infrastructure:
            console.print("[bold]Infrastructure:[/bold]")
            console.print("  • monitoring      - Prometheus + Grafana")
            console.print("")

        if agent_platforms:
            console.print("[bold]Agent Platforms:[/bold]")
            console.print("  • openhands       - OpenHands (AI Software Engineer)")
            console.print("")

        if ml_runtimes or vllm_families:
            console.print("[bold]ML Runtimes:[/bold]")
            for name in ml_runtimes:
                desc = (
                    "Ollama server (manage models: ollama pull/list)"
                    if name == "ollama"
                    else "ML runtime"
                )
                console.print(f"  • {name:15} - {desc}")
            console.print("  • vllm          - vLLM inference server")
            console.print("")

        if vllm_families:
            console.print("[bold]vLLM Model Families:[/bold]")
            family_desc = {
                "olmo3": "Allen AI OLMo 3 (text)",
                "gemma3": "Google Gemma 3 (multimodal)",
                "molmo": "Allen AI Molmo (multimodal vision)",
            }
            for name in sorted(vllm_families):
                desc = family_desc.get(name, "Model family")
                console.print(f"  • {name:15} - {desc}")
            console.print("")

        console.print("[bold]Usage:[/bold]")
        console.print(
            "  kanoa mlops serve <runtime>                          # Start runtime"
        )
        console.print(
            "  kanoa mlops serve vllm <family> --model <id>         # Specific model"
        )
        console.print(
            "  kanoa mlops serve all                                # Start all services"
        )
        console.print("")
        console.print("[bold]Examples:[/bold]")
        console.print("  kanoa mlops serve monitoring")
        console.print("  kanoa mlops serve ollama")
        console.print("  kanoa mlops serve vllm gemma3 --model google/gemma-3-12b-it")
        return

    # Construct service name from runtime and model_family
    service = None
    if runtime in ["monitoring", "all"]:
        # These are standalone services
        service = runtime
    elif runtime == "ollama":
        # Ollama manages its own models
        service = "ollama"
        model_family = getattr(args, "model_family", None)

        # Handle model selection if family specified
        if model_family:
            if _is_tty():
                console.print(
                    f"[cyan]Selecting {model_family} model from Ollama...[/cyan]"
                )
                console.print("")
                selected_model = _select_ollama_model_interactive(family=model_family)
                if selected_model:
                    console.print(f"\n[green]Selected: {selected_model}[/green]")

                    # Check if Ollama is already running
                    is_container = _is_service_running("ollama")
                    is_native = not is_container and _check_url(
                        "http://localhost:11434"
                    )

                    if is_container:
                        console.print(
                            "\n[green]Ollama already running (Docker)[/green]"
                        )
                        console.print(
                            f"\nLoad the model with:\n  [bold]docker exec kanoa-ollama ollama run {selected_model}[/bold]\n"
                        )
                    elif is_native:
                        console.print(
                            "\n[green]Ollama already running (Native)[/green]"
                        )
                        console.print(
                            f"\nLoad the model with:\n  [bold]ollama run {selected_model}[/bold]\n"
                        )
                    else:
                        console.print("\n[cyan]Starting Ollama (Docker)...[/cyan]")
                        # ... fallback to normal docker start ...
                        console.print(
                            f"\nLoad the model with:\n  [bold]docker exec kanoa-ollama ollama run {selected_model}[/bold]\n"
                        )
                else:
                    console.print(
                        "[yellow]No model selected, starting Ollama server only.[/yellow]"
                    )
            else:
                console.print(
                    f"[yellow]Model family '{model_family}' specified but running non-interactively.[/yellow]"
                )
                console.print("\nList Ollama models with:")
                console.print("  [bold]docker exec kanoa-ollama ollama list[/bold]")
    elif runtime == "vllm":
        # vLLM requires a model family
        if not model_family:
            # Missing model family - handle based on TTY
            if _is_tty():
                model_family = _select_vllm_family_interactive(service_map)
                if model_family is None:
                    console.print("[yellow]Cancelled.[/yellow]")
                    sys.exit(0)
                console.print("")
            else:
                console.print("[red]Error: model family required for vLLM[/red]")
                console.print(
                    "\nUsage: kanoa mlops serve vllm <model-family> [--model <specific-model>]"
                )
                console.print("\nAvailable families:")
                for k in service_map:
                    if k.startswith("vllm-"):
                        console.print(f"  • {k.replace('vllm-', '')}")
                sys.exit(1)
        service = f"vllm-{model_family}"
    else:
        # Unknown runtime - might be legacy flat service name
        service = runtime

    # Prepare environment variables for docker-compose
    compose_env = {}

    # Set offline mode if requested
    if hasattr(args, "offline") and args.offline:
        compose_env["HF_HUB_OFFLINE"] = "1"
        console.print("[cyan]Running in offline mode (HF_HUB_OFFLINE=1)[/cyan]")

    # Handle model selection for vLLM services
    model_name = None
    if hasattr(args, "model") and args.model:
        model_name = args.model
    elif service and service.startswith("vllm-"):
        # No model specified for vLLM service
        if _is_tty():
            # Interactive mode - show selector with family filter
            console.print(
                "[cyan]No model specified, showing available models...[/cyan]"
            )
            console.print("")
            # Extract family from service name (e.g., vllm-gemma3 -> gemma3)
            family = (
                service.replace("vllm-", "") if service.startswith("vllm-") else None
            )
            model_name = _select_model_interactive(family=family)
            if not model_name:
                console.print("[yellow]No model selected, exiting.[/yellow]")
                sys.exit(0)
        else:
            # Non-interactive mode - show error
            family_name = service.replace("vllm-", "")
            console.print(f"[red]Error: --model required for vLLM {family_name}[/red]")
            console.print(
                f"\nUsage: kanoa mlops serve vllm {family_name} --model <model-id>"
            )
            console.print("\nTo see available cached models, run interactively:")
            console.print(f"  kanoa mlops serve vllm {family_name}")
            sys.exit(1)

    if model_name:
        compose_env["MODEL_NAME"] = model_name
        compose_env["SERVED_MODEL_NAME"] = model_name

        # Check if model is cached for vLLM services
        if (
            service
            and service.startswith("vllm-")
            and not _download_model_if_needed(model_name)
        ):
            sys.exit(1)

    if service is None:
        # Categorize services
        infrastructure = []
        vllm_families = []
        ml_runtimes = []
        agent_platforms = []

        for name in service_map:
            if name == "monitoring":
                infrastructure.append(name)
            elif name.startswith("vllm-"):
                vllm_families.append(name.replace("vllm-", ""))
            elif name == "ollama":
                ml_runtimes.append(name)
            elif name == "openhands":
                agent_platforms.append(name)
            else:
                # Fallback for unknown services
                ml_runtimes.append(name)

        # Display categorized help
        console.print("[bold cyan]kanoa serve[/bold cyan] - MLOps Service Manager\n")

        if infrastructure:
            console.print("[bold]Infrastructure:[/bold]")
            console.print("  • monitoring      - Prometheus + Grafana")
            console.print("")

        if agent_platforms:
            console.print("[bold]Agent Platforms:[/bold]")
            console.print("  • openhands       - OpenHands (AI Software Engineer)")
            console.print("")

        if ml_runtimes or vllm_families:
            console.print("[bold]ML Runtimes:[/bold]")
            for name in ml_runtimes:
                desc = (
                    "Ollama server (manage models: ollama pull/list)"
                    if name == "ollama"
                    else "ML runtime"
                )
                console.print(f"  • {name:15} - {desc}")
            console.print("  • vllm          - vLLM inference server")
            console.print("")

        if vllm_families:
            console.print("[bold]vLLM Model Families:[/bold]")
            family_desc = {
                "olmo3": "Allen AI OLMo 3 (text)",
                "gemma3": "Google Gemma 3 (multimodal)",
                "molmo": "Allen AI Molmo (multimodal vision)",
            }
            for name in sorted(vllm_families):
                desc = family_desc.get(name, "Model family")
                console.print(f"  • {name:15} - {desc}")
            console.print("")

        console.print("[bold]Usage:[/bold]")
        console.print(
            "  kanoa mlops serve <runtime>                          # Start runtime"
        )
        console.print(
            "  kanoa mlops serve vllm <family> --model <id>         # Specific model"
        )
        if _is_tty():
            console.print(
                "  kanoa mlops serve vllm <family>                      # Interactive selection"
            )
        console.print(
            "  kanoa mlops serve all                                # Start all services"
        )
        console.print("")
        console.print("[bold]Examples:[/bold]")
        console.print("  kanoa mlops serve monitoring")
        console.print("  kanoa mlops serve ollama")
        console.print("  kanoa mlops serve vllm gemma3 --model google/gemma-3-12b-it")
        if _is_tty():
            console.print(
                "  kanoa mlops serve vllm molmo  # Shows interactive model selector"
            )
        return

    if service == "all":
        for name, compose_file in service_map.items():
            if not compose_file.exists():
                console.print(
                    f"[yellow]Skipping {name}: compose file not found[/yellow]"
                )
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
                    console.print(
                        "[red]Error: No Docker Compose client available to build images.[/red]"
                    )
                    continue
                try:
                    subprocess.run(
                        [*COMPOSE_CMD, "-f", str(compose_file), "build"], check=True
                    )
                except subprocess.CalledProcessError:
                    console.print(
                        f"[red]Failed to build images for {name}, skipping start.[/red]"
                    )
                    continue

            run_docker_compose(compose_file, "up", env=compose_env)
    else:
        compose_file_opt = service_map.get(service)
        if compose_file_opt is None or not compose_file_opt.exists():
            console.print(f"[red]Error: Service '{service}' not found.[/red]")
            console.print("Available services:")
            for s in service_map:
                console.print(f"  - {s}")
            sys.exit(1)

        compose_file = compose_file_opt  # Now narrowed to Path

        # Check if service is already running
        if _is_service_running(service):
            console.print(f"[green]{service} already running[/green]")
        else:
            console.print(f"[blue]Starting {service}...[/blue]")

        # Auto-build missing images for this service before starting
        images = _parse_images_from_compose(compose_file)
        missing = [img for img in images if not _image_exists(img)]
        if missing:
            console.print(
                f"[yellow]Detected missing images: {', '.join(missing)}. Building first...[/yellow]"
            )
            if COMPOSE_CMD is None:
                console.print(
                    "[red]Error: No Docker Compose client available to build images.[/red]"
                )
                sys.exit(1)
            try:
                subprocess.run(
                    [*COMPOSE_CMD, "-f", str(compose_file), "build"], check=True
                )
            except subprocess.CalledProcessError:
                console.print(f"[red]Failed to build images for {service}[/red]")
                sys.exit(1)

        if not run_docker_compose(compose_file, "up", env=compose_env):
            console.print(f"[red]Failed to start {service}[/red]")
            sys.exit(1)

    # Print helpful info
    if service in ("ollama", "all"):
        console.print("[green]Ollama running at http://localhost:11434[/green]")
    if service in ("monitoring", "all"):
        console.print(
            "[green]Grafana running at http://localhost:3000 (admin/admin)[/green]"
        )


def _get_running_services(service_map: dict) -> list[str]:
    """Return a list of service names that are currently running."""
    running = set()
    result = _run_docker_command(["docker", "ps", "--format", "{{.Names}}"])

    if result and result.stdout:
        container_names = result.stdout.strip().split("\n")

        for cname in container_names:
            if not cname.startswith("kanoa-"):
                continue

            suffix = cname[6:]  # remove 'kanoa-'

            if suffix in service_map:
                running.add(suffix)
            elif suffix in ["prometheus", "grafana"]:
                running.add("monitoring")

    return sorted(running)


def _is_service_running(service: str) -> bool:
    """Check if a specific service is currently running."""
    result = _run_docker_command(
        [
            "docker",
            "ps",
            "--format",
            "{{.Names}}",
            "--filter",
            f"name=kanoa-{service}",
        ]
    )
    return bool(result and result.stdout.strip())


def handle_stop(args) -> None:
    """Handle the 'stop' command by stopping docker-compose services."""
    # Check docker availability early
    if not _ensure_docker_available(interactive=True):
        sys.exit(1)

    mlops_path = resolve_mlops_path()

    if not mlops_path:
        console.print("[yellow]No mlops path configured. Nothing to stop.[/yellow]")
        return

    service_map = get_initialized_services(mlops_path)

    # Parse arguments
    # args.service is now a list (nargs="*") or None/empty
    service_parts = getattr(args, "service", [])
    if not service_parts:
        service_parts = []

    service = None
    if service_parts:
        if len(service_parts) == 1:
            service = service_parts[0]
        elif len(service_parts) >= MIN_VLLM_PARTS and service_parts[0] == "vllm":
            # Handle 'vllm gemma3' -> 'vllm-gemma3'
            service = f"vllm-{service_parts[1]}"
        else:
            # Fallback: join with hyphens (e.g. 'vllm-gemma3')
            # This handles cases where user might type 'vllm-gemma3' as one arg
            # or potentially other multi-word services in future
            service = "-".join(service_parts)

    # Interactive selection if no service specified
    if service is None:
        running_services = _get_running_services(service_map)

        if not running_services:
            console.print("[yellow]No running kanoa services detected.[/yellow]")
            return

        # Show interactive menu for running services
        table = Table(title="Running Services")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Service", style="green")

        choices = []
        for idx, svc in enumerate(running_services, 1):
            table.add_row(str(idx), svc)
            choices.append((idx, svc))

        # Add 'all' option
        all_idx = len(choices) + 1
        table.add_row(str(all_idx), "all", style="bold red")
        choices.append((all_idx, "all"))

        console.print(table)
        choice = Prompt.ask(
            "Select service to stop",
            choices=[str(i) for i, _ in choices] + ["q"],
            default="q",
        )

        if choice == "q":
            return

        for idx, svc in choices:
            if idx == int(choice):
                service = svc
                break

    if service == "all":
        # Stop all running services
        running_services = _get_running_services(service_map)
        if not running_services:
            console.print("[yellow]No running services to stop.[/yellow]")
            return

        for name in running_services:
            compose_file = service_map.get(name)
            if compose_file and compose_file.exists():
                console.print(f"[blue]Stopping {name}...[/blue]")
                run_docker_compose(compose_file, "down")
    else:
        if service is None:
            return

        compose_file_opt = service_map.get(service)
        if compose_file_opt is not None and compose_file_opt.exists():
            console.print(f"[blue]Stopping {service}...[/blue]")
            run_docker_compose(compose_file_opt, "down")
        else:
            console.print(f"[red]Error: Service '{service}' not found.[/red]")
            # Try to be helpful if they typed 'vllm gemma3' but it didn't match
            if service.startswith("vllm-"):
                console.print(
                    f"Did you mean: kanoa mlops stop vllm {service.replace('vllm-', '')}?"
                )

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
            console.print(
                "Run [bold]kanoa mlops restart <service>[/bold] to restart one."
            )
            console.print(
                "Run [bold]kanoa mlops restart all[/bold] to restart everything."
            )
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
        "openhands": docker_dir / "openhands" / "docker-compose.yml",
    }

    # Check vLLM templates if present
    vllm_dir = docker_dir / "vllm"
    if vllm_dir.exists():
        for f in vllm_dir.glob("docker-compose.*.yml"):
            name = f.stem.replace("docker-compose.", "")  # e.g. 'molmo' or 'gemma'
            services[f"vllm-{name}"] = f

    services.update({name: path for name, path in candidates.items() if path.exists()})
    return services


HTTP_OK = 200


def _check_url(url: str) -> bool:
    """Check if a URL is reachable and returns 200 OK."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1) as response:
            return response.status == HTTP_OK  # type: ignore[no-any-return]
    except Exception:
        return False


def _check_docker_connection(timeout: int = 2) -> bool:
    """Check if Docker daemon is reachable."""
    result = _run_docker_command(
        ["docker", "info"],
        timeout=timeout,
    )
    return result is not None and result.returncode == 0


def _ensure_docker_available(interactive: bool = True) -> bool:
    """Check if Docker is available, offering to start OrbStack on macOS if needed."""
    if _check_docker_connection():
        return True

    # Docker is not reachable
    if interactive:
        console.print("[yellow]✘ Docker daemon is unreachable[/yellow]")

    # Specific macOS / OrbStack handling
    if sys.platform == "darwin" and shutil.which("orb"):
        is_orb_running = False
        try:
            subprocess.run(
                ["pgrep", "-x", "OrbStack"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            is_orb_running = True
        except subprocess.CalledProcessError:
            pass

        if not is_orb_running:
            if interactive:
                console.print("  [yellow]OrbStack is stopped.[/yellow]")
                if _is_tty():
                    if (
                        Prompt.ask(
                            "  Start OrbStack now?", choices=["y", "n"], default="y"
                        )
                        == "y"
                    ):
                        console.print("  [blue]Starting OrbStack...[/blue]")
                        subprocess.run(["open", "-a", "OrbStack"], check=False)
                        console.print(
                            "  [dim]Please wait a moment for Docker to initialize...[/dim]"
                        )
                        # Wait for it to come up
                        import time

                        for _ in range(15):
                            time.sleep(1)
                            if _check_docker_connection():
                                console.print(
                                    "  [green]Docker is now available![/green]"
                                )
                                return True
                        console.print("[red]Timed out waiting for Docker.[/red]")
        elif interactive:
            console.print(
                "  [dim]OrbStack is running but Docker socket is unresponsive.[/dim]"
            )

    return False


def handle_status(args) -> None:
    """Show current configuration and running services."""
    mlops_path = resolve_mlops_path()

    console.print("[bold]kanoa-mlops Status[/bold]")
    console.print("")

    if mlops_path:
        console.print(f"[green]✔ Configured path:[/green] {mlops_path}")
    else:
        console.print("[yellow]✘ Not initialized[/yellow]")
        console.print("  Run: kanoa mlops init --dir ./my-project")
        return

    # Check docker services
    console.print("")
    console.print("[bold]Running Containers:[/bold]")

    ollama_running = False
    vllm_running = False
    openhands_running = False
    has_running = False

    # Check connection first to avoid hanging
    if _ensure_docker_available(interactive=False):
        try:
            result = _run_docker_command(
                [
                    "docker",
                    "ps",
                    "--format",
                    "table {{.Names}}\t{{.Status}}\t{{.Ports}}",
                ]
            )

            if result and result.stdout:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # Header + at least one container
                    for line in lines[1:]:
                        if "kanoa" in line.lower():
                            console.print(f"  {line}")
                            has_running = True
                            if "ollama" in line.lower():
                                ollama_running = True
                            if "vllm" in line.lower():
                                vllm_running = True
                            if "openhands" in line.lower():
                                openhands_running = True

            if not has_running:
                console.print("  [dim]No kanoa services running[/dim]")

        except FileNotFoundError:
            console.print("  [yellow]Docker not available[/yellow]")
    else:
        console.print("  [yellow]✘ Docker daemon is not reachable[/yellow]")
        # Invoke specialized check just for display
        _ensure_docker_available(interactive=True)

    # Check Endpoints
    console.print("")
    console.print("[bold]Service Endpoints:[/bold]")

    # Check native services if no docker services found
    if not has_running:
        # Check native Ollama
        if _check_url("http://localhost:11434/"):
            console.print(
                "  [green]✔ Ollama API (Native)[/green]     http://localhost:11434/"
            )
            return

        console.print("  [dim]No active services to check[/dim]")
        return

    # Ollama
    ollama_url = "http://localhost:11434/"
    if ollama_running:
        if _check_url(ollama_url):
            console.print(f"  [green]✔ Ollama API (Docker)[/green]     {ollama_url}")
        else:
            console.print(
                f"  [dim]✘ Ollama API (Docker)[/dim]     {ollama_url} (Unreachable)"
            )
    elif _check_url(ollama_url):
        console.print(f"  [green]✔ Ollama API (Native)[/green]     {ollama_url}")

    # vLLM
    if vllm_running:
        vllm_url = "http://localhost:8000/health"
        if _check_url(vllm_url):
            console.print("  [green]✔ vLLM API[/green]       http://localhost:8000")
        else:
            console.print(
                "  [dim]✘ vLLM API[/dim]       http://localhost:8000 (Unreachable)"
            )

    # OpenHands
    if openhands_running:
        oh_url = "http://localhost:3000/"
        if _check_url(oh_url):
            console.print(f"  [green]✔ OpenHands[/green]        {oh_url}")
        else:
            console.print(f"  [dim]✘ OpenHands[/dim]        {oh_url} (Unreachable)")


def handle_list(args) -> None:
    """List available services and models."""
    mlops_path = resolve_mlops_path()
    if not mlops_path:
        console.print("[red]Error: kanoa-mlops not initialized.[/red]")
        return

    # Check if filtering by runtime
    filter_runtime = getattr(args, "runtime", None)

    # Show services if no filter or not filtering
    if filter_runtime is None:
        console.print("[bold]Available Services:[/bold]")
        services = get_initialized_services(mlops_path)
        if not services:
            console.print("  [dim]No services found in docker/ directory[/dim]")
        else:
            for name, path in services.items():
                console.print(
                    f"  • {name:<15} [dim]({path.relative_to(mlops_path)})[/dim]"
                )
        console.print("")

    # Show Ollama models if no filter or filtering for ollama
    if filter_runtime is None or filter_runtime == "ollama":
        console.print("[bold]Ollama Models:[/bold]")

        # First check local cache
        ollama_models = _list_ollama_models()
        if ollama_models:
            for model in ollama_models:
                if model["size_gb"] > 0:
                    console.print(
                        f"  • {model['name']:40} ({model['size_gb']:5.1f} GB)"
                    )
                else:
                    console.print(f"  • {model['name']}")
        else:
            console.print(
                "  [dim]No models found in Ollama cache (~/.ollama/models)[/dim]"
            )

        if filter_runtime is None:
            console.print("")

    # Show vLLM models if no filter or filtering for vllm
    if filter_runtime is None or filter_runtime == "vllm":
        console.print("[bold]vLLM Models:[/bold]")

        # Get all cached models and categorize by family
        cached_models = _list_cached_models()

        if not cached_models:
            console.print("  [dim]No models found in HuggingFace cache[/dim]")
        else:
            # Define family patterns for categorization
            family_patterns = {
                "gemma3": ["google/gemma-3", "google/gemma3"],
                "molmo": ["allenai/molmo", "allenai/Molmo"],
                "olmo3": ["allenai/olmo-3", "allenai/Olmo-3"],
            }

            # Categorize models by family
            family_models: dict[str, list[dict]] = {
                family: [] for family in family_patterns
            }
            other_models = []

            for model in cached_models:
                if not model["complete"]:
                    continue

                model_name = model["name"].lower()
                categorized = False

                for family, patterns in family_patterns.items():
                    if any(pattern.lower() in model_name for pattern in patterns):
                        family_models[family].append(model)
                        categorized = True
                        break

                if not categorized:
                    other_models.append(model)

            # Display models by family
            first_family = True
            for family in ["gemma3", "molmo", "olmo3"]:
                models = family_models[family]
                if models:
                    if first_family:
                        console.print(f"  [cyan]{family}:[/cyan]")
                        first_family = False
                    else:
                        console.print(f"\n  [cyan]{family}:[/cyan]")
                    for model in models:
                        console.print(
                            f"    • {model['name']:40} ({model['size_gb']:5.1f} GB)"
                        )

            if other_models:
                console.print("\n  [cyan]other:[/cyan]")
                for model in other_models:
                    console.print(
                        f"    • {model['name']:40} ({model['size_gb']:5.1f} GB)"
                    )

            if not any(family_models.values()) and not other_models:
                console.print("  [dim]No complete models found in cache[/dim]")


# =============================================================================
# CLI Registration
# =============================================================================


def _handle_mlops_help(args) -> None:
    """Show mlops-specific help when no subcommand is provided."""
    console.print("[bold cyan]kanoa mlops[/bold cyan] - MLOps Service Manager\n")
    console.print("[bold]Usage:[/bold] kanoa mlops <command> [options]\n")
    console.print("[bold]Available commands:[/bold]")
    console.print("  init       Initialize kanoa-mlops templates in a directory")
    console.print("  serve      Start local services (Ollama, vLLM, monitoring)")
    console.print("  stop       Stop running services")
    console.print("  restart    Restart services")
    console.print("  status     Show configuration and service status")
    console.print("  list       List available services and models")
    console.print("\n[bold]Examples:[/bold]")
    console.print("  kanoa mlops init --dir .")
    console.print("  kanoa mlops serve ollama")
    console.print("  kanoa mlops serve vllm molmo")
    console.print("  kanoa mlops status")
    console.print(
        "\nRun [bold]kanoa mlops <command> -h[/bold] for command-specific help."
    )


def register(subparsers) -> None:
    """Register CLI subcommands with the kanoa CLI.

    This function receives the subparsers object from the main kanoa CLI,
    and should add an 'ops' subcommand with its own subcommands underneath.
    """
    # Create the ops subcommand
    mlops_parser = subparsers.add_parser(
        "mlops", help="Manage local MLOps services (vLLM, Ollama, monitoring)"
    )

    # Add subcommands under 'kanoa ops'
    mlops_subparsers = mlops_parser.add_subparsers(
        dest="mlops_command", help="MLOps subcommands"
    )

    # Set default handler for mlops command when no subcommand is provided
    mlops_parser.set_defaults(func=_handle_mlops_help)

    # init command -> kanoa ops init
    init_parser = mlops_subparsers.add_parser(
        "init", help="Initialize kanoa-mlops in a directory"
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

    # serve command -> kanoa mlops serve
    serve_parser = mlops_subparsers.add_parser(
        "serve", help="Start local services (Ollama, Monitoring, vLLM)"
    )
    serve_parser.add_argument(
        "runtime",
        default=None,
        nargs="?",
        help="Runtime or service to start (vllm, ollama, monitoring, all)",
    )
    serve_parser.add_argument(
        "model_family",
        default=None,
        nargs="?",
        help="Model family for vLLM (gemma3, molmo, olmo3) or Ollama model",
    )
    serve_parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Specific model to serve (e.g., google/gemma-3-12b-it)",
    )
    serve_parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline mode (only use cached model files, no internet access)",
    )
    serve_parser.set_defaults(func=handle_serve)

    # stop command -> kanoa mlops stop
    stop_parser = mlops_subparsers.add_parser("stop", help="Stop local services")
    stop_parser.add_argument(
        "service",
        default=None,
        nargs="*",
        help="Service to stop (default: interactive selection of running services)",
    )
    stop_parser.set_defaults(func=handle_stop)

    # restart command -> kanoa mlops restart
    restart_parser = mlops_subparsers.add_parser(
        "restart", help="Restart local services"
    )
    restart_parser.add_argument(
        "service",
        default=None,
        nargs="?",
        help="Service to restart (default: list services)",
    )
    restart_parser.set_defaults(func=handle_restart)

    # status command -> kanoa mlops status
    status_parser = mlops_subparsers.add_parser(
        "status", help="Show configuration and running services"
    )
    status_parser.set_defaults(func=handle_status)

    # list command -> kanoa ops list
    list_parser = mlops_subparsers.add_parser(
        "list", help="List available services and models"
    )
    list_parser.add_argument(
        "runtime",
        default=None,
        nargs="?",
        choices=["ollama", "vllm"],
        help="Filter by runtime (ollama or vllm)",
    )
    list_parser.set_defaults(func=handle_list)
