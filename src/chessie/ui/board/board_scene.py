"""BoardScene — QGraphicsScene that draws the chessboard and pieces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPen
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsSimpleTextItem,
)

from chessie.core.enums import PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.types import Square, file_of, make_square, rank_of
from chessie.ui.board.piece_item import PieceItem
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
        font = QFont("Helvetica Neue", max(9, t // 8))

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
                item.setPos(vf * t, vr * t)
                self.addItem(item)
                self._piece_items[sq] = item

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

        If multiple (promotions), the promotion dialog will be needed.
        For now, auto-queen.
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
        # Multiple → promotions, pick queen by default (dialog will override later)
        queen_move = [m for m in candidates if m.promotion == PieceType.QUEEN]
        return queen_move[0] if queen_move else candidates[0]

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
