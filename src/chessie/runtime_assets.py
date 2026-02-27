"""Helpers for locating runtime asset files."""

from __future__ import annotations

from pathlib import Path

_PACKAGE_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_REPO_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def assets_dir() -> Path:
    """Return the root directory for runtime assets."""
    if _PACKAGE_ASSETS_DIR.is_dir():
        return _PACKAGE_ASSETS_DIR
    return _REPO_ASSETS_DIR


def asset_path(*parts: str) -> Path:
    """Build an absolute path inside the runtime assets directory."""
    return assets_dir().joinpath(*parts)
