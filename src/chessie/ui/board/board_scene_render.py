"""Rendering helpers for :class:`BoardScene`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPen
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem

from chessie.core.types import Square, file_of, make_square, rank_of
from chessie.ui.board.piece_item import PieceItem

if TYPE_CHECKING:
    from chessie.ui.board.board_scene import BoardScene


def visual_coords(scene: BoardScene, file: int, rank: int) -> tuple[int, int]:
    """Convert board file/rank to visual column/row."""
    if scene._flipped:
        return 7 - file, rank
    return file, 7 - rank


def pos_to_square(scene: BoardScene, pos: QPointF) -> Square | None:
    """Scene position -> board square."""
    t = scene.TILE
    col = int(pos.x() // t)
    row = int(pos.y() // t)
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    if scene._flipped:
        file_idx, rank_idx = 7 - col, row
    else:
        file_idx, rank_idx = col, 7 - row
    return make_square(file_idx, rank_idx)


def make_highlight(scene: BoardScene, sq: Square, color: QColor) -> QGraphicsRectItem:
    """Create a coloured overlay rectangle on a square."""
    t = scene.TILE
    file_idx, rank_idx = file_of(sq), rank_of(sq)
    vf, vr = visual_coords(scene, file_idx, rank_idx)
    rect = QGraphicsRectItem(vf * t, vr * t, t, t)
    rect.setBrush(QBrush(color))
    rect.setPen(QPen(Qt.PenStyle.NoPen))
    rect.setZValue(0.8)
    scene.addItem(rect)
    return rect


def clear_items(scene: BoardScene, items: list[QGraphicsRectItem]) -> None:
    for item in items:
        scene.removeItem(item)
    items.clear()


def draw_board(scene: BoardScene) -> None:
    """Draw or redraw the 64 squares and coordinates."""
    for sq_item in scene._square_items.values():
        scene.removeItem(sq_item)
    scene._square_items.clear()
    for coord_item in scene._coord_items:
        scene.removeItem(coord_item)
    scene._coord_items.clear()

    t = scene.TILE
    font = QFont("Adwaita Sans", max(9, t // 8))

    for sq in range(64):
        file_idx, rank_idx = file_of(sq), rank_of(sq)
        vf, vr = visual_coords(scene, file_idx, rank_idx)
        is_light = (file_idx + rank_idx) % 2 == 0
        color = scene._theme.dark_square if is_light else scene._theme.light_square
        rect = QGraphicsRectItem(vf * t, vr * t, t, t)
        rect.setBrush(QBrush(color))
        rect.setPen(QPen(Qt.PenStyle.NoPen))
        rect.setZValue(0)
        scene.addItem(rect)
        scene._square_items[sq] = rect

        if file_idx == 0:
            label = str(rank_idx + 1)
            txt = QGraphicsSimpleTextItem(label)
            txt.setFont(font)
            txt.setBrush(
                QBrush(
                    scene._theme.coord_dark if is_light else scene._theme.coord_light
                )
            )
            txt.setPos(vf * t + 2, vr * t + 1)
            txt.setZValue(0.3)
            txt.setVisible(scene._show_coordinates)
            scene.addItem(txt)
            scene._coord_items.append(txt)

        if rank_idx == 0:
            letter = chr(ord("a") + file_idx)
            txt = QGraphicsSimpleTextItem(letter)
            txt.setFont(font)
            txt.setBrush(
                QBrush(
                    scene._theme.coord_dark if is_light else scene._theme.coord_light
                )
            )
            txt.setPos(vf * t + t - 12, vr * t + t - 16)
            txt.setZValue(0.3)
            txt.setVisible(scene._show_coordinates)
            scene.addItem(txt)
            scene._coord_items.append(txt)

    scene.setSceneRect(0, 0, 8 * t, 8 * t)


def sync_pieces(scene: BoardScene) -> None:
    """Re-create all piece items from the current position."""
    for item in scene._piece_items.values():
        scene.removeItem(item)
    scene._piece_items.clear()

    if scene._position is None:
        return

    t = scene.TILE
    for sq in range(64):
        piece = scene._position.board[sq]
        if piece is not None:
            item = PieceItem(piece, sq, t)
            file_idx, rank_idx = file_of(sq), rank_of(sq)
            vf, vr = visual_coords(scene, file_idx, rank_idx)
            item.setPos(vf * t + item.margin, vr * t + item.margin)
            scene.addItem(item)
            scene._piece_items[sq] = item
