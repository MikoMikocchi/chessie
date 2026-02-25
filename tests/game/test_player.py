"""Tests for Player implementations."""

from chessie.core.enums import Color
from chessie.core.notation import STARTING_FEN, position_from_fen
from chessie.game.player import AIPlayer, HumanPlayer


class TestHumanPlayer:
    def test_properties(self) -> None:
        p = HumanPlayer(Color.WHITE, "Alice")
        assert p.color == Color.WHITE
        assert p.name == "Alice"
        assert p.is_human is True

    def test_default_name(self) -> None:
        p = HumanPlayer(Color.BLACK)
        assert "black" in p.name.lower()

    def test_request_move_noop(self) -> None:
        p = HumanPlayer(Color.WHITE)
        pos = position_from_fen(STARTING_FEN)
        p.request_move(pos)  # should not raise

    def test_cancel_noop(self) -> None:
        p = HumanPlayer(Color.WHITE)
        p.cancel()  # should not raise


class TestAIPlayer:
    def test_properties(self) -> None:
        p = AIPlayer(Color.BLACK, "Chessie AI")
        assert p.color == Color.BLACK
        assert p.name == "Chessie AI"
        assert p.is_human is False

    def test_request_move_calls_callback(self) -> None:
        called_with = []
        p = AIPlayer(
            Color.BLACK,
            on_request_move=lambda pos: called_with.append(pos),
        )
        pos = position_from_fen(STARTING_FEN)
        p.request_move(pos)
        assert len(called_with) == 1
        assert called_with[0] is pos

    def test_cancel_calls_callback(self) -> None:
        cancelled = []
        p = AIPlayer(
            Color.BLACK,
            on_cancel=lambda: cancelled.append(True),
        )
        p.cancel()
        assert cancelled == [True]

    def test_no_callback_no_error(self) -> None:
        p = AIPlayer(Color.BLACK)
        pos = position_from_fen(STARTING_FEN)
        p.request_move(pos)
        p.cancel()
