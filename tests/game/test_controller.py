"""Tests for GameController — the orchestrator."""

import time

import pytest

from chessie.core.enums import Color, GameResult, MoveFlag
from chessie.core.move import Move
from chessie.core.types import D5, D7, E2, E4, parse_square
from chessie.game.controller import GameController
from chessie.game.interfaces import DrawOffer, GamePhase, TimeControl
from chessie.game.player import AIPlayer, HumanPlayer


def _make_hh_controller(
    time_control: TimeControl | None = None,
    fen: str | None = None,
) -> GameController:
    """Helper: human vs human game."""
    ctrl = GameController()
    ctrl.new_game(
        HumanPlayer(Color.WHITE, "W"),
        HumanPlayer(Color.BLACK, "B"),
        time_control=time_control,
        fen=fen,
    )
    return ctrl


class TestNewGame:
    def test_phase_awaiting(self) -> None:
        ctrl = _make_hh_controller()
        assert ctrl.state.phase == GamePhase.AWAITING_MOVE

    def test_players_assigned(self) -> None:
        ctrl = _make_hh_controller()
        assert ctrl.player(Color.WHITE) is not None
        assert ctrl.player(Color.BLACK) is not None

    def test_current_player_is_white(self) -> None:
        ctrl = _make_hh_controller()
        cp = ctrl.current_player
        assert cp is not None and cp.color == Color.WHITE

    def test_custom_fen(self) -> None:
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        ctrl = _make_hh_controller(fen=fen)
        assert ctrl.state.side_to_move == Color.BLACK


class TestSubmitMove:
    def test_legal_move_accepted(self) -> None:
        ctrl = _make_hh_controller()
        ok = ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert ok
        assert ctrl.state.side_to_move == Color.BLACK

    def test_illegal_move_rejected(self) -> None:
        ctrl = _make_hh_controller()
        ok = ctrl.submit_move(Move(E2, parse_square("e5")))  # can't jump 3 ranks
        assert not ok
        assert ctrl.state.side_to_move == Color.WHITE

    def test_move_event_fires(self) -> None:
        ctrl = _make_hh_controller()
        events: list[str] = []
        ctrl.events.on_move.append(lambda m, san, st: events.append(san))
        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert events == ["e4"]

    def test_game_over_event_on_checkmate(self) -> None:
        ctrl = _make_hh_controller()
        results: list[GameResult] = []
        ctrl.events.on_game_over.append(lambda r: results.append(r))
        # Fool's mate: 1.f3 e5 2.g4 Qh4#
        ctrl.submit_move(Move(parse_square("f2"), parse_square("f3")))
        ctrl.submit_move(
            Move(parse_square("e7"), parse_square("e5"), MoveFlag.DOUBLE_PAWN)
        )
        ctrl.submit_move(
            Move(parse_square("g2"), parse_square("g4"), MoveFlag.DOUBLE_PAWN)
        )
        ctrl.submit_move(Move(parse_square("d8"), parse_square("h4")))
        assert results == [GameResult.BLACK_WINS]


class TestResignDraw:
    def test_resign(self) -> None:
        ctrl = _make_hh_controller()
        ctrl.resign(Color.WHITE)
        assert ctrl.state.result == GameResult.BLACK_WINS
        assert ctrl.state.is_game_over

    def test_draw_offer_accept(self) -> None:
        ctrl = _make_hh_controller()
        ctrl.offer_draw(Color.WHITE)
        assert ctrl.state.draw_offer == DrawOffer.OFFERED
        ctrl.accept_draw(Color.BLACK)
        assert ctrl.state.result == GameResult.DRAW

    def test_cannot_accept_own_draw_offer(self) -> None:
        ctrl = _make_hh_controller()
        ctrl.offer_draw(Color.WHITE)
        ctrl.accept_draw(Color.WHITE)
        assert ctrl.state.result == GameResult.IN_PROGRESS
        assert ctrl.state.draw_offer == DrawOffer.OFFERED

    def test_draw_offer_decline(self) -> None:
        ctrl = _make_hh_controller()
        ctrl.offer_draw(Color.WHITE)
        ctrl.decline_draw()
        assert ctrl.state.draw_offer == DrawOffer.DECLINED
        assert not ctrl.state.is_game_over

    def test_cannot_submit_after_game_over(self) -> None:
        ctrl = _make_hh_controller()
        ctrl.resign(Color.WHITE)
        ok = ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert not ok


class TestUndoMove:
    def test_undo_reverts(self) -> None:
        ctrl = _make_hh_controller()
        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        ok = ctrl.undo_move()
        assert ok
        assert ctrl.state.side_to_move == Color.WHITE
        assert ctrl.state.ply_count == 0

    def test_undo_empty_fails(self) -> None:
        ctrl = _make_hh_controller()
        assert not ctrl.undo_move()


class TestWithClock:
    def test_clock_created(self) -> None:
        ctrl = _make_hh_controller(TimeControl.blitz_5m())
        assert ctrl.clock is not None
        assert ctrl.clock.remaining(Color.WHITE) == pytest.approx(300.0, abs=1.0)

    def test_no_clock_by_default(self) -> None:
        ctrl = _make_hh_controller()
        assert ctrl.clock is None

    def test_move_does_not_consume_extra_time_after_submit(self) -> None:
        ctrl = _make_hh_controller(TimeControl(60, 0))
        clock = ctrl.clock
        assert clock is not None

        # Keep callback intentionally slow to detect accidental double-consume.
        ctrl.events.on_move.append(lambda _m, _san, _st: time.sleep(0.25))
        time.sleep(0.05)
        before = clock.remaining(Color.WHITE)
        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        after = clock.remaining(Color.WHITE)

        assert before - after < 0.12

    def test_undo_restores_clock_snapshot(self) -> None:
        ctrl = _make_hh_controller(TimeControl(60, 0))
        clock = ctrl.clock
        assert clock is not None

        time.sleep(0.05)
        white_before = clock.remaining(Color.WHITE)
        black_before = clock.remaining(Color.BLACK)

        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        time.sleep(0.05)  # Black clock runs before undo.
        assert ctrl.undo_move()

        assert ctrl.state.side_to_move == Color.WHITE
        assert clock.active_color == Color.WHITE
        assert clock.is_running
        assert clock.remaining(Color.WHITE) == pytest.approx(white_before, abs=0.12)
        assert clock.remaining(Color.BLACK) == pytest.approx(black_before, abs=0.12)


class TestAIIntegration:
    def test_ai_request_move_called(self) -> None:
        called = []
        ai = AIPlayer(
            Color.BLACK,
            on_request_move=lambda pos: called.append(True),
        )
        ctrl = GameController()
        ctrl.new_game(HumanPlayer(Color.WHITE), ai)

        # White plays e4 → controller should call ai.request_move
        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert called == [True]
        assert ctrl.state.phase == GamePhase.THINKING

    def test_ai_responds(self) -> None:
        """Simulate AI responding with d5."""
        ai = AIPlayer(Color.BLACK)
        ctrl = GameController()
        ctrl.new_game(HumanPlayer(Color.WHITE), ai)
        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        # Simulate AI callback (engine worker would emit this)
        ok = ctrl.submit_move(Move(D7, D5, MoveFlag.DOUBLE_PAWN))
        assert ok
        assert ctrl.state.side_to_move == Color.WHITE
