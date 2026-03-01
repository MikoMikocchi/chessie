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

    # Product policy:
    # - Claim-based draws: 50-move rule, threefold repetition.
    # - Automatic draws: insufficient material, 75-move rule, fivefold repetition.

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
        white_occ = board.all_pieces_bitboard(Color.WHITE)
        black_occ = board.all_pieces_bitboard(Color.BLACK)
        total = (white_occ | black_occ).bit_count()

        # K vs K
        if total == 2:
            return True

        # K+minor vs K
        if total == 3:
            return (
                board.has_piece(Color.WHITE, PieceType.KNIGHT)
                or board.has_piece(Color.WHITE, PieceType.BISHOP)
                or board.has_piece(Color.BLACK, PieceType.KNIGHT)
                or board.has_piece(Color.BLACK, PieceType.BISHOP)
            )

        # K+B vs K+B with same-colour bishops
        if total == 4:
            wb = board.pieces_bitboard(Color.WHITE, PieceType.BISHOP)
            bb = board.pieces_bitboard(Color.BLACK, PieceType.BISHOP)
            if wb.bit_count() == 1 and bb.bit_count() == 1:
                w_sq = (wb & -wb).bit_length() - 1
                b_sq = (bb & -bb).bit_length() - 1
                w_color = (file_of(w_sq) + rank_of(w_sq)) % 2
                b_color = (file_of(b_sq) + rank_of(b_sq)) % 2
                return w_color == b_color

        return False

    @staticmethod
    def is_fifty_move_rule(position: Position) -> bool:
        return position.halfmove_clock >= 100  # 100 half-moves = 50 full moves

    @staticmethod
    def is_seventy_five_move_rule(position: Position) -> bool:
        return position.halfmove_clock >= 150  # 150 half-moves = 75 full moves

    @staticmethod
    def is_threefold_repetition(position: Position) -> bool:
        return position.repetition_count() >= 3

    @staticmethod
    def is_fivefold_repetition(position: Position) -> bool:
        return position.repetition_count() >= 5

    @staticmethod
    def is_claimable_draw(position: Position) -> bool:
        """Whether the side to move may claim an immediate draw by rule."""
        return Rules.is_fifty_move_rule(position) or Rules.is_threefold_repetition(
            position
        )

    @staticmethod
    def is_automatic_draw(position: Position) -> bool:
        """Whether the position is an automatic draw without player claim."""
        return (
            Rules.is_insufficient_material(position)
            or Rules.is_seventy_five_move_rule(position)
            or Rules.is_fivefold_repetition(position)
        )

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

        if Rules.is_automatic_draw(position):
            return GameResult.DRAW

        return GameResult.IN_PROGRESS
