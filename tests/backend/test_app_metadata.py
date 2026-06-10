"""Tests that project metadata is real and the API version tracks the package version (#25)."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pytest


def test_api_version_matches_package_version():
    try:
        package_version = version("ai-hedge-fund")
    except PackageNotFoundError:
        pytest.skip("package not installed; version fallback applies")

    from app.backend.main import app

    assert app.version == package_version


def test_pyproject_has_no_placeholder_author():
    pyproject = (Path(__file__).parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    assert "Your Name" not in pyproject
    assert "your.email@example.com" not in pyproject
