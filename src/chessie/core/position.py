"""Position — complete game state (board + metadata) with make/unmake."""

from __future__ import annotations

from dataclasses import dataclass

from chessie.core.board import Board
from chessie.core.enums import CastlingRights, Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.piece import Piece
from chessie.core.types import Square, file_of, make_square, rank_of


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
        self._history: list[_PositionState] = []
        key = self._position_key()
        self._key_stack: list[
            tuple[tuple[Piece | None, ...], Color, CastlingRights, Square | None]
        ] = [key]
        self._key_counts: dict[
            tuple[tuple[Piece | None, ...], Color, CastlingRights, Square | None],
            int,
        ] = {key: 1}

    # ── Core move operations ─────────────────────────────────────────────

    def make_move(self, move: Move) -> None:
        """Apply *move*, pushing undo state onto the history stack."""
        captured = self.board[move.to_sq]

        # En passant: the captured pawn sits on a different square
        if move.flag == MoveFlag.EN_PASSANT:
            ep_capture_sq = make_square(file_of(move.to_sq), rank_of(move.from_sq))
            captured = self.board[ep_capture_sq]
            self.board[ep_capture_sq] = None

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
        self.board[move.from_sq] = None

        # Place piece (handle promotion)
        if move.flag == MoveFlag.PROMOTION and move.promotion is not None:
            self.board[move.to_sq] = Piece(piece.color, move.promotion)
        else:
            self.board[move.to_sq] = piece

        # Slide the rook for castling
        if move.flag == MoveFlag.CASTLE_KINGSIDE:
            r = rank_of(move.from_sq)
            self.board[make_square(5, r)] = self.board[make_square(7, r)]
            self.board[make_square(7, r)] = None
        elif move.flag == MoveFlag.CASTLE_QUEENSIDE:
            r = rank_of(move.from_sq)
            self.board[make_square(3, r)] = self.board[make_square(0, r)]
            self.board[make_square(0, r)] = None

        # En passant target for the opponent
        if move.flag == MoveFlag.DOUBLE_PAWN:
            self.en_passant = make_square(
                file_of(move.from_sq),
                (rank_of(move.from_sq) + rank_of(move.to_sq)) // 2,
            )
        else:
            self.en_passant = None

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
        key = self._position_key()
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

    # ── Castling bookkeeping ─────────────────────────────────────────────

    _ROOK_CORNERS: dict[Square, CastlingRights] = {
        make_square(0, 0): CastlingRights.WHITE_QUEENSIDE,
        make_square(7, 0): CastlingRights.WHITE_KINGSIDE,
        make_square(0, 7): CastlingRights.BLACK_QUEENSIDE,
        make_square(7, 7): CastlingRights.BLACK_KINGSIDE,
    }

    def _update_castling(self, move: Move, piece: Piece) -> None:
        if piece.piece_type == PieceType.KING:
            if piece.color == Color.WHITE:
                self.castling &= ~CastlingRights.WHITE_BOTH
            else:
                self.castling &= ~CastlingRights.BLACK_BOTH

        for sq in (move.from_sq, move.to_sq):
            if sq in self._ROOK_CORNERS:
                self.castling &= ~self._ROOK_CORNERS[sq]

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
        pos._key_stack = self._key_stack.copy()
        pos._key_counts = self._key_counts.copy()
        return pos

    def repetition_count(self) -> int:
        """How many times the current position key occurred in game history."""
        key = self._key_stack[-1]
        return self._key_counts.get(key, 0)

    def _position_key(
        self,
    ) -> tuple[tuple[Piece | None, ...], Color, CastlingRights, Square | None]:
        return (
            tuple(self.board[sq] for sq in range(64)),
            self.side_to_move,
            self.castling,
            self.en_passant,
        )
