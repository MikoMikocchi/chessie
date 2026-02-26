"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path


def _load_app_fonts() -> None:
    """Register bundled fonts for consistent cross-platform rendering."""
    from PyQt6.QtGui import QFontDatabase

    fonts_dir = Path(__file__).resolve().parents[2] / "assets" / "fonts"
    for font_name in (
        "AdwaitaSans-Regular.ttf",
        "AdwaitaMonoNerdFont-Regular.ttf",
    ):
        font_path = fonts_dir / font_name
        if font_path.is_file():
            QFontDatabase.addApplicationFont(str(font_path))


def main() -> None:
    """Launch the Chessie application."""
    from PyQt6.QtWidgets import QApplication

    from chessie.ui.main_window import MainWindow
    from chessie.ui.styles.theme import APP_STYLE

    app = QApplication(sys.argv)
    app.setApplicationName("Chessie")
    app.setStyle("Fusion")
    _load_app_fonts()
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
