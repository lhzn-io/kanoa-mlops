from pathlib import Path
from unittest.mock import patch

from kanoa_mlops.plugin import get_templates_path, resolve_mlops_path


def test_get_templates_path():
    """Test that get_templates_path returns a valid path object."""
    path = get_templates_path()
    assert isinstance(path, Path)
    assert path.name == "templates"


@patch("kanoa_mlops.plugin.get_mlops_path")
def test_resolve_mlops_path_from_config(mock_get_config):
    """Test resolving path when config is set."""
    expected_path = Path("/tmp/kanoa-mlops")
    mock_get_config.return_value = expected_path

    result = resolve_mlops_path()
    assert result == expected_path


@patch("kanoa_mlops.plugin.get_mlops_path")
def test_resolve_mlops_path_dev_mode(mock_get_config):
    """Test resolving path when in dev mode (repo root)."""
    mock_get_config.return_value = None

    # We need to mock Path.exists to simulate dev environment
    # Since resolve_mlops_path uses Path(__file__)... we need to be careful.
    # It checks (repo_root / "docker" / "ollama").exists()

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True

        result = resolve_mlops_path()

        # The result should be the parent.parent of the plugin file
        # We can't easily assert the exact path without knowing where the test runs,
        # but we can check it's not None
        assert result is not None
        assert (result / "docker" / "ollama").exists()


@patch("kanoa_mlops.plugin.get_mlops_path")
def test_resolve_mlops_path_none(mock_get_config):
    """Test resolving path when nothing is found."""
    mock_get_config.return_value = None

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = resolve_mlops_path()
        assert result is None
