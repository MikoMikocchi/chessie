"""Preview widgets used by settings pages."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget

from chessie.core.enums import Color, PieceType
from chessie.core.piece import Piece
from chessie.ui.resources import piece_pixmap
from chessie.ui.styles.theme import BoardTheme


class _BoardThemePreviewWidget(QWidget):
    """Compact board appearance preview for theme selection."""

    _THEME_MAP: dict[str, BoardTheme] = {
        "Classic": BoardTheme.default(),
        "Blue": BoardTheme.blue(),
        "Green": BoardTheme.green(),
        "Walnut": BoardTheme.walnut(),
        "Slate": BoardTheme.slate(),
    }

    def __init__(self, theme_name: str) -> None:
        super().__init__()
        self._theme_name = theme_name
        self.setFixedSize(136, 72)

    def set_theme_name(self, theme_name: str) -> None:
        if self._theme_name == theme_name:
            return
        self._theme_name = theme_name
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        del event
        square = 64
        board_x = 2
        board_y = 2
        piece_size = 56

        theme = self._THEME_MAP.get(self._theme_name, BoardTheme.default())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        frame_w = (square * 2) + 4
        frame_h = square + 4
        painter.fillRect(0, 0, frame_w, frame_h, Qt.GlobalColor.black)

        painter.fillRect(board_x, board_y, square, square, theme.light_square)
        painter.fillRect(board_x + square, board_y, square, square, theme.dark_square)

        white_piece = Piece(Color.WHITE, PieceType.KING)
        black_piece = Piece(Color.BLACK, PieceType.QUEEN)

        white_pixmap = piece_pixmap(white_piece, piece_size)
        black_pixmap = piece_pixmap(black_piece, piece_size)

        white_x = board_x + (square - piece_size) // 2
        black_x = board_x + square + (square - piece_size) // 2
        piece_y = board_y + (square - piece_size) // 2

        painter.drawPixmap(white_x, piece_y, white_pixmap)
        painter.drawPixmap(black_x, piece_y, black_pixmap)
        painter.end()


class _MoveNotationPreviewWidget(QWidget):
    """Compact preview for move notation format selection."""

    def __init__(self) -> None:
        super().__init__()
        self._use_figurine_notation = True
        self.setFixedSize(136, 72)

    def set_use_figurine_notation(self, enabled: bool) -> None:
        if self._use_figurine_notation == enabled:
            return
        self._use_figurine_notation = enabled
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        panel_w = 132
        panel_h = 68
        painter.fillRect(2, 2, panel_w, panel_h, QColor("#1e1e1e"))

        number_font = QFont("Adwaita Sans", 10)
        move_font = QFont("AdwaitaMono Nerd Font", 10)

        white = "♘f3" if self._use_figurine_notation else "Nf3"
        black = "♞c6" if self._use_figurine_notation else "Nc6"

        painter.setFont(number_font)
        painter.setPen(QColor("#9f9f9f"))
        painter.drawText(10, 28, "1")
        painter.drawText(10, 50, "2")

        painter.setFont(move_font)
        painter.setPen(QColor("#d4d4d4"))
        painter.drawText(30, 28, "e4")
        painter.drawText(78, 28, "e5")
        painter.drawText(30, 50, white)
        painter.drawText(78, 50, black)
        painter.end()
