"""Regression tests for EngineSession wiring."""

from __future__ import annotations

import weakref
from collections.abc import Callable

from chessie.game.controller import GameController
from chessie.ui.engine_session import EngineSession


class _StubEngineRequest:
    def connect(self, _slot: Callable[..., object]) -> object:
        return object()

    def emit(self, _position_obj: object, _request_id: int) -> object:
        return object()


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
