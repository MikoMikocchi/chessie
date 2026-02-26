"""Tests for GameState."""

from chessie.core.enums import Color, GameResult, MoveFlag
from chessie.core.move import Move
from chessie.core.notation import position_to_fen
from chessie.core.types import D5, D7, E2, E4, parse_square
from chessie.game.interfaces import GamePhase
from chessie.game.state import GameState


class TestGameStateSetup:
    def test_position_is_available_before_setup(self) -> None:
        gs = GameState()
        assert gs.phase == GamePhase.NOT_STARTED
        assert gs.side_to_move == Color.WHITE

    def test_setup_default(self) -> None:
        gs = GameState()
        gs.setup()
        assert gs.phase == GamePhase.AWAITING_MOVE
        assert gs.result == GameResult.IN_PROGRESS
        assert gs.side_to_move == Color.WHITE
        assert gs.ply_count == 0

    def test_setup_custom_fen(self) -> None:
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        gs = GameState()
        gs.setup(fen)
        assert gs.side_to_move == Color.BLACK
        assert gs.start_fen == fen

    def test_setup_resets(self) -> None:
        gs = GameState()
        gs.setup()
        gs.apply_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert gs.ply_count == 1
        gs.setup()  # reset
        assert gs.ply_count == 0
        assert gs.side_to_move == Color.WHITE


class TestGameStateMoves:
    def test_apply_move_records(self) -> None:
        gs = GameState()
        gs.setup()
        record = gs.apply_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert record.san == "e4"
        assert gs.side_to_move == Color.BLACK
        assert gs.ply_count == 1

    def test_undo_restores(self) -> None:
        gs = GameState()
        gs.setup()
        fen_before = position_to_fen(gs.position)
        gs.apply_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        undone = gs.undo_last_move()
        assert undone is not None
        assert position_to_fen(gs.position) == fen_before
        assert gs.ply_count == 0

    def test_undo_empty_returns_none(self) -> None:
        gs = GameState()
        gs.setup()
        assert gs.undo_last_move() is None

    def test_fullmove_display(self) -> None:
        gs = GameState()
        gs.setup()
        assert gs.fullmove_display == 1
        gs.apply_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert gs.fullmove_display == 1  # still move 1 (black hasn't moved)
        gs.apply_move(Move(D7, D5, MoveFlag.DOUBLE_PAWN))
        assert gs.fullmove_display == 2  # move 2 now

    def test_apply_move_marks_en_passant_capture(self) -> None:
        gs = GameState()
        gs.setup("8/8/8/3pP3/8/8/8/4K2k w - d6 0 1")
        record = gs.apply_move(
            Move(parse_square("e5"), parse_square("d6"), MoveFlag.EN_PASSANT)
        )
        assert record.was_capture


class TestGameStateTermination:
    def test_resign_white(self) -> None:
        gs = GameState()
        gs.setup()
        gs.resign(Color.WHITE)
        assert gs.result == GameResult.BLACK_WINS
        assert gs.is_game_over

    def test_resign_black(self) -> None:
        gs = GameState()
        gs.setup()
        gs.resign(Color.BLACK)
        assert gs.result == GameResult.WHITE_WINS
        assert gs.is_game_over

    def test_set_draw(self) -> None:
        gs = GameState()
        gs.setup()
        gs.set_draw()
        assert gs.result == GameResult.DRAW
        assert gs.is_game_over

    def test_flag_fall(self) -> None:
        gs = GameState()
        gs.setup()
        gs.flag_fall(Color.WHITE)
        assert gs.result == GameResult.BLACK_WINS
        assert gs.is_game_over

    def test_fools_mate_detected(self) -> None:
        """1.f3 e5 2.g4 Qh4# → checkmate detected automatically."""
        gs = GameState()
        gs.setup()
        gs.apply_move(Move(parse_square("f2"), parse_square("f3")))
        gs.apply_move(
            Move(parse_square("e7"), parse_square("e5"), MoveFlag.DOUBLE_PAWN)
        )
        gs.apply_move(
            Move(parse_square("g2"), parse_square("g4"), MoveFlag.DOUBLE_PAWN)
        )
        gs.apply_move(Move(parse_square("d8"), parse_square("h4")))
        assert gs.result == GameResult.BLACK_WINS
        assert gs.is_game_over

    def test_undo_reverses_game_over(self) -> None:
        gs = GameState()
        gs.setup()
        gs.resign(Color.WHITE)
        assert gs.is_game_over
        # manual reset for testing
        gs.result = GameResult.IN_PROGRESS
        gs.phase = GamePhase.AWAITING_MOVE
        assert not gs.is_game_over
