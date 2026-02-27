"""Regression tests for EngineSession wiring."""

from __future__ import annotations

import weakref
from collections.abc import Callable
from types import SimpleNamespace

from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.notation import STARTING_FEN, position_from_fen, position_to_fen
from chessie.core.types import E2, E4
from chessie.game.controller import GameController
from chessie.game.interfaces import GamePhase
from chessie.ui.engine_session import EngineSession


class _StubEngineRequest:
    def __init__(self) -> None:
        self.emitted: list[tuple[object, int]] = []

    def connect(self, _slot: Callable[..., object]) -> object:
        return object()

    def emit(self, position_obj: object, request_id: int) -> object:
        self.emitted.append((position_obj, request_id))
        return object()


class _StubController:
    def __init__(self) -> None:
        self.state = SimpleNamespace(
            phase=GamePhase.THINKING,
            side_to_move=Color.BLACK,
            position=position_from_fen(STARTING_FEN),
        )
        self.resigned: list[Color] = []

    def resign(self, color: Color) -> None:
        self.resigned.append(color)

    def submit_move(self, _move: object) -> bool:
        return True


class TestEngineSession:
    def test_shutdown_before_setup_is_noop(self) -> None:
        session = EngineSession(
            controller=GameController(),
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        session.shutdown()
        assert session._is_started is False

    def test_setup_twice_keeps_started_state(self) -> None:
        session = EngineSession(
            controller=GameController(),
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        session.setup()
        session.setup()
        assert session._is_started is True
        session.shutdown()

    def test_setup_connects_slots_without_weakref_error(self) -> None:
        session = EngineSession(
            controller=GameController(),
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        assert weakref.ref(session)() is session

        session.setup()
        session.shutdown()

    def test_engine_error_retries_once_before_resign(self) -> None:
        controller = _StubController()
        status: list[str] = []
        sync_calls: list[bool] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda text: status.append(text),
            sync_board_interactivity=lambda: sync_calls.append(True),
        )

        session._engine_request_id = 3
        session._pending_engine_request = 3
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)
        session._remaining_failure_retries = 1

        session._on_engine_error(3, "boom")

        assert session._pending_engine_request == 4
        assert session._remaining_failure_retries == 0
        assert controller.resigned == []
        assert status == []
        assert sync_calls == []

        session.cancel_ai_search()

    def test_engine_error_resigns_ai_after_retry_budget_exhausted(self) -> None:
        controller = _StubController()
        status: list[str] = []
        sync_calls: list[bool] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda text: status.append(text),
            sync_board_interactivity=lambda: sync_calls.append(True),
        )

        session._pending_engine_request = 9
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)
        session._remaining_failure_retries = 0

        session._on_engine_error(9, "boom")

        assert controller.resigned == [Color.BLACK]
        assert status and "boom" in status[-1]
        assert sync_calls == [True]
        assert session._pending_engine_request is None
        assert session._pending_engine_position is None
        assert session._pending_engine_fen is None

    def test_engine_no_move_uses_failure_policy(self) -> None:
        controller = _StubController()
        status: list[str] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda text: status.append(text),
            sync_board_interactivity=lambda: None,
        )

        session._pending_engine_request = 5
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)
        session._remaining_failure_retries = 0

        session._on_engine_no_move(5, 0, 0, 0)

        assert controller.resigned == [Color.BLACK]
        assert status and "no move" in status[-1].lower()

    def test_set_limits_before_setup_updates_worker_limits(self) -> None:
        session = EngineSession(
            controller=GameController(),
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )

        session.set_limits(6, 1500)

        assert session._engine_worker._limits.max_depth == 6
        assert session._engine_worker._limits.time_limit_ms == 1500

    def test_request_ai_move_queues_when_started(self) -> None:
        request = _StubEngineRequest()
        position = position_from_fen(STARTING_FEN)
        session = EngineSession(
            controller=GameController(),
            engine_request=request,
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        session._is_started = True

        session.request_ai_move(position)

        assert session._pending_engine_request == 1
        assert session._pending_engine_position is not None
        assert session._pending_engine_fen == position_to_fen(position)

    def test_emit_pending_request_sends_position_and_request_id(self) -> None:
        request = _StubEngineRequest()
        position = position_from_fen(STARTING_FEN)
        session = EngineSession(
            controller=GameController(),
            engine_request=request,
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        session._is_started = True
        session._pending_engine_request = 11
        session._pending_engine_position = position

        session._emit_pending_request()

        assert request.emitted == [(position, 11)]

    def test_best_move_applies_eval_with_side_to_move_sign(self) -> None:
        request = _StubEngineRequest()
        controller = _StubController()
        eval_values: list[float] = []
        sync_calls: list[bool] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=request,
            set_eval=eval_values.append,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: sync_calls.append(True),
        )

        session._pending_engine_request = 7
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)

        session._on_engine_best_move(7, Move(E2, E4), 120, 1, 1)

        assert eval_values == [-120.0]
        assert sync_calls == [True]
        assert session._pending_engine_request is None

    def test_engine_cancelled_matching_request_clears_pending(self) -> None:
        controller = _StubController()
        sync_calls: list[bool] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: sync_calls.append(True),
        )

        session._pending_engine_request = 13
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)
        session._on_engine_cancelled(13)

        assert sync_calls == [True]
        assert session._pending_engine_request is None
        assert session._pending_engine_position is None
        assert session._pending_engine_fen is None

    def test_request_ai_move_ignored_when_not_started_or_shutting_down(self) -> None:
        session = EngineSession(
            controller=GameController(),
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        session.request_ai_move(position_from_fen(STARTING_FEN))
        assert session._pending_engine_request is None

        session._is_started = True
        session._is_shutting_down = True
        session.request_ai_move(position_from_fen(STARTING_FEN))
        assert session._pending_engine_request is None

    def test_emit_pending_request_no_pending_is_noop(self) -> None:
        request = _StubEngineRequest()
        session = EngineSession(
            controller=GameController(),
            engine_request=request,
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        session._is_started = True
        session._emit_pending_request()
        assert request.emitted == []

    def test_on_engine_best_move_ignores_mismatched_request_and_type(self) -> None:
        controller = _StubController()
        eval_values: list[float] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=_StubEngineRequest(),
            set_eval=eval_values.append,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )

        session._pending_engine_request = 2
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)
        session._on_engine_best_move(1, Move(E2, E4), 12, 1, 1)
        session._on_engine_best_move(2, object(), 12, 1, 1)

        assert eval_values == []
        assert session._pending_engine_request == 2

    def test_on_engine_best_move_ignores_wrong_phase_or_fen(self) -> None:
        controller = _StubController()
        eval_values: list[float] = []
        session = EngineSession(
            controller=controller,  # type: ignore[arg-type]
            engine_request=_StubEngineRequest(),
            set_eval=eval_values.append,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )

        session._pending_engine_request = 3
        session._pending_engine_position = controller.state.position.copy()
        session._pending_engine_fen = position_to_fen(controller.state.position)

        controller.state.phase = GamePhase.AWAITING_MOVE
        session._on_engine_best_move(3, Move(E2, E4), 12, 1, 1)
        assert eval_values == []

        controller.state.phase = GamePhase.THINKING
        session._pending_engine_fen = "invalid-fen"
        session._on_engine_best_move(3, Move(E2, E4), 12, 1, 1)
        assert eval_values == []

    def test_set_limits_when_started_uses_signal_path(self) -> None:
        session = EngineSession(
            controller=GameController(),
            engine_request=_StubEngineRequest(),
            set_eval=lambda _cp: None,
            set_status=lambda _text: None,
            sync_board_interactivity=lambda: None,
        )
        captured: list[tuple[int, int]] = []
        session._command_bus.set_limits_requested.connect(
            lambda depth, ms: captured.append((depth, ms))
        )
        session._is_started = True

        session.set_limits(7, 2000)

        assert captured == [(7, 2000)]
