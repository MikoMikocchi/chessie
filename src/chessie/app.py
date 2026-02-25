"""Application entry point."""

from __future__ import annotations

import sys


def main() -> None:
    """Launch the Chessie application."""
    from PyQt6.QtWidgets import QApplication

    from chessie.ui.main_window import MainWindow
    from chessie.ui.styles.theme import APP_STYLE

    app = QApplication(sys.argv)
    app.setApplicationName("Chessie")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
