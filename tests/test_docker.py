"""Test Docker configuration files."""
from pathlib import Path


def test_dockerfile_exists() -> None:
    """Test that Dockerfile exists."""
    base_path = Path(__file__).parent.parent
    assert (base_path / "Dockerfile").exists(), "Dockerfile should exist"


def test_docker_compose_exists() -> None:
    """Test that docker-compose.yml exists."""
    base_path = Path(__file__).parent.parent
    assert (base_path / "docker-compose.yml").exists(), "docker-compose.yml should exist"


def test_docker_compose_dev_exists() -> None:
    """Test that docker-compose.dev.yml exists."""
    base_path = Path(__file__).parent.parent
    assert (base_path / "docker-compose.dev.yml").exists(), "docker-compose.dev.yml should exist"