"""High-level chess rules: checkmate, stalemate, draw detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chessie.core.enums import Color, GameResult, PieceType
from chessie.core.move_generator import MoveGenerator
from chessie.core.types import file_of, rank_of

if TYPE_CHECKING:
    from chessie.core.position import Position


class Rules:
    """Static rule-checker that operates on a :class:`Position`."""

    @staticmethod
    def is_in_check(position: Position) -> bool:
        gen = MoveGenerator(position)
        return gen.is_in_check(position.side_to_move)

    @staticmethod
    def is_checkmate(position: Position) -> bool:
        if not Rules.is_in_check(position):
            return False
        gen = MoveGenerator(position)
        return len(gen.generate_legal_moves()) == 0

    @staticmethod
    def is_stalemate(position: Position) -> bool:
        if Rules.is_in_check(position):
            return False
        gen = MoveGenerator(position)
        return len(gen.generate_legal_moves()) == 0

    @staticmethod
    def is_insufficient_material(position: Position) -> bool:
        """K vs K, K+B vs K, K+N vs K, K+B vs K+B (same-color bishops)."""
        board = position.board
        white = board.all_pieces(Color.WHITE)
        black = board.all_pieces(Color.BLACK)
        total = len(white) + len(black)

        # K vs K
        if total == 2:
            return True

        # K+minor vs K
        if total == 3:
            for sq in white + black:
                p = board[sq]
                if p is not None and p.piece_type in (PieceType.KNIGHT, PieceType.BISHOP):
                    return True

        # K+B vs K+B with same-colour bishops
        if total == 4:
            wb = board.pieces(Color.WHITE, PieceType.BISHOP)
            bb = board.pieces(Color.BLACK, PieceType.BISHOP)
            if len(wb) == 1 and len(bb) == 1:
                w_color = (file_of(wb[0]) + rank_of(wb[0])) % 2
                b_color = (file_of(bb[0]) + rank_of(bb[0])) % 2
                return w_color == b_color

        return False

    @staticmethod
    def is_fifty_move_rule(position: Position) -> bool:
        return position.halfmove_clock >= 100  # 100 half-moves = 50 full moves

    @staticmethod
    def game_result(position: Position) -> GameResult:
        """Determine the current game result."""
        gen = MoveGenerator(position)
        legal_moves = gen.generate_legal_moves()

        if not legal_moves:
            if gen.is_in_check(position.side_to_move):
                return (
                    GameResult.BLACK_WINS
                    if position.side_to_move == Color.WHITE
                    else GameResult.WHITE_WINS
                )
            return GameResult.DRAW  # stalemate

        if Rules.is_insufficient_material(position):
            return GameResult.DRAW

        if Rules.is_fifty_move_rule(position):
            return GameResult.DRAW

        return GameResult.IN_PROGRESS
