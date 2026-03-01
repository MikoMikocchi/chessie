"""Animation helpers for :class:`BoardScene`."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QPointF

from chessie.core.enums import MoveFlag
from chessie.core.move import Move
from chessie.core.types import file_of, make_square, rank_of

if TYPE_CHECKING:
    from PyQt6.QtCore import QPropertyAnimation

    from chessie.core.position import Position
    from chessie.ui.board.board_scene import BoardScene


def animate_and_sync(
    scene: BoardScene,
    move: Move,
    new_position: Position,
    *,
    animation_cls: type[QPropertyAnimation],
    on_done: Callable[[], None] | None = None,
) -> None:
    """Slide the moving piece to its destination, then full-sync."""
    if scene._active_anim is not None:
        scene._active_anim.stop()
        scene._active_anim = None
        scene._position = new_position
        scene._sync_pieces()
        if on_done:
            on_done()
        return

    item = scene._piece_items.get(move.from_sq)
    if not scene._animate_moves or item is None:
        scene._position = new_position
        scene._sync_pieces()
        if on_done:
            on_done()
        return

    t = scene.TILE

    if move.flag == MoveFlag.EN_PASSANT:
        ep_sq = make_square(file_of(move.to_sq), rank_of(move.from_sq))
        captured = scene._piece_items.pop(ep_sq, None)
        if captured is not None:
            scene.removeItem(captured)
    else:
        captured = scene._piece_items.pop(move.to_sq, None)
        if captured is not None:
            scene.removeItem(captured)

    if move.flag in (MoveFlag.CASTLE_KINGSIDE, MoveFlag.CASTLE_QUEENSIDE):
        rank = rank_of(move.from_sq)
        if move.flag == MoveFlag.CASTLE_KINGSIDE:
            rook_from, rook_to = make_square(7, rank), make_square(5, rank)
        else:
            rook_from, rook_to = make_square(0, rank), make_square(3, rank)
        rook_item = scene._piece_items.pop(rook_from, None)
        if rook_item is not None:
            rvf, rvr = scene._visual_coords(file_of(rook_to), rank_of(rook_to))
            rook_item.setPos(rvf * t + rook_item.margin, rvr * t + rook_item.margin)
            scene._piece_items[rook_to] = rook_item

    vf, vr = scene._visual_coords(file_of(move.to_sq), rank_of(move.to_sq))
    target = QPointF(vf * t + item.margin, vr * t + item.margin)

    del scene._piece_items[move.from_sq]
    scene._piece_items[move.to_sq] = item
    item.square = move.to_sq
    item.setZValue(2)

    anim = animation_cls(item, b"pos", scene)
    anim.setDuration(scene._ANIM_DURATION_MS)
    anim.setStartValue(item.pos())
    anim.setEndValue(target)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _on_finished() -> None:
        scene._active_anim = None
        item.setZValue(1)
        scene._position = new_position
        scene._sync_pieces()
        if on_done:
            on_done()

    anim.finished.connect(_on_finished)
    scene._active_anim = anim
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
