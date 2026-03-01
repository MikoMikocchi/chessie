"""Render FEN board positions as QPixmap for embedding in the manual."""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap

from chessie.core.piece import Piece
from chessie.ui.resources import piece_renderer

# Board colours (default warm theme)
_LIGHT = QColor(240, 217, 181)
_DARK = QColor(181, 136, 99)
_HIGHLIGHT = QColor(93, 163, 255, 135)
_HIGHLIGHT_BORDER = QColor(50, 108, 186, 220)
_COORD_LIGHT = QColor(181, 136, 99)
_COORD_DARK = QColor(240, 217, 181)


def _parse_placement(fen: str) -> dict[tuple[int, int], Piece]:
    """Parse FEN piece-placement part → ``{(row, col): Piece}``."""
    placement = fen.split()[0] if " " in fen else fen
    ranks = placement.split("/")
    if len(ranks) != 8:
        msg = f"Invalid FEN placement rank count: {placement!r}"
        raise ValueError(msg)

    pieces: dict[tuple[int, int], Piece] = {}
    for row_idx, rank_str in enumerate(ranks):
        col = 0
        for ch in rank_str:
            if ch.isdigit():
                col += int(ch)
            else:
                if not (0 <= col < 8):
                    msg = f"Invalid FEN placement file index in rank: {rank_str!r}"
                    raise ValueError(msg)
                pieces[(row_idx, col)] = Piece.from_char(ch)
                col += 1
        if col != 8:
            msg = f"Invalid FEN rank width ({col}) in rank: {rank_str!r}"
            raise ValueError(msg)
    return pieces


def _parse_square(name: str) -> tuple[int, int]:
    """Convert algebraic square name (e.g. ``'e4'``) to ``(row, col)``."""
    sq = name.strip().lower()
    if len(sq) != 2 or sq[0] not in "abcdefgh" or sq[1] not in "12345678":
        msg = f"Invalid square name: {name!r}"
        raise ValueError(msg)
    col = ord(sq[0]) - ord("a")
    row = 8 - int(sq[1])
    return row, col


@lru_cache(maxsize=128)
def render_fen_board(
    fen: str,
    board_size: int = 280,
    *,
    show_coords: bool = True,
    highlights: tuple[str, ...] = (),
) -> QPixmap:
    """Render a FEN position to a ``QPixmap``.

    Parameters
    ----------
    fen:
        FEN string (at least the piece-placement part).
    board_size:
        Target width / height in pixels (approximate – rounded to fit
        whole squares plus an optional coordinate margin).
    show_coords:
        Draw rank / file labels around the edge.
    highlights:
        Sequence of algebraic square names to overlay with a
        semi-transparent blue highlight.
    """
    margin = 18 if show_coords else 0
    sq = (board_size - margin) // 8
    total = sq * 8 + margin

    image = QImage(total, total, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    try:
        pieces = _parse_placement(fen)
    except ValueError:
        pieces = {}

    hl_set: set[tuple[int, int]] = set()
    for sq_name in highlights:
        try:
            hl_set.add(_parse_square(sq_name))
        except ValueError:
            continue

    # Squares
    for row in range(8):
        for col in range(8):
            x = margin + col * sq
            y = row * sq
            is_light = (row + col) % 2 == 0
            painter.fillRect(x, y, sq, sq, _LIGHT if is_light else _DARK)

            if (row, col) in hl_set:
                painter.fillRect(x, y, sq, sq, _HIGHLIGHT)
                pen = QPen(_HIGHLIGHT_BORDER)
                pen.setWidth(max(1, sq // 22))
                painter.setPen(pen)
                painter.drawRect(x + 1, y + 1, sq - 2, sq - 2)

            piece = pieces.get((row, col))
            if piece is not None:
                renderer = piece_renderer(piece)
                pad = int(sq * 0.05)
                target = QRectF(x + pad, y + pad, sq - 2 * pad, sq - 2 * pad)
                renderer.render(painter, target)

    # Coordinates
    if show_coords:
        font = QFont("Adwaita Sans", max(8, sq // 5))
        font.setBold(True)
        painter.setFont(font)
        for col in range(8):
            painter.setPen(_COORD_DARK if col % 2 == 0 else _COORD_LIGHT)
            painter.drawText(
                QRectF(margin + col * sq, 8 * sq, sq, margin),
                Qt.AlignmentFlag.AlignCenter,
                chr(ord("a") + col),
            )
        for row in range(8):
            painter.setPen(_COORD_LIGHT if row % 2 == 0 else _COORD_DARK)
            painter.drawText(
                QRectF(0, row * sq, margin, sq),
                Qt.AlignmentFlag.AlignCenter,
                str(8 - row),
            )

    painter.end()
    return QPixmap.fromImage(image)
