"""Qt application bootstrap helpers."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from chessie.runtime_assets import asset_path

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication

_LOGGER = logging.getLogger(__name__)
_FONT_FILES = (
    "AdwaitaSans-Regular.ttf",
    "AdwaitaMonoNerdFont-Regular.ttf",
)


def _load_app_fonts() -> None:
    """Register bundled fonts for consistent cross-platform rendering."""
    from PyQt6.QtGui import QFontDatabase

    for font_name in _FONT_FILES:
        font_path = asset_path("fonts", font_name)
        if not font_path.is_file():
            _LOGGER.warning("Bundled font not found: %s", font_path)
            continue
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id < 0:
            _LOGGER.warning("Failed to load bundled font: %s", font_path)


def _configure_application(app: QApplication) -> None:
    """Apply app-wide settings and theme."""
    from chessie.ui.styles.theme import APP_STYLE

    app.setApplicationName("Chessie")
    app.setStyle("Fusion")
    _load_app_fonts()
    app.setStyleSheet(APP_STYLE)


def run_application(argv: list[str] | None = None) -> int:
    """Create and run the main Qt application."""
    from PyQt6.QtWidgets import QApplication

    from chessie.ui.main_window import MainWindow

    app = QApplication(sys.argv if argv is None else argv)
    _configure_application(app)

    window = MainWindow()
    window.show()

    return app.exec()
