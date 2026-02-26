"""Visual theme constants and QSS styles for Chessie."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QColor


@dataclass(frozen=True)
class BoardTheme:
    """Colour scheme for the chessboard."""

    light_square: QColor
    dark_square: QColor
    highlight_from: QColor  # selected piece origin
    highlight_to: QColor  # legal move targets
    highlight_check: QColor  # king in check
    last_move_from: QColor  # last move origin
    last_move_to: QColor  # last move destination
    coord_light: QColor  # coordinate text on dark squares
    coord_dark: QColor  # coordinate text on light squares

    @classmethod
    def default(cls) -> BoardTheme:
        return cls(
            light_square=QColor(240, 217, 181),  # tan
            dark_square=QColor(181, 136, 99),  # brown
            highlight_from=QColor(255, 255, 0, 100),  # yellow transparent
            highlight_to=QColor(0, 0, 0, 40),  # dark dot overlay
            highlight_check=QColor(255, 0, 0, 120),  # red transparent
            last_move_from=QColor(155, 199, 0, 105),  # green
            last_move_to=QColor(155, 199, 0, 105),
            coord_light=QColor(181, 136, 99),
            coord_dark=QColor(240, 217, 181),
        )

    @classmethod
    def blue(cls) -> BoardTheme:
        return cls(
            light_square=QColor(222, 227, 230),
            dark_square=QColor(140, 162, 173),
            highlight_from=QColor(255, 255, 0, 100),
            highlight_to=QColor(0, 0, 0, 40),
            highlight_check=QColor(255, 0, 0, 120),
            last_move_from=QColor(155, 199, 0, 105),
            last_move_to=QColor(155, 199, 0, 105),
            coord_light=QColor(140, 162, 173),
            coord_dark=QColor(222, 227, 230),
        )

    @classmethod
    def green(cls) -> BoardTheme:
        return cls(
            light_square=QColor(236, 238, 220),
            dark_square=QColor(112, 149, 120),
            highlight_from=QColor(255, 255, 0, 100),
            highlight_to=QColor(0, 0, 0, 40),
            highlight_check=QColor(255, 0, 0, 120),
            last_move_from=QColor(155, 199, 0, 105),
            last_move_to=QColor(155, 199, 0, 105),
            coord_light=QColor(112, 149, 120),
            coord_dark=QColor(236, 238, 220),
        )

    @classmethod
    def walnut(cls) -> BoardTheme:
        return cls(
            light_square=QColor(228, 210, 184),
            dark_square=QColor(118, 74, 47),
            highlight_from=QColor(255, 255, 0, 100),
            highlight_to=QColor(0, 0, 0, 40),
            highlight_check=QColor(255, 0, 0, 120),
            last_move_from=QColor(155, 199, 0, 105),
            last_move_to=QColor(155, 199, 0, 105),
            coord_light=QColor(118, 74, 47),
            coord_dark=QColor(228, 210, 184),
        )

    @classmethod
    def slate(cls) -> BoardTheme:
        return cls(
            light_square=QColor(224, 226, 231),
            dark_square=QColor(101, 110, 122),
            highlight_from=QColor(255, 255, 0, 100),
            highlight_to=QColor(0, 0, 0, 40),
            highlight_check=QColor(255, 0, 0, 120),
            last_move_from=QColor(155, 199, 0, 105),
            last_move_to=QColor(155, 199, 0, 105),
            coord_light=QColor(101, 110, 122),
            coord_dark=QColor(224, 226, 231),
        )


# ── Application-wide QSS ────────────────────────────────────────────────────

APP_STYLE = """
QMainWindow {
    background: #2b2b2b;
}

QLabel {
    color: #e0e0e0;
    font-family: "Adwaita Sans", "Helvetica Neue", sans-serif;
}

QListWidget {
    background: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    font-family: "Adwaita Sans", "Consolas", monospace;
    font-size: 13px;
}

QListWidget::item:selected {
    background: #264f78;
}

QPushButton {
    background: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 13px;
}
QPushButton:hover {
    background: #505050;
}
QPushButton:pressed {
    background: #264f78;
}
QPushButton:disabled {
    color: #666;
    background: #2b2b2b;
}

QMenuBar {
    background: #2b2b2b;
    color: #e0e0e0;
}
QMenuBar::item:selected {
    background: #3c3c3c;
}
QMenu {
    background: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #3c3c3c;
}
QMenu::item:selected {
    background: #264f78;
}
"""
