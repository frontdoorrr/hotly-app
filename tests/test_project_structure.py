"""Test project structure and basic setup."""
from pathlib import Path


def test_project_structure_exists() -> None:
    """Test that all required directories exist."""
    base_path = Path(__file__).parent.parent
    required_dirs = [
        "app",
        "app/api",
        "app/api/api_v1",
        "app/api/api_v1/endpoints",
        "app/core",
        "app/crud",
        "app/db",
        "app/models",
        "app/schemas",
        "app/services",
        "app/features",
        "app/exceptions",
        "tests",
    ]

    for dir_path in required_dirs:
        assert (base_path / dir_path).exists(), f"Directory {dir_path} should exist"


def test_init_files_exist() -> None:
    """Test that __init__.py files exist in Python packages."""
    base_path = Path(__file__).parent.parent
    required_init_files = [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/api_v1/__init__.py",
        "app/api/api_v1/endpoints/__init__.py",
        "app/core/__init__.py",
        "app/crud/__init__.py",
        "app/db/__init__.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/features/__init__.py",
        "app/exceptions/__init__.py",
    ]

    for init_file in required_init_files:
        assert (base_path / init_file).exists(), f"Init file {init_file} should exist"


def test_main_app_file_exists() -> None:
    """Test that main application file exists."""
    base_path = Path(__file__).parent.parent
    assert (base_path / "app/main.py").exists(), "app/main.py should exist"


def test_pyproject_toml_exists() -> None:
    """Test that Poetry configuration exists."""
    base_path = Path(__file__).parent.parent
    assert (base_path / "pyproject.toml").exists(), "pyproject.toml should exist"


def test_env_example_exists() -> None:
    """Test that environment template exists."""
    base_path = Path(__file__).parent.parent
    assert (base_path / ".env.example").exists(), ".env.example should exist"
