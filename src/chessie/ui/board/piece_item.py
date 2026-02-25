"""PieceItem — draggable chess piece on the QGraphicsScene."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QGraphicsPixmapItem

from chessie.core.piece import Piece
from chessie.core.types import Square
from chessie.ui.resources import piece_pixmap


class PieceItem(QGraphicsPixmapItem):
    """A single chess piece on the board.

    Stores its logical *square* and supports drag & drop.
    """

    def __init__(self, piece: Piece, square: Square, tile_size: int) -> None:
        super().__init__()
        self.piece = piece
        self.square = square
        self._tile_size = tile_size
        self._drag_origin: QPointF | None = None

        self.setPixmap(piece_pixmap(piece, tile_size))
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setZValue(1)

    def set_tile_size(self, size: int) -> None:
        """Update tile size and re-render."""
        self._tile_size = size
        self.setPixmap(piece_pixmap(self.piece, size))

    def enable_drag(self, enabled: bool) -> None:
        """Allow / disallow dragging."""
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, enabled)
        if enabled:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def start_drag(self) -> None:
        """Called at the beginning of a drag gesture."""
        self._drag_origin = self.pos()
        self.setZValue(10)  # bring to front
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        self.setOpacity(0.85)

    def cancel_drag(self) -> None:
        """Snap back to original position."""
        if self._drag_origin is not None:
            self.setPos(self._drag_origin)
        self._finish_drag()

    def finish_drag(self) -> None:
        """Cleanup after a successful drop."""
        self._finish_drag()

    def _finish_drag(self) -> None:
        self._drag_origin = None
        self.setZValue(1)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setOpacity(1.0)
