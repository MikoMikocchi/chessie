"""Engine search session orchestration for the main UI thread."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from PyQt6.QtCore import QObject, QThread, QTimer

from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.notation import position_to_fen
from chessie.engine.qt_bridge import EngineWorker
from chessie.game.controller import GameController
from chessie.game.interfaces import GamePhase
from chessie.game.player import AIPlayer
from chessie.ui.i18n import t

if TYPE_CHECKING:
    from chessie.core.position import Position


class EngineRequestSignal(Protocol):
    """Minimal signal interface used by :class:`EngineSession`."""

    def connect(self, slot: Callable[..., object]) -> object: ...

    def emit(self, position_obj: object, request_id: int) -> object: ...


class EngineSession:
    """Owns worker-thread search lifecycle and move handoff to controller."""

    __slots__ = (
        "__weakref__",
        "_controller",
        "_engine_request",
        "_set_eval",
        "_set_status",
        "_sync_board_interactivity",
        "_engine_thread",
        "_engine_worker",
        "_engine_request_id",
        "_pending_engine_request",
        "_pending_engine_fen",
        "_is_started",
    )

    def __init__(
        self,
        *,
        controller: GameController,
        engine_request: EngineRequestSignal,
        set_eval: Callable[[float], None],
        set_status: Callable[[str], None],
        sync_board_interactivity: Callable[[], None],
        parent: QObject | None = None,
        max_depth: int = 4,
        time_limit_ms: int = 900,
    ) -> None:
        self._controller = controller
        self._engine_request = engine_request
        self._set_eval = set_eval
        self._set_status = set_status
        self._sync_board_interactivity = sync_board_interactivity

        self._engine_thread = QThread(parent)
        self._engine_worker = EngineWorker(
            max_depth=max_depth, time_limit_ms=time_limit_ms
        )
        self._engine_request_id = 0
        self._pending_engine_request: int | None = None
        self._pending_engine_fen: str | None = None
        self._is_started = False

    def setup(self) -> None:
        """Start engine worker in a dedicated thread and connect callbacks."""
        if self._is_started:
            return
        self._engine_worker.moveToThread(self._engine_thread)
        self._engine_request.connect(self._engine_worker.request_move)
        self._engine_worker.best_move_ready.connect(self._on_engine_best_move)
        self._engine_worker.search_cancelled.connect(self._on_engine_cancelled)
        self._engine_worker.search_error.connect(self._on_engine_error)
        self._engine_thread.start()
        self._is_started = True

    def shutdown(self) -> None:
        """Stop active search and shut down the worker thread."""
        self.cancel_ai_search()
        self._engine_thread.quit()
        self._engine_thread.wait(2000)
        self._is_started = False

    def set_limits(self, max_depth: int, time_limit_ms: int) -> None:
        """Update engine limits for subsequent searches."""
        self._engine_worker.set_limits(max_depth, time_limit_ms)

    def create_ai_player(self, color: Color) -> AIPlayer:
        """Create an AI player wired to this session."""
        return AIPlayer(
            color,
            "Chessie AI",
            on_request_move=self.request_ai_move,
            on_cancel=self.cancel_ai_search,
        )

    def request_ai_move(self, position: Position) -> None:
        """Queue a best-move search for *position*."""
        self.cancel_ai_search()
        self._engine_request_id += 1
        request_id = self._engine_request_id

        self._pending_engine_request = request_id
        self._pending_engine_fen = position_to_fen(position)

        # Delay engine start slightly to allow UI repaint after user move.
        def _emit_if_valid() -> None:
            if self._pending_engine_request == request_id:
                self._engine_request.emit(position.copy(), request_id)

        QTimer.singleShot(50, _emit_if_valid)

    def cancel_ai_search(self) -> None:
        """Cancel any pending/active engine request."""
        self._pending_engine_request = None
        self._pending_engine_fen = None
        self._engine_worker.cancel()

    def _on_engine_best_move(
        self,
        request_id: int,
        move_obj: object,
        score_cp: int,
        _depth: int,
        _nodes: int,
    ) -> None:
        if request_id != self._pending_engine_request:
            return
        if not isinstance(move_obj, Move):
            return

        state = self._controller.state
        if state.phase != GamePhase.THINKING:
            return
        if self._pending_engine_fen != position_to_fen(state.position):
            return

        # Eval bar is white-centric; engine score is side-to-move-centric.
        white_cp = score_cp if state.side_to_move == Color.WHITE else -score_cp

        self._pending_engine_request = None
        self._pending_engine_fen = None
        ok = self._controller.submit_move(move_obj)
        if ok:
            self._set_eval(float(white_cp))
        self._sync_board_interactivity()

    def _on_engine_error(self, request_id: int, message: str) -> None:
        if request_id != self._pending_engine_request:
            return
        self._pending_engine_request = None
        self._pending_engine_fen = None

        state = self._controller.state
        if state.phase != GamePhase.THINKING:
            return

        legal = state.legal_moves()
        if legal:
            self._controller.submit_move(legal[0])
            return

        self._set_status(t().status_engine_error.format(msg=message))
        self._sync_board_interactivity()

    def _on_engine_cancelled(self, request_id: int) -> None:
        if request_id != self._pending_engine_request:
            return
        self._pending_engine_request = None
        self._pending_engine_fen = None
        self._sync_board_interactivity()
