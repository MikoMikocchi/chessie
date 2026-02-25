"""PieceItem — draggable chess piece on the QGraphicsScene."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import QGraphicsItem

from chessie.core.piece import Piece
from chessie.core.types import Square
from chessie.ui.resources import piece_renderer


class PieceItem(QGraphicsSvgItem):
    """A single chess piece on the board.

    Stores its logical *square* and supports drag & drop.
    """

    _MARGIN_RATIO = 0.03

    def __init__(self, piece: Piece, square: Square, tile_size: int) -> None:
        super().__init__()
        self.piece = piece
        self.square = square
        self._tile_size = tile_size
        self._margin = 0.0
        self._drag_origin: QPointF | None = None

        self.setSharedRenderer(piece_renderer(piece))
        self.setTransformOriginPoint(0.0, 0.0)
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)
        self._update_size(tile_size)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setZValue(1)

    def set_tile_size(self, size: int) -> None:
        """Update tile size and re-render."""
        self._update_size(size)

    @property
    def margin(self) -> float:
        """Inner margin to keep the piece away from tile edges."""
        return self._margin

    def enable_drag(self, enabled: bool) -> None:
        """Allow / disallow dragging."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
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

    def _update_size(self, size: int) -> None:
        self._tile_size = size
        self._margin = float(size) * self._MARGIN_RATIO
        draw_size = max(float(size) - 2.0 * self._margin, 1.0)

        renderer = self.renderer()
        if renderer is None:
            return
        bounds = self.boundingRect()
        width = float(bounds.width()) or float(renderer.defaultSize().width()) or 1.0
        height = float(bounds.height()) or float(renderer.defaultSize().height()) or 1.0
        scale = min(draw_size / width, draw_size / height)
        self.setScale(scale)
