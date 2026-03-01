"""Qt bridge to run engine search in a worker thread."""

from __future__ import annotations

import threading

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from chessie.core.position import Position
from chessie.engine import DefaultEngine
from chessie.engine.search import SearchLimits


class EngineWorker(QObject):
    """Thread-affine worker that computes engine moves on demand."""

    best_move_ready = pyqtSignal(int, object, int, int, int)
    search_cancelled = pyqtSignal(int)
    search_no_move = pyqtSignal(int, int, int, int)
    search_error = pyqtSignal(int, str)

    __slots__ = ("_cancel_event", "_engine", "_limits")

    def __init__(
        self,
        *,
        max_depth: int = 3,
        time_limit_ms: int | None = 700,
    ) -> None:
        super().__init__()
        self._engine = DefaultEngine()
        self._limits = SearchLimits(max_depth=max_depth, time_limit_ms=time_limit_ms)
        self._cancel_event = threading.Event()

    @pyqtSlot(object, int)
    def request_move(self, position_obj: object, request_id: int) -> None:
        """Search for the best move in *position_obj* and emit result."""
        if not isinstance(position_obj, Position):
            self.search_error.emit(request_id, "Engine received invalid position")
            return

        self._cancel_event.clear()
        try:
            result = self._engine.search(
                position_obj,
                self._limits,
                is_cancelled=self._cancel_event.is_set,
            )
        except Exception as exc:
            self.search_error.emit(request_id, str(exc))
            return

        if self._cancel_event.is_set():
            self.search_cancelled.emit(request_id)
            return

        if result.best_move is None:
            self.search_no_move.emit(
                request_id,
                result.score_cp,
                result.depth,
                result.nodes,
            )
            return

        self.best_move_ready.emit(
            request_id,
            result.best_move,
            result.score_cp,
            result.depth,
            result.nodes,
        )

    @pyqtSlot()
    def cancel(self) -> None:
        """Request cancellation of the current search."""
        self._cancel_event.set()

    @pyqtSlot(int, int)
    def set_limits(self, max_depth: int, time_limit_ms: int) -> None:
        """Update search limits (takes effect on the next search)."""
        self._limits = SearchLimits(max_depth=max_depth, time_limit_ms=time_limit_ms)
