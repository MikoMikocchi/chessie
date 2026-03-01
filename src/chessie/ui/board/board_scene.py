"""BoardScene - QGraphicsScene that draws the chessboard and pieces."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QPointF, QPropertyAnimation, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsSimpleTextItem,
)

from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.types import Square
from chessie.ui.board.board_scene_animation import animate_and_sync as _animate_and_sync
from chessie.ui.board.board_scene_interaction import (
    clear_selection as _clear_selection,
)
from chessie.ui.board.board_scene_interaction import (
    find_legal_move as _find_legal_move,
)
from chessie.ui.board.board_scene_interaction import (
    handle_mouse_press as _handle_mouse_press,
)
from chessie.ui.board.board_scene_interaction import (
    handle_mouse_release as _handle_mouse_release,
)
from chessie.ui.board.board_scene_interaction import (
    select_square as _select_square,
)
from chessie.ui.board.board_scene_render import (
    clear_items as _clear_items,
)
from chessie.ui.board.board_scene_render import (
    draw_board as _draw_board,
)
from chessie.ui.board.board_scene_render import (
    make_highlight as _make_highlight,
)
from chessie.ui.board.board_scene_render import (
    pos_to_square as _pos_to_square,
)
from chessie.ui.board.board_scene_render import (
    sync_pieces as _sync_pieces,
)
from chessie.ui.board.board_scene_render import (
    visual_coords as _visual_coords,
)
from chessie.ui.board.piece_item import PieceItem
from chessie.ui.dialogs.promotion_dialog import PromotionDialog
from chessie.ui.styles.theme import BoardTheme

if TYPE_CHECKING:
    from chessie.core.position import Position


class BoardScene(QGraphicsScene):
    """Renders the board, coordinates, highlights, and piece items.

    Signals:
        move_made(Move): Emitted when a user completes a legal move via drag/click.
    """

    move_made = pyqtSignal(Move)

    TILE = 80  # px per square
    _ANIM_DURATION_MS = 150

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._theme = BoardTheme.default()
        self._position: Position | None = None
        self._flipped = False

        # Interaction state
        self._selected_sq: Square | None = None
        self._legal_moves: list[Move] = []
        self._dragging_item: PieceItem | None = None
        self._interactive = True
        self._show_coordinates = True
        self._show_legal_moves = True
        self._animate_moves = True
        self._active_anim: QPropertyAnimation | None = None

        # Visual layers
        self._square_items: dict[Square, QGraphicsRectItem] = {}
        self._highlight_items: list[QGraphicsRectItem] = []
        self._last_move_highlights: list[QGraphicsRectItem] = []
        self._legal_dot_items: list[QGraphicsRectItem] = []
        self._piece_items: dict[Square, PieceItem] = {}
        self._coord_items: list[QGraphicsSimpleTextItem] = []

        self._draw_board()

    # Public API
    def set_position(self, position: Position) -> None:
        self._position = position
        self._clear_selection()
        self._sync_pieces()

    def set_interactive(self, interactive: bool) -> None:
        self._interactive = interactive

    def set_flipped(self, flipped: bool) -> None:
        self._flipped = flipped
        self._draw_board()
        if self._position:
            self._sync_pieces()

    def is_flipped(self) -> bool:
        return self._flipped

    def set_theme(self, theme: BoardTheme) -> None:
        self._theme = theme
        self._draw_board()
        if self._position:
            self._sync_pieces()

    def set_show_coordinates(self, visible: bool) -> None:
        self._show_coordinates = visible
        for item in self._coord_items:
            item.setVisible(visible)

    def set_show_legal_moves(self, visible: bool) -> None:
        self._show_legal_moves = visible
        if not visible:
            self._clear_items(self._legal_dot_items)

    def set_animate_moves(self, enabled: bool) -> None:
        self._animate_moves = enabled

    def highlight_last_move(self, move: Move | None) -> None:
        self._clear_last_move_highlights()
        if move is None:
            return
        for sq, color in [
            (move.from_sq, self._theme.last_move_from),
            (move.to_sq, self._theme.last_move_to),
        ]:
            rect = self._make_highlight(sq, color)
            rect.setZValue(0.5)
            self._last_move_highlights.append(rect)

    def highlight_check(self) -> None:
        self._clear_items(self._highlight_items)
        if self._position is None:
            return
        gen = MoveGenerator(self._position)
        color = self._position.side_to_move
        if gen.is_in_check(color):
            king_sq = self._position.board.king_square(color)
            rect = self._make_highlight(king_sq, self._theme.highlight_check)
            rect.setZValue(0.6)
            self._highlight_items.append(rect)

    # Rendering
    def _draw_board(self) -> None:
        _draw_board(self)

    def _sync_pieces(self) -> None:
        _sync_pieces(self)

    def _visual_coords(self, file: int, rank: int) -> tuple[int, int]:
        return _visual_coords(self, file, rank)

    def _pos_to_square(self, pos: QPointF) -> Square | None:
        return _pos_to_square(self, pos)

    def _make_highlight(self, sq: Square, color: QColor) -> QGraphicsRectItem:
        return _make_highlight(self, sq, color)

    def _clear_items(self, items: list[QGraphicsRectItem]) -> None:
        _clear_items(self, items)

    # Animation
    def animate_and_sync(
        self,
        move: Move,
        new_position: Position,
        *,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        _animate_and_sync(
            self,
            move,
            new_position,
            animation_cls=QPropertyAnimation,
            on_done=on_done,
        )

    # Mouse interaction
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if not self._interactive or self._position is None or event is None:
            return super().mousePressEvent(event)
        if _handle_mouse_press(self, event):
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if (
            self._position is not None
            and event is not None
            and _handle_mouse_release(self, event)
        ):
            return
        super().mouseReleaseEvent(event)

    # Selection and move resolution
    def _select_square(self, sq: Square) -> None:
        _select_square(self, sq)

    def _clear_selection(self) -> None:
        _clear_selection(self)

    def _clear_last_move_highlights(self) -> None:
        self._clear_items(self._last_move_highlights)

    def _find_legal_move(self, from_sq: Square, to_sq: Square) -> Move | None:
        return _find_legal_move(
            self,
            from_sq,
            to_sq,
            promotion_dialog_cls=PromotionDialog,
        )
