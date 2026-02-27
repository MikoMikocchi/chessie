"""Piece rendering helpers for chess SVG assets."""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtSvg import QSvgRenderer

from chessie.core.enums import Color, PieceType
from chessie.core.piece import Piece
from chessie.runtime_assets import asset_path

_ASSETS_DIR = asset_path("pieces")

_PIECE_NAMES: dict[PieceType, str] = {
    PieceType.PAWN: "pawn",
    PieceType.KNIGHT: "knight",
    PieceType.BISHOP: "bishop",
    PieceType.ROOK: "rook",
    PieceType.QUEEN: "queen",
    PieceType.KING: "king",
}

_COLOR_SUFFIX: dict[Color, str] = {
    Color.WHITE: "w",
    Color.BLACK: "b",
}

# Cache SVG renderers (one per piece/color)
_renderers: dict[tuple[Color, PieceType], QSvgRenderer] = {}


def _get_renderer(color: Color, piece_type: PieceType) -> QSvgRenderer:
    """Load and cache the QSvgRenderer for a piece."""
    key = (color, piece_type)
    if key not in _renderers:
        name = _PIECE_NAMES[piece_type]
        suffix = _COLOR_SUFFIX[color]
        path = _ASSETS_DIR / f"{name}-{suffix}.svg"
        renderer = QSvgRenderer(str(path))
        if not renderer.isValid():
            raise FileNotFoundError(f"SVG asset not found or invalid: {path}")
        _renderers[key] = renderer
    return _renderers[key]


def piece_renderer(piece: Piece) -> QSvgRenderer:
    """Return a cached SVG renderer for *piece*."""
    return _get_renderer(piece.color, piece.piece_type)


@lru_cache(maxsize=128)
def piece_pixmap(piece: Piece, size: int) -> QPixmap:
    """Render a chess piece SVG as a *size* × *size* QPixmap."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter

    renderer = piece_renderer(piece)

    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # Slight padding so pieces don't touch square edges
    margin = int(size * 0.03)
    target = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    renderer.render(painter, target)

    painter.end()
    return QPixmap.fromImage(image)
