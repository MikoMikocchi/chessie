"""Tests for Rules: checkmate, stalemate, draw detection."""

from chessie.core.enums import GameResult
from chessie.core.move import Move
from chessie.core.notation import position_from_fen
from chessie.core.rules import Rules
from chessie.core.types import parse_square


class TestCheck:
    def test_starting_not_in_check(self) -> None:
        pos = position_from_fen(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        assert not Rules.is_in_check(pos)

    def test_fools_mate_in_check(self) -> None:
        # After 1.f3 e5 2.g4 Qh4# — white is in check
        pos = position_from_fen(
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        )
        assert Rules.is_in_check(pos)


class TestCheckmate:
    def test_fools_mate(self) -> None:
        pos = position_from_fen(
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        )
        assert Rules.is_checkmate(pos)
        assert Rules.game_result(pos) == GameResult.BLACK_WINS

    def test_back_rank_mate(self) -> None:
        # R on a8 checks black king d8; white king d6 covers all escapes
        pos = position_from_fen("R2k4/8/3K4/8/8/8/8/8 b - - 0 1")
        assert Rules.is_checkmate(pos)
        assert Rules.game_result(pos) == GameResult.WHITE_WINS

    def test_not_checkmate_when_can_escape(self) -> None:
        # King can move out of check
        pos = position_from_fen("4k3/8/8/8/8/8/8/r3K3 w - - 0 1")
        assert not Rules.is_checkmate(pos)


class TestStalemate:
    def test_king_trapped(self) -> None:
        # Black king on h8, white K on f6, white Q on g6
        pos = position_from_fen("7k/8/5KQ1/8/8/8/8/8 b - - 0 1")
        assert Rules.is_stalemate(pos)
        assert Rules.game_result(pos) == GameResult.DRAW

    def test_not_stalemate_when_has_moves(self) -> None:
        pos = position_from_fen("7k/8/5K2/8/8/8/8/8 b - - 0 1")
        assert not Rules.is_stalemate(pos)


class TestInsufficientMaterial:
    def test_k_vs_k(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/8/8 w - - 0 1")
        assert Rules.is_insufficient_material(pos)

    def test_k_bishop_vs_k(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/3B4/8 w - - 0 1")
        assert Rules.is_insufficient_material(pos)

    def test_k_knight_vs_k(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/3N4/8 w - - 0 1")
        assert Rules.is_insufficient_material(pos)

    def test_k_rook_vs_k_sufficient(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/3R4/8 w - - 0 1")
        assert not Rules.is_insufficient_material(pos)

    def test_kp_vs_k_sufficient(self) -> None:
        pos = position_from_fen("8/8/4k3/8/4P3/4K3/8/8 w - - 0 1")
        assert not Rules.is_insufficient_material(pos)


class TestFiftyMoveRule:
    def test_not_triggered_at_start(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/8/8 w - - 0 1")
        assert not Rules.is_fifty_move_rule(pos)

    def test_triggered_at_100_halfmoves(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/8/8 w - - 100 51")
        assert Rules.is_fifty_move_rule(pos)

    def test_seventy_five_move_rule(self) -> None:
        pos = position_from_fen("8/8/4k3/8/8/4K3/8/8 w - - 150 76")
        assert Rules.is_seventy_five_move_rule(pos)


class TestRepetition:
    def test_threefold_repetition_detected(self) -> None:
        pos = position_from_fen("4k2n/8/8/8/8/8/8/4K2N w - - 0 1")

        for _ in range(2):
            pos.make_move(Move(parse_square("h1"), parse_square("f2")))
            pos.make_move(Move(parse_square("h8"), parse_square("f7")))
            pos.make_move(Move(parse_square("f2"), parse_square("h1")))
            pos.make_move(Move(parse_square("f7"), parse_square("h8")))

        assert Rules.is_threefold_repetition(pos)
        assert Rules.is_claimable_draw(pos)
        assert Rules.game_result(pos) == GameResult.IN_PROGRESS


class TestDrawPolicy:
    def test_fifty_move_is_claimable_not_automatic(self) -> None:
        pos = position_from_fen("4k3/8/8/8/8/8/4K2R/7r w - - 100 51")
        assert Rules.is_fifty_move_rule(pos)
        assert Rules.is_claimable_draw(pos)
        assert not Rules.is_automatic_draw(pos)
        assert Rules.game_result(pos) == GameResult.IN_PROGRESS

    def test_seventy_five_move_is_automatic(self) -> None:
        pos = position_from_fen("4k3/8/8/8/8/8/4K2R/7r w - - 150 76")
        assert Rules.is_seventy_five_move_rule(pos)
        assert Rules.is_automatic_draw(pos)
        assert Rules.game_result(pos) == GameResult.DRAW


class TestGameResult:
    def test_in_progress_at_start(self) -> None:
        pos = position_from_fen(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        assert Rules.game_result(pos) == GameResult.IN_PROGRESS
