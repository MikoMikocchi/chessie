"""Shared pytest fixtures used across the test suite."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

# Linux CI runners are often headless. Force an offscreen backend only there.
if (
    sys.platform.startswith("linux")
    and "QT_QPA_PLATFORM" not in os.environ
    and "DISPLAY" not in os.environ
    and "WAYLAND_DISPLAY" not in os.environ
):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def _is_ui_test(request: pytest.FixtureRequest) -> bool:
    return "ui" in Path(str(request.node.fspath)).parts


@pytest.fixture(scope="session")
def qapp() -> Iterator[object]:
    """Provide a singleton QApplication for UI tests."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _reset_language() -> Iterator[None]:
    """Reset shared i18n state between tests."""
    from chessie.ui.i18n import set_language

    set_language("English")
    yield
    set_language("English")


@pytest.fixture(autouse=True)
def _cleanup_qt_widgets(
    request: pytest.FixtureRequest,
) -> Iterator[None]:
    """Ensure UI tests do not leak top-level widgets into the next test."""
    if not _is_ui_test(request):
        yield
        return

    app = request.getfixturevalue("qapp")
    yield

    for widget in list(app.topLevelWidgets()):
        widget.close()
    app.processEvents()
