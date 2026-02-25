"""Legal and pseudo-legal move generation + attack detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chessie.core.enums import CastlingRights, Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.types import Square, file_of, make_square, rank_of

if TYPE_CHECKING:
    from chessie.core.position import Position

# ── Direction tables ─────────────────────────────────────────────────────────

KNIGHT_OFFSETS: list[tuple[int, int]] = [
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
]

KING_OFFSETS: list[tuple[int, int]] = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]

BISHOP_DIRS: list[tuple[int, int]] = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRS: list[tuple[int, int]] = BISHOP_DIRS + ROOK_DIRS


class MoveGenerator:
    """Generates legal moves for a given :class:`Position`.

    The generator mutates the position via ``make_move`` / ``unmake_move``
    internally but always restores it before returning.
    """

    __slots__ = ("_pos", "_board")

    def __init__(self, position: Position) -> None:
        self._pos = position
        self._board = position.board

    # ── Public API ───────────────────────────────────────────────────────

    def generate_legal_moves(self) -> list[Move]:
        """All strictly legal moves for the side to move."""
        legal: list[Move] = []
        for move in self.generate_pseudo_legal_moves():
            self._pos.make_move(move)
            # After making the move, side_to_move has flipped.
            # We check if the *moving* side's king is now attacked.
            if not self.is_in_check(self._pos.side_to_move.opposite):
                legal.append(move)
            self._pos.unmake_move(move)
        return legal

    def generate_pseudo_legal_moves(self) -> list[Move]:
        """All pseudo-legal moves (may leave own king in check)."""
        moves: list[Move] = []
        color = self._pos.side_to_move
        for sq in self._board.all_pieces(color):
            piece = self._board[sq]
            assert piece is not None
            pt = piece.piece_type

            if pt == PieceType.PAWN:
                self._gen_pawn(sq, color, moves)
            elif pt == PieceType.KNIGHT:
                self._gen_knight(sq, color, moves)
            elif pt == PieceType.BISHOP:
                self._gen_sliding(sq, color, BISHOP_DIRS, moves)
            elif pt == PieceType.ROOK:
                self._gen_sliding(sq, color, ROOK_DIRS, moves)
            elif pt == PieceType.QUEEN:
                self._gen_sliding(sq, color, QUEEN_DIRS, moves)
            elif pt == PieceType.KING:
                self._gen_king(sq, color, moves)
        return moves

    # ── Attack detection (public) ────────────────────────────────────────

    def is_in_check(self, color: Color) -> bool:
        """Is *color*'s king attacked by the opponent?"""
        king_sq = self._board.king_square(color)
        return self.is_square_attacked(king_sq, color.opposite)

    def is_square_attacked(self, sq: Square, by_color: Color) -> bool:
        """Is *sq* attacked by any piece of *by_color*?"""
        f, r = file_of(sq), rank_of(sq)

        # ── Pawns ────────────────────────────────────────────────────
        pawn_rank_dir = -1 if by_color == Color.WHITE else 1
        for df in (-1, 1):
            af, ar = f + df, r + pawn_rank_dir
            if 0 <= af < 8 and 0 <= ar < 8:
                p = self._board[make_square(af, ar)]
                if (
                    p is not None
                    and p.color == by_color
                    and p.piece_type == PieceType.PAWN
                ):
                    return True

        # ── Knights ──────────────────────────────────────────────────
        for df, dr in KNIGHT_OFFSETS:
            af, ar = f + df, r + dr
            if 0 <= af < 8 and 0 <= ar < 8:
                p = self._board[make_square(af, ar)]
                if (
                    p is not None
                    and p.color == by_color
                    and p.piece_type == PieceType.KNIGHT
                ):
                    return True

        # ── King ─────────────────────────────────────────────────────
        for df, dr in KING_OFFSETS:
            af, ar = f + df, r + dr
            if 0 <= af < 8 and 0 <= ar < 8:
                p = self._board[make_square(af, ar)]
                if (
                    p is not None
                    and p.color == by_color
                    and p.piece_type == PieceType.KING
                ):
                    return True

        # ── Bishops / Queens (diagonals) ─────────────────────────────
        for df, dr in BISHOP_DIRS:
            af, ar = f + df, r + dr
            while 0 <= af < 8 and 0 <= ar < 8:
                p = self._board[make_square(af, ar)]
                if p is not None:
                    if p.color == by_color and p.piece_type in (
                        PieceType.BISHOP,
                        PieceType.QUEEN,
                    ):
                        return True
                    break
                af += df
                ar += dr

        # ── Rooks / Queens (straights) ───────────────────────────────
        for df, dr in ROOK_DIRS:
            af, ar = f + df, r + dr
            while 0 <= af < 8 and 0 <= ar < 8:
                p = self._board[make_square(af, ar)]
                if p is not None:
                    if p.color == by_color and p.piece_type in (
                        PieceType.ROOK,
                        PieceType.QUEEN,
                    ):
                        return True
                    break
                af += df
                ar += dr

        return False

    # ── Piece-specific generators (private) ──────────────────────────────

    def _gen_pawn(self, sq: Square, color: Color, moves: list[Move]) -> None:
        f, r = file_of(sq), rank_of(sq)
        direction = 1 if color == Color.WHITE else -1
        start_rank = 1 if color == Color.WHITE else 6
        promo_rank = 7 if color == Color.WHITE else 0

        to_r = r + direction
        if not (0 <= to_r < 8):
            return

        # ── Single push ──────────────────────────────────────────────
        to_sq = make_square(f, to_r)
        if self._board.is_empty(to_sq):
            if to_r == promo_rank:
                for pt in (
                    PieceType.QUEEN,
                    PieceType.ROOK,
                    PieceType.BISHOP,
                    PieceType.KNIGHT,
                ):
                    moves.append(Move(sq, to_sq, MoveFlag.PROMOTION, pt))
            else:
                moves.append(Move(sq, to_sq))
                # ── Double push ──────────────────────────────────────
                if r == start_rank:
                    to_sq2 = make_square(f, r + 2 * direction)
                    if self._board.is_empty(to_sq2):
                        moves.append(Move(sq, to_sq2, MoveFlag.DOUBLE_PAWN))

        # ── Captures (including en passant) ──────────────────────────
        for df in (-1, 1):
            cf = f + df
            if not (0 <= cf < 8):
                continue
            cap_sq = make_square(cf, to_r)
            target = self._board[cap_sq]
            if target is not None and target.color != color:
                if to_r == promo_rank:
                    for pt in (
                        PieceType.QUEEN,
                        PieceType.ROOK,
                        PieceType.BISHOP,
                        PieceType.KNIGHT,
                    ):
                        moves.append(Move(sq, cap_sq, MoveFlag.PROMOTION, pt))
                else:
                    moves.append(Move(sq, cap_sq))
            elif cap_sq == self._pos.en_passant:
                moves.append(Move(sq, cap_sq, MoveFlag.EN_PASSANT))

    def _gen_knight(self, sq: Square, color: Color, moves: list[Move]) -> None:
        f, r = file_of(sq), rank_of(sq)
        for df, dr in KNIGHT_OFFSETS:
            af, ar = f + df, r + dr
            if 0 <= af < 8 and 0 <= ar < 8:
                to_sq = make_square(af, ar)
                target = self._board[to_sq]
                if target is None or target.color != color:
                    moves.append(Move(sq, to_sq))

    def _gen_sliding(
        self,
        sq: Square,
        color: Color,
        directions: list[tuple[int, int]],
        moves: list[Move],
    ) -> None:
        f, r = file_of(sq), rank_of(sq)
        for df, dr in directions:
            af, ar = f + df, r + dr
            while 0 <= af < 8 and 0 <= ar < 8:
                to_sq = make_square(af, ar)
                target = self._board[to_sq]
                if target is None:
                    moves.append(Move(sq, to_sq))
                elif target.color != color:
                    moves.append(Move(sq, to_sq))
                    break
                else:
                    break
                af += df
                ar += dr

    def _gen_king(self, sq: Square, color: Color, moves: list[Move]) -> None:
        f, r = file_of(sq), rank_of(sq)
        for df, dr in KING_OFFSETS:
            af, ar = f + df, r + dr
            if 0 <= af < 8 and 0 <= ar < 8:
                to_sq = make_square(af, ar)
                target = self._board[to_sq]
                if target is None or target.color != color:
                    moves.append(Move(sq, to_sq))

        self._gen_castling(sq, color, moves)

    def _gen_castling(self, king_sq: Square, color: Color, moves: list[Move]) -> None:
        if self.is_in_check(color):
            return

        rank = 0 if color == Color.WHITE else 7

        # ── Kingside (O-O) ───────────────────────────────────────────
        ks = (
            CastlingRights.WHITE_KINGSIDE
            if color == Color.WHITE
            else CastlingRights.BLACK_KINGSIDE
        )
        if self._pos.castling & ks:
            f_sq = make_square(5, rank)
            g_sq = make_square(6, rank)
            if (
                self._board.is_empty(f_sq)
                and self._board.is_empty(g_sq)
                and not self.is_square_attacked(f_sq, color.opposite)
                and not self.is_square_attacked(g_sq, color.opposite)
            ):
                moves.append(Move(king_sq, g_sq, MoveFlag.CASTLE_KINGSIDE))

        # ── Queenside (O-O-O) ────────────────────────────────────────
        qs = (
            CastlingRights.WHITE_QUEENSIDE
            if color == Color.WHITE
            else CastlingRights.BLACK_QUEENSIDE
        )
        if self._pos.castling & qs:
            b_sq = make_square(1, rank)
            c_sq = make_square(2, rank)
            d_sq = make_square(3, rank)
            # queenside path squares must be clear and safe
            if (
                self._board.is_empty(b_sq)
                and self._board.is_empty(c_sq)
                and self._board.is_empty(d_sq)
                and not self.is_square_attacked(c_sq, color.opposite)
                and not self.is_square_attacked(d_sq, color.opposite)
            ):
                moves.append(Move(king_sq, c_sq, MoveFlag.CASTLE_QUEENSIDE))
