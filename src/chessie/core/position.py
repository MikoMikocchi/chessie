"""Position — complete game state (board + metadata) with make/unmake."""

from __future__ import annotations

from dataclasses import dataclass

from chessie.core.board import Board
from chessie.core.enums import CastlingRights, Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.piece import Piece
from chessie.core.types import Square, file_of, make_square, rank_of
from chessie.core.zobrist import (
    castling_key as zobrist_castling_key,
)
from chessie.core.zobrist import (
    en_passant_key as zobrist_en_passant_key,
)
from chessie.core.zobrist import (
    piece_key as zobrist_piece_key,
)
from chessie.core.zobrist import (
    side_to_move_key as zobrist_side_to_move_key,
)


@dataclass(slots=True)
class _PositionState:
    """Snapshot saved before each move so we can undo it."""

    castling: CastlingRights
    en_passant: Square | None
    halfmove_clock: int
    captured_piece: Piece | None


class Position:
    """Full chess position: board + side to move + castling + en passant + clocks.

    Supports efficient :meth:`make_move` / :meth:`unmake_move` via an internal
    history stack (Command pattern).
    """

    __slots__ = (
        "board",
        "side_to_move",
        "castling",
        "en_passant",
        "halfmove_clock",
        "fullmove_number",
        "_zobrist_hash",
        "_history",
        "_key_stack",
        "_key_counts",
    )

    def __init__(
        self,
        board: Board | None = None,
        side_to_move: Color = Color.WHITE,
        castling: CastlingRights = CastlingRights.ALL,
        en_passant: Square | None = None,
        halfmove_clock: int = 0,
        fullmove_number: int = 1,
    ) -> None:
        self.board = board if board is not None else Board.initial()
        self.side_to_move = side_to_move
        self.castling = castling
        self.en_passant = en_passant
        self.halfmove_clock = halfmove_clock
        self.fullmove_number = fullmove_number
        self._zobrist_hash = self._compute_zobrist_hash()
        self._history: list[_PositionState] = []
        key = self._zobrist_hash
        self._key_stack: list[int] = [key]
        self._key_counts: dict[int, int] = {key: 1}

    # ── Core move operations ─────────────────────────────────────────────

    def make_move(self, move: Move) -> None:
        """Apply *move*, pushing undo state onto the history stack."""
        captured = self.board[move.to_sq]
        capture_sq = move.to_sq

        # En passant: the captured pawn sits on a different square
        if move.flag == MoveFlag.EN_PASSANT:
            ep_capture_sq = make_square(file_of(move.to_sq), rank_of(move.from_sq))
            captured = self.board[ep_capture_sq]
            capture_sq = ep_capture_sq

        # Save undo state
        self._history.append(
            _PositionState(
                castling=self.castling,
                en_passant=self.en_passant,
                halfmove_clock=self.halfmove_clock,
                captured_piece=captured,
            )
        )

        piece = self.board[move.from_sq]
        if piece is None:
            raise ValueError(f"No piece on {move.from_sq}")

        # Lift piece from origin
        self._toggle_piece_hash(piece, move.from_sq)
        self.board[move.from_sq] = None

        # Remove captured piece from the board (normal capture or en passant)
        if captured is not None:
            self._toggle_piece_hash(captured, capture_sq)
            self.board[capture_sq] = None

        # Place piece (handle promotion)
        placed_piece = piece
        if move.flag == MoveFlag.PROMOTION and move.promotion is not None:
            placed_piece = Piece(piece.color, move.promotion)
        self.board[move.to_sq] = placed_piece
        self._toggle_piece_hash(placed_piece, move.to_sq)

        # Slide the rook for castling
        if move.flag == MoveFlag.CASTLE_KINGSIDE:
            r = rank_of(move.from_sq)
            rook_from = make_square(7, r)
            rook_to = make_square(5, r)
            rook = self.board[rook_from]
            assert rook is not None
            self._toggle_piece_hash(rook, rook_from)
            self.board[rook_to] = rook
            self._toggle_piece_hash(rook, rook_to)
            self.board[rook_from] = None
        elif move.flag == MoveFlag.CASTLE_QUEENSIDE:
            r = rank_of(move.from_sq)
            rook_from = make_square(0, r)
            rook_to = make_square(3, r)
            rook = self.board[rook_from]
            assert rook is not None
            self._toggle_piece_hash(rook, rook_from)
            self.board[rook_to] = rook
            self._toggle_piece_hash(rook, rook_to)
            self.board[rook_from] = None

        # En passant target for the opponent
        next_en_passant: Square | None = None
        if move.flag == MoveFlag.DOUBLE_PAWN:
            next_en_passant = make_square(
                file_of(move.from_sq),
                (rank_of(move.from_sq) + rank_of(move.to_sq)) // 2,
            )
        self._set_en_passant(next_en_passant)

        # Castling rights
        self._update_castling(move, piece)

        # Clocks
        if piece.piece_type == PieceType.PAWN or captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if self.side_to_move == Color.BLACK:
            self.fullmove_number += 1

        self.side_to_move = self.side_to_move.opposite
        self._toggle_side_hash()
        key = self._zobrist_hash
        self._key_stack.append(key)
        self._key_counts[key] = self._key_counts.get(key, 0) + 1

    def unmake_move(self, move: Move) -> None:
        """Undo the last :meth:`make_move`."""
        state = self._history.pop()
        key = self._key_stack.pop()
        key_count = self._key_counts[key] - 1
        if key_count:
            self._key_counts[key] = key_count
        else:
            del self._key_counts[key]

        self.side_to_move = self.side_to_move.opposite
        if self.side_to_move == Color.BLACK:
            self.fullmove_number -= 1

        piece = self.board[move.to_sq]
        assert piece is not None

        # Restore pawn for promotion
        if move.flag == MoveFlag.PROMOTION:
            piece = Piece(piece.color, PieceType.PAWN)

        # Put the piece back; restore captured piece (or None)
        self.board[move.from_sq] = piece
        if move.flag == MoveFlag.EN_PASSANT:
            self.board[move.to_sq] = None
            ep_capture_sq = make_square(file_of(move.to_sq), rank_of(move.from_sq))
            self.board[ep_capture_sq] = state.captured_piece
        else:
            self.board[move.to_sq] = state.captured_piece

        # Undo rook slide for castling
        if move.flag == MoveFlag.CASTLE_KINGSIDE:
            r = rank_of(move.from_sq)
            self.board[make_square(7, r)] = self.board[make_square(5, r)]
            self.board[make_square(5, r)] = None
        elif move.flag == MoveFlag.CASTLE_QUEENSIDE:
            r = rank_of(move.from_sq)
            self.board[make_square(0, r)] = self.board[make_square(3, r)]
            self.board[make_square(3, r)] = None

        self.castling = state.castling
        self.en_passant = state.en_passant
        self.halfmove_clock = state.halfmove_clock
        self._zobrist_hash = self._key_stack[-1]

    # ── Castling bookkeeping ─────────────────────────────────────────────

    _ROOK_CORNERS: dict[Square, CastlingRights] = {
        make_square(0, 0): CastlingRights.WHITE_QUEENSIDE,
        make_square(7, 0): CastlingRights.WHITE_KINGSIDE,
        make_square(0, 7): CastlingRights.BLACK_QUEENSIDE,
        make_square(7, 7): CastlingRights.BLACK_KINGSIDE,
    }

    def _update_castling(self, move: Move, piece: Piece) -> None:
        next_castling = self.castling
        if piece.piece_type == PieceType.KING:
            if piece.color == Color.WHITE:
                next_castling &= ~CastlingRights.WHITE_BOTH
            else:
                next_castling &= ~CastlingRights.BLACK_BOTH

        for sq in (move.from_sq, move.to_sq):
            if sq in self._ROOK_CORNERS:
                next_castling &= ~self._ROOK_CORNERS[sq]

        self._set_castling(next_castling)

    def _toggle_piece_hash(self, piece: Piece, sq: Square) -> None:
        self._zobrist_hash ^= zobrist_piece_key(piece, sq)

    def _toggle_side_hash(self) -> None:
        self._zobrist_hash ^= zobrist_side_to_move_key()

    def _set_castling(self, castling: CastlingRights) -> None:
        if castling == self.castling:
            return
        self._zobrist_hash ^= zobrist_castling_key(self.castling)
        self.castling = castling
        self._zobrist_hash ^= zobrist_castling_key(self.castling)

    def _set_en_passant(self, en_passant: Square | None) -> None:
        if en_passant == self.en_passant:
            return
        if self.en_passant is not None:
            self._zobrist_hash ^= zobrist_en_passant_key(self.en_passant)
        self.en_passant = en_passant
        if self.en_passant is not None:
            self._zobrist_hash ^= zobrist_en_passant_key(self.en_passant)

    # ── Utilities ────────────────────────────────────────────────────────

    def copy(self) -> Position:
        """Deep copy without history."""
        pos = Position(
            board=self.board.copy(),
            side_to_move=self.side_to_move,
            castling=self.castling,
            en_passant=self.en_passant,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
        )
        pos._zobrist_hash = self._zobrist_hash
        pos._key_stack = self._key_stack.copy()
        pos._key_counts = self._key_counts.copy()
        return pos

    def repetition_count(self) -> int:
        """How many times the current position key occurred in game history."""
        key = self._key_stack[-1]
        return self._key_counts.get(key, 0)

    @property
    def zobrist_hash(self) -> int:
        """Current Zobrist key for the full position."""
        return self._key_stack[-1]

    def _position_key(self) -> int:
        return self.zobrist_hash

    def _compute_zobrist_hash(self) -> int:
        key = zobrist_castling_key(self.castling)
        if self.side_to_move == Color.BLACK:
            key ^= zobrist_side_to_move_key()
        if self.en_passant is not None:
            key ^= zobrist_en_passant_key(self.en_passant)

        for sq in range(64):
            piece = self.board[sq]
            if piece is not None:
                key ^= zobrist_piece_key(piece, sq)
        return key
