"""Configuration management for kanoa-mlops."""

from pathlib import Path
from typing import Any

import toml

CONFIG_DIR = Path.home() / ".config" / "kanoa"
CONFIG_FILE = CONFIG_DIR / "mlops.toml"

DEFAULT_CONFIG = {
    "mlops_path": "",  # Path to user's kanoa-mlops working directory
}


def load_config() -> dict[str, Any]:
    """Load user configuration from ~/.config/kanoa/mlops.toml."""
    if CONFIG_FILE.exists():
        return dict(toml.load(CONFIG_FILE))
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save user configuration to ~/.config/kanoa/mlops.toml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)


def get_mlops_path() -> Path | None:
    """
    Get the configured mlops working directory.

    Returns:
        Path to the mlops working directory, or None if not configured.
    """
    config = load_config()
    path_str = config.get("mlops_path", "")
    if path_str:
        path = Path(path_str)
        if path.exists():
            return path
    return None


def set_mlops_path(path: Path) -> None:
    """
    Set the mlops working directory in user config.

    Args:
        path: Absolute path to the mlops working directory.
    """
    config = load_config()
    config["mlops_path"] = str(path.resolve())
    save_config(config)


def get_templates_path() -> Path:
    """
    Get the path to the kanoa-mlops templates directory.

    Returns:
        Path to the templates directory within the kanoa_mlops package.
    """
    return Path(__file__).parent / "templates"
