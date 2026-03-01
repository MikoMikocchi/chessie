"""Engine search session orchestration for the main UI thread."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

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


class _EngineCommandBus(QObject):
    """Signal bridge for issuing worker commands with queued delivery."""

    cancel_requested = pyqtSignal()
    set_limits_requested = pyqtSignal(int, int)


class EngineSession:
    """Owns worker-thread search lifecycle and move handoff to controller."""

    _REQUEST_DELAY_MS = 50
    _MOVE_APPLY_DELAY_MS = 200
    _MAX_FAILURE_RETRIES = 1

    __slots__ = (
        "__weakref__",
        "_controller",
        "_engine_request",
        "_set_eval",
        "_set_status",
        "_sync_board_interactivity",
        "_command_bus",
        "_dispatch_timer",
        "_move_apply_timer",
        "_pending_move",
        "_pending_move_white_cp",
        "_engine_thread",
        "_engine_worker",
        "_engine_request_id",
        "_pending_engine_request",
        "_pending_engine_position",
        "_pending_engine_fen",
        "_remaining_failure_retries",
        "_is_shutting_down",
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

        self._command_bus = _EngineCommandBus(parent)
        self._dispatch_timer = QTimer(parent)
        self._dispatch_timer.setSingleShot(True)
        self._dispatch_timer.timeout.connect(self._emit_pending_request)

        self._move_apply_timer = QTimer(parent)
        self._move_apply_timer.setSingleShot(True)
        self._move_apply_timer.timeout.connect(self._apply_delayed_move)
        self._pending_move: Move | None = None
        self._pending_move_white_cp = 0

        self._engine_thread = QThread(parent)
        self._engine_worker = EngineWorker(
            max_depth=max_depth, time_limit_ms=time_limit_ms
        )
        self._engine_request_id = 0
        self._pending_engine_request: int | None = None
        self._pending_engine_position: Position | None = None
        self._pending_engine_fen: str | None = None
        self._remaining_failure_retries = 0
        self._is_shutting_down = False
        self._is_started = False

    def setup(self) -> None:
        """Start engine worker in a dedicated thread and connect callbacks."""
        if self._is_started:
            return
        self._is_shutting_down = False
        self._engine_worker.moveToThread(self._engine_thread)
        self._engine_request.connect(self._engine_worker.request_move)
        self._command_bus.cancel_requested.connect(self._engine_worker.cancel)
        self._command_bus.set_limits_requested.connect(self._engine_worker.set_limits)
        self._engine_worker.best_move_ready.connect(self._on_engine_best_move)
        self._engine_worker.search_cancelled.connect(self._on_engine_cancelled)
        self._engine_worker.search_no_move.connect(self._on_engine_no_move)
        self._engine_worker.search_error.connect(self._on_engine_error)
        self._engine_thread.start()
        self._is_started = True

    def shutdown(self) -> None:
        """Stop active search and shut down the worker thread."""
        if not self._is_started:
            return
        self._is_shutting_down = True
        self.cancel_ai_search()
        self._dispatch_timer.stop()
        self._engine_thread.quit()
        self._engine_thread.wait(2000)
        self._clear_pending_request()
        self._is_started = False

    def set_limits(self, max_depth: int, time_limit_ms: int) -> None:
        """Update engine limits for subsequent searches."""
        if self._is_started:
            self._command_bus.set_limits_requested.emit(max_depth, time_limit_ms)
            return
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
        if not self._is_started or self._is_shutting_down:
            return
        self._queue_request(position.copy(), reset_retry_budget=True)

    def cancel_ai_search(self) -> None:
        """Cancel any pending/active engine request."""
        self._dispatch_timer.stop()
        self._move_apply_timer.stop()
        self._clear_pending_request()
        self._pending_move = None
        self._pending_move_white_cp = 0
        if self._is_started:
            self._command_bus.cancel_requested.emit()

    def _on_engine_best_move(
        self,
        request_id: int,
        move_obj: object,
        score_cp: int,
        _depth: int,
        _nodes: int,
    ) -> None:
        if self._is_shutting_down:
            return
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

        self._clear_pending_request()
        self._remaining_failure_retries = 0

        # Update eval immediately
        self._set_eval(float(white_cp))

        # Store the move and schedule it with a delay to allow animations to complete
        self._pending_move = move_obj
        self._pending_move_white_cp = white_cp
        self._sync_board_interactivity()
        self._move_apply_timer.start(self._MOVE_APPLY_DELAY_MS)

    def _on_engine_error(self, request_id: int, message: str) -> None:
        self._handle_engine_failure(request_id, message)

    def _apply_delayed_move(self) -> None:
        """Apply the pending move after animation delay."""
        if self._is_shutting_down or self._pending_move is None:
            return

        ok = self._controller.submit_move(self._pending_move)
        if ok:
            self._sync_board_interactivity()
        self._pending_move = None
        self._pending_move_white_cp = 0

    def _on_engine_no_move(
        self,
        request_id: int,
        _score_cp: int,
        _depth: int,
        _nodes: int,
    ) -> None:
        self._handle_engine_failure(request_id, "Engine produced no move")

    def _on_engine_cancelled(self, request_id: int) -> None:
        if self._is_shutting_down:
            return
        if request_id != self._pending_engine_request:
            return
        self._clear_pending_request()
        self._remaining_failure_retries = 0
        self._sync_board_interactivity()

    def _queue_request(self, position: Position, *, reset_retry_budget: bool) -> None:
        self.cancel_ai_search()
        if self._is_shutting_down:
            return

        self._engine_request_id += 1
        self._pending_engine_request = self._engine_request_id
        self._pending_engine_position = position
        self._pending_engine_fen = position_to_fen(position)
        if reset_retry_budget:
            self._remaining_failure_retries = self._MAX_FAILURE_RETRIES
        self._dispatch_timer.start(self._REQUEST_DELAY_MS)

    def _emit_pending_request(self) -> None:
        if self._is_shutting_down:
            return

        request_id = self._pending_engine_request
        position = self._pending_engine_position
        if request_id is None or position is None:
            return
        self._engine_request.emit(position, request_id)

    def _clear_pending_request(self) -> None:
        self._pending_engine_request = None
        self._pending_engine_position = None
        self._pending_engine_fen = None

    def _handle_engine_failure(self, request_id: int, message: str) -> None:
        if self._is_shutting_down:
            return
        if request_id != self._pending_engine_request:
            return

        state = self._controller.state
        if state.phase != GamePhase.THINKING:
            self._clear_pending_request()
            return

        if self._remaining_failure_retries > 0:
            self._remaining_failure_retries -= 1
            self._queue_request(state.position.copy(), reset_retry_budget=False)
            return

        self._clear_pending_request()
        self._set_status(t().status_engine_error.format(msg=message))
        self._controller.resign(state.side_to_move)
        self._sync_board_interactivity()
