"""Interaction helpers for :class:`BoardScene`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.types import Square

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QGraphicsSceneMouseEvent

    from chessie.ui.board.board_scene import BoardScene
    from chessie.ui.dialogs.promotion_dialog import PromotionDialog


def handle_mouse_press(scene: BoardScene, event: QGraphicsSceneMouseEvent) -> bool:
    """Handle press; return True when event is fully handled."""
    position = scene._position
    if position is None:
        return False

    sq = scene._pos_to_square(event.scenePos())
    if sq is None:
        scene._clear_selection()
        return False

    piece = position.board[sq]

    if scene._selected_sq is not None:
        move = scene._find_legal_move(scene._selected_sq, sq)
        if move is not None:
            scene._clear_selection()
            scene.move_made.emit(move)
            return True

    if piece is not None and piece.color == position.side_to_move:
        scene._select_square(sq)
        if sq in scene._piece_items:
            item = scene._piece_items[sq]
            item.enable_drag(True)
            item.start_drag()
            scene._dragging_item = item
    else:
        scene._clear_selection()
    return False


def handle_mouse_release(scene: BoardScene, event: QGraphicsSceneMouseEvent) -> bool:
    """Handle release; return True when event is fully handled."""
    if scene._dragging_item is None:
        return False

    item = scene._dragging_item
    drop_sq = scene._pos_to_square(event.scenePos())

    if drop_sq is not None and drop_sq != item.square:
        move = scene._find_legal_move(item.square, drop_sq)
        if move is not None:
            item.finish_drag()
            item.enable_drag(False)
            scene._dragging_item = None
            scene._clear_selection()
            scene.move_made.emit(move)
            return True

    item.cancel_drag()
    item.enable_drag(False)
    scene._dragging_item = None
    return False


def select_square(scene: BoardScene, sq: Square) -> None:
    scene._clear_selection()
    scene._selected_sq = sq

    rect = scene._make_highlight(sq, scene._theme.highlight_from)
    scene._highlight_items.append(rect)

    if scene._position is not None:
        gen = MoveGenerator(scene._position)
        scene._legal_moves = gen.generate_legal_moves()
        if scene._show_legal_moves:
            for move in scene._legal_moves:
                if move.from_sq == sq:
                    dot = scene._make_highlight(move.to_sq, scene._theme.highlight_to)
                    scene._legal_dot_items.append(dot)


def clear_selection(scene: BoardScene) -> None:
    scene._selected_sq = None
    scene._legal_moves = []
    scene._clear_items(scene._highlight_items)
    scene._clear_items(scene._legal_dot_items)


def find_legal_move(
    scene: BoardScene,
    from_sq: Square,
    to_sq: Square,
    *,
    promotion_dialog_cls: type[PromotionDialog],
) -> Move | None:
    """Find one legal move from *from_sq* to *to_sq*."""
    if not scene._legal_moves:
        if scene._position is None:
            return None
        gen = MoveGenerator(scene._position)
        scene._legal_moves = gen.generate_legal_moves()

    candidates = [
        move
        for move in scene._legal_moves
        if move.from_sq == from_sq and move.to_sq == to_sq
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    if scene._position is None:
        return None
    piece = scene._position.board[from_sq]
    if piece is None:
        return None

    parent = scene.views()[0] if scene.views() else None
    promotion = promotion_dialog_cls.ask(piece.color, parent)
    if promotion is None:
        return None

    for move in candidates:
        if move.promotion == promotion:
            return move
    return candidates[0]
