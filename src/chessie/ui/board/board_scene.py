"""BoardScene — QGraphicsScene that draws the chessboard and pieces."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPointF,
    QPropertyAnimation,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QBrush, QColor, QFont, QPen
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsSimpleTextItem,
)

from chessie.core.enums import MoveFlag
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.types import Square, file_of, make_square, rank_of
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

    # ── Public API ───────────────────────────────────────────────────────

    def set_position(self, position: Position) -> None:
        """Update the displayed position (full redraw of pieces)."""
        self._position = position
        self._clear_selection()
        self._sync_pieces()

    def set_interactive(self, interactive: bool) -> None:
        """Enable / disable piece interaction."""
        self._interactive = interactive

    def set_flipped(self, flipped: bool) -> None:
        """Flip the board orientation."""
        self._flipped = flipped
        self._draw_board()
        if self._position:
            self._sync_pieces()

    def is_flipped(self) -> bool:
        """Return whether the board is currently flipped."""
        return self._flipped

    def set_theme(self, theme: BoardTheme) -> None:
        self._theme = theme
        self._draw_board()
        if self._position:
            self._sync_pieces()

    def set_show_coordinates(self, visible: bool) -> None:
        """Show or hide rank/file coordinate labels."""
        self._show_coordinates = visible
        for item in self._coord_items:
            item.setVisible(visible)

    def set_show_legal_moves(self, visible: bool) -> None:
        """Show or hide legal-move dot highlights."""
        self._show_legal_moves = visible
        if not visible:
            self._clear_items(self._legal_dot_items)

    def set_animate_moves(self, enabled: bool) -> None:
        """Enable or disable piece move animations."""
        self._animate_moves = enabled

    def highlight_last_move(self, move: Move | None) -> None:
        """Highlight origin/destination of the last played move."""
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
        """Highlight the king that is in check."""
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

    # ── Board drawing ────────────────────────────────────────────────────

    def _draw_board(self) -> None:
        """Draw or redraw the 64 squares and coordinates."""
        for sq_item in self._square_items.values():
            self.removeItem(sq_item)
        self._square_items.clear()
        for coord_item in self._coord_items:
            self.removeItem(coord_item)
        self._coord_items.clear()

        t = self.TILE
        font = QFont("Adwaita Sans", max(9, t // 8))

        for sq in range(64):
            f, r = file_of(sq), rank_of(sq)
            vf, vr = self._visual_coords(f, r)
            is_light = (f + r) % 2 == 0
            color = self._theme.dark_square if is_light else self._theme.light_square
            rect = QGraphicsRectItem(vf * t, vr * t, t, t)
            rect.setBrush(QBrush(color))
            rect.setPen(QPen(Qt.PenStyle.NoPen))
            rect.setZValue(0)
            self.addItem(rect)
            self._square_items[sq] = rect

            # Rank numbers (left edge)
            if f == 0:
                label = str(r + 1)
                txt = QGraphicsSimpleTextItem(label)
                txt.setFont(font)
                txt.setBrush(
                    QBrush(
                        self._theme.coord_dark if is_light else self._theme.coord_light
                    )
                )
                txt.setPos(vf * t + 2, vr * t + 1)
                txt.setZValue(0.3)
                txt.setVisible(self._show_coordinates)
                self.addItem(txt)
                self._coord_items.append(txt)

            # File letters (bottom edge)
            if r == 0:
                letter = chr(ord("a") + f)
                txt = QGraphicsSimpleTextItem(letter)
                txt.setFont(font)
                txt.setBrush(
                    QBrush(
                        self._theme.coord_dark if is_light else self._theme.coord_light
                    )
                )
                txt.setPos(vf * t + t - 12, vr * t + t - 16)
                txt.setZValue(0.3)
                txt.setVisible(self._show_coordinates)
                self.addItem(txt)
                self._coord_items.append(txt)

        self.setSceneRect(0, 0, 8 * t, 8 * t)

    # ── Piece synchronisation ────────────────────────────────────────────

    def _sync_pieces(self) -> None:
        """Re-create all piece items from the current position."""
        for item in self._piece_items.values():
            self.removeItem(item)
        self._piece_items.clear()

        if self._position is None:
            return

        t = self.TILE
        for sq in range(64):
            piece = self._position.board[sq]
            if piece is not None:
                item = PieceItem(piece, sq, t)
                f, r = file_of(sq), rank_of(sq)
                vf, vr = self._visual_coords(f, r)
                item.setPos(vf * t + item.margin, vr * t + item.margin)
                self.addItem(item)
                self._piece_items[sq] = item

    def animate_and_sync(
        self,
        move: Move,
        new_position: Position,
        *,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """Slide the moving piece to its destination, then full-sync.

        Falls back to an instant sync when animation is disabled or a
        previous animation is still running (e.g. fast PGN playback).
        """
        # If a previous animation is still running, stop it and fall back to
        # an instant sync for this call — avoids a corrupt piece-dict state.
        if self._active_anim is not None:
            self._active_anim.stop()
            self._active_anim = None
            self._position = new_position
            self._sync_pieces()
            if on_done:
                on_done()
            return

        item = self._piece_items.get(move.from_sq)
        if not self._animate_moves or item is None:
            self._position = new_position
            self._sync_pieces()
            if on_done:
                on_done()
            return

        t = self.TILE

        # ── Remove captured piece visually before animating ──────────────
        if move.flag == MoveFlag.EN_PASSANT:
            ep_sq = make_square(file_of(move.to_sq), rank_of(move.from_sq))
            cap = self._piece_items.pop(ep_sq, None)
            if cap is not None:
                self.removeItem(cap)
        else:
            cap = self._piece_items.pop(move.to_sq, None)
            if cap is not None:
                self.removeItem(cap)

        # ── Snap castling rook to its destination instantly ──────────────
        if move.flag in (MoveFlag.CASTLE_KINGSIDE, MoveFlag.CASTLE_QUEENSIDE):
            rank = rank_of(move.from_sq)
            if move.flag == MoveFlag.CASTLE_KINGSIDE:
                rook_from, rook_to = make_square(7, rank), make_square(5, rank)
            else:
                rook_from, rook_to = make_square(0, rank), make_square(3, rank)
            rook_item = self._piece_items.pop(rook_from, None)
            if rook_item is not None:
                rvf, rvr = self._visual_coords(file_of(rook_to), rank_of(rook_to))
                rook_item.setPos(rvf * t + rook_item.margin, rvr * t + rook_item.margin)
                self._piece_items[rook_to] = rook_item

        # ── Animate main piece ───────────────────────────────────────────
        vf, vr = self._visual_coords(file_of(move.to_sq), rank_of(move.to_sq))
        target = QPointF(vf * t + item.margin, vr * t + item.margin)

        # Update bookkeeping before the animation completes so that
        # mouse events during the slide see a consistent state.
        del self._piece_items[move.from_sq]
        self._piece_items[move.to_sq] = item
        item.square = move.to_sq
        item.setZValue(2)

        anim = QPropertyAnimation(item, b"pos", self)
        anim.setDuration(self._ANIM_DURATION_MS)
        anim.setStartValue(item.pos())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_finished() -> None:
            self._active_anim = None
            item.setZValue(1)
            self._position = new_position
            self._sync_pieces()
            if on_done:
                on_done()

        anim.finished.connect(_on_finished)
        self._active_anim = anim
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── Mouse interaction ────────────────────────────────────────────────

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if not self._interactive or self._position is None or event is None:
            return super().mousePressEvent(event)

        sq = self._pos_to_square(event.scenePos())
        if sq is None:
            self._clear_selection()
            return super().mousePressEvent(event)

        piece = self._position.board[sq]

        # Clicking a legal target → make the move
        if self._selected_sq is not None:
            move = self._find_legal_move(self._selected_sq, sq)
            if move is not None:
                self._clear_selection()
                self.move_made.emit(move)
                return

        # Select own piece
        if piece is not None and piece.color == self._position.side_to_move:
            self._select_square(sq)
            # Start drag
            if sq in self._piece_items:
                item = self._piece_items[sq]
                item.enable_drag(True)
                item.start_drag()
                self._dragging_item = item
        else:
            self._clear_selection()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if (
            self._dragging_item is not None
            and self._position is not None
            and event is not None
        ):
            item = self._dragging_item
            drop_sq = self._pos_to_square(event.scenePos())

            if drop_sq is not None and drop_sq != item.square:
                move = self._find_legal_move(item.square, drop_sq)
                if move is not None:
                    item.finish_drag()
                    item.enable_drag(False)
                    self._dragging_item = None
                    self._clear_selection()
                    self.move_made.emit(move)
                    return

            # Invalid drop — snap back
            item.cancel_drag()
            item.enable_drag(False)
            self._dragging_item = None

        super().mouseReleaseEvent(event)

    # ── Selection / highlights ───────────────────────────────────────────

    def _select_square(self, sq: Square) -> None:
        self._clear_selection()
        self._selected_sq = sq

        # Highlight origin
        rect = self._make_highlight(sq, self._theme.highlight_from)
        self._highlight_items.append(rect)

        # Legal move dots
        if self._position is not None:
            gen = MoveGenerator(self._position)
            self._legal_moves = gen.generate_legal_moves()
            if self._show_legal_moves:
                for m in self._legal_moves:
                    if m.from_sq == sq:
                        dot = self._make_highlight(m.to_sq, self._theme.highlight_to)
                        self._legal_dot_items.append(dot)

    def _clear_selection(self) -> None:
        self._selected_sq = None
        self._legal_moves = []
        self._clear_items(self._highlight_items)
        self._clear_items(self._legal_dot_items)

    def _clear_last_move_highlights(self) -> None:
        self._clear_items(self._last_move_highlights)

    def _clear_items(self, items: list[QGraphicsRectItem]) -> None:
        for item in items:
            self.removeItem(item)
        items.clear()

    # ── Move resolution ──────────────────────────────────────────────────

    def _find_legal_move(self, from_sq: Square, to_sq: Square) -> Move | None:
        """Find a single legal move from *from_sq* to *to_sq*.

        If multiple candidates exist (promotion), ask the user which piece to pick.
        """
        if not self._legal_moves:
            if self._position is None:
                return None
            gen = MoveGenerator(self._position)
            self._legal_moves = gen.generate_legal_moves()

        candidates = [
            m for m in self._legal_moves if m.from_sq == from_sq and m.to_sq == to_sq
        ]
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        if self._position is None:
            return None
        piece = self._position.board[from_sq]
        if piece is None:
            return None

        parent = self.views()[0] if self.views() else None
        promotion = PromotionDialog.ask(piece.color, parent)
        if promotion is None:
            return None

        for move in candidates:
            if move.promotion == promotion:
                return move
        return candidates[0]

    # ── Coordinate helpers ───────────────────────────────────────────────

    def _visual_coords(self, file: int, rank: int) -> tuple[int, int]:
        """Convert board file/rank to visual column/row."""
        if self._flipped:
            return 7 - file, rank
        return file, 7 - rank

    def _pos_to_square(self, pos: QPointF) -> Square | None:
        """Scene position → board square."""
        t = self.TILE
        col = int(pos.x() // t)
        row = int(pos.y() // t)
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        if self._flipped:
            f, r = 7 - col, row
        else:
            f, r = col, 7 - row
        return make_square(f, r)

    def _make_highlight(self, sq: Square, color: QColor) -> QGraphicsRectItem:
        """Create a coloured overlay rectangle on a square."""
        t = self.TILE
        f, r = file_of(sq), rank_of(sq)
        vf, vr = self._visual_coords(f, r)
        rect = QGraphicsRectItem(vf * t, vr * t, t, t)
        rect.setBrush(QBrush(color))
        rect.setPen(QPen(Qt.PenStyle.NoPen))
        rect.setZValue(0.8)
        self.addItem(rect)
        return rect
