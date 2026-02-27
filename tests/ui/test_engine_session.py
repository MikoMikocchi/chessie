"""Regression tests for EngineSession wiring."""

from __future__ import annotations

import weakref
from collections.abc import Callable
from types import SimpleNamespace

from chessie.core.enums import Color
from chessie.core.notation import STARTING_FEN, position_from_fen, position_to_fen
from chessie.game.controller import GameController
from chessie.game.interfaces import GamePhase
from chessie.ui.engine_session import EngineSession


class _StubEngineRequest:
    def connect(self, _slot: Callable[..., object]) -> object:
        return object()

    def emit(self, _position_obj: object, _request_id: int) -> object:
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
