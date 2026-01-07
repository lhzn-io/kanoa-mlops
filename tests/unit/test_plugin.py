from pathlib import Path
from unittest.mock import MagicMock, patch

from kanoa_mlops.plugin import (
    _detect_compose_client,
    _image_exists,
    _parse_images_from_compose,
    get_templates_path,
    resolve_mlops_path,
)


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

    # Mock Path.exists to return True for the expected path
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True

        result = resolve_mlops_path()
        assert result == expected_path.resolve()


@patch("kanoa_mlops.plugin.get_mlops_path")
def test_resolve_mlops_path_dev_mode(mock_get_config):
    """Test resolving path when in dev mode (repo root)."""
    mock_get_config.return_value = None

    # We need to mock Path.exists to simulate dev environment
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True

        result = resolve_mlops_path()

        assert result is not None
        # In dev mode, it returns the repo root
        assert (result / "docker" / "ollama").exists()


@patch("kanoa_mlops.plugin.get_mlops_path")
def test_resolve_mlops_path_none(mock_get_config):
    """Test resolving path when nothing is found."""
    mock_get_config.return_value = None

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = resolve_mlops_path()
        assert result is None


# --- New Tests ---


@patch("subprocess.run")
def test_detect_compose_client_plugin(mock_run):
    """Test detection of 'docker compose' plugin."""
    # Simulate success for 'docker compose version'
    mock_run.return_value.returncode = 0

    client = _detect_compose_client()
    assert client == ["docker", "compose"]
    mock_run.assert_called_with(
        ["docker", "compose", "version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )


@patch("subprocess.run")
def test_detect_compose_client_standalone(mock_run):
    """Test detection of 'docker-compose' standalone."""
    # Simulate failure for 'docker compose version'
    # Simulate success for 'docker-compose --version'

    def side_effect(cmd, **kwargs):
        res = MagicMock()
        if cmd == ["docker", "compose", "version"]:
            res.returncode = 1
        elif cmd == ["docker-compose", "--version"]:
            res.returncode = 0
        else:
            res.returncode = 1
        return res

    mock_run.side_effect = side_effect

    client = _detect_compose_client()
    assert client == ["docker-compose"]


@patch("subprocess.run")
def test_detect_compose_client_none(mock_run):
    """Test when no compose client is found."""
    mock_run.return_value.returncode = 1

    client = _detect_compose_client()
    assert client is None


def test_parse_images_from_compose(tmp_path):
    """Test parsing images from a compose file."""
    compose_content = """
version: '3.8'
services:
  app:
    image: my-app:latest
    build: .
  db:
    image:  postgres:15-alpine
  redis:
    # image: commented-out
    image: redis:7
"""
    f = tmp_path / "docker-compose.yml"
    f.write_text(compose_content)

    images = _parse_images_from_compose(f)
    assert "my-app:latest" in images
    assert "postgres:15-alpine" in images
    assert "redis:7" in images
    assert len(images) == 3


@patch("subprocess.run")
def test_image_exists_true(mock_run):
    """Test _image_exists when image is present."""
    mock_run.return_value.stdout = "sha256:12345..."

    assert _image_exists("my-image:latest") is True
    mock_run.assert_called_with(
        ["docker", "images", "-q", "my-image:latest"],
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
    )


@patch("subprocess.run")
def test_image_exists_false(mock_run):
    """Test _image_exists when image is missing."""
    mock_run.return_value.stdout = ""

    assert _image_exists("missing:latest") is False
