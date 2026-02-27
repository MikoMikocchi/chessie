"""Background game analysis orchestration for the UI thread."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from chessie.analysis import AnalysisCancelled, GameAnalysisReport, GameAnalyzer
from chessie.engine import SearchLimits

if TYPE_CHECKING:
    from chessie.game.state import MoveRecord


class _AnalysisCommandBus(QObject):
    analyze_requested = pyqtSignal(int, str, object, int, int)
    cancel_requested = pyqtSignal()


class _AnalysisWorker(QObject):
    progress = pyqtSignal(int, int, int)  # request_id, done, total
    finished = pyqtSignal(int, object)  # request_id, report
    cancelled = pyqtSignal(int)  # request_id
    failed = pyqtSignal(int, str)  # request_id, message

    __slots__ = ("_analyzer", "_cancel_event")

    def __init__(self) -> None:
        super().__init__()
        self._analyzer = GameAnalyzer()
        self._cancel_event = threading.Event()

    @pyqtSlot(int, str, object, int, int)
    def analyze(
        self,
        request_id: int,
        start_fen: str,
        move_history_obj: object,
        max_depth: int,
        time_limit_ms: int,
    ) -> None:
        if not isinstance(start_fen, str):
            self.failed.emit(request_id, "Invalid start FEN for analysis")
            return
        if not isinstance(move_history_obj, list):
            self.failed.emit(request_id, "Invalid move history for analysis")
            return
        if max_depth <= 0:
            self.failed.emit(request_id, "Analysis depth must be >= 1")
            return

        self._cancel_event.clear()
        limits = SearchLimits(max_depth=max_depth, time_limit_ms=time_limit_ms)

        try:
            report = self._analyzer.analyze_game(
                start_fen=start_fen,
                move_history=move_history_obj,
                limits=limits,
                is_cancelled=self._cancel_event.is_set,
                on_progress=lambda done, total: self.progress.emit(
                    request_id,
                    done,
                    total,
                ),
            )
        except AnalysisCancelled:
            self.cancelled.emit(request_id)
            return
        except Exception as exc:
            self.failed.emit(request_id, str(exc))
            return

        if self._cancel_event.is_set():
            self.cancelled.emit(request_id)
            return
        self.finished.emit(request_id, report)

    @pyqtSlot()
    def cancel(self) -> None:
        self._cancel_event.set()


class AnalysisSession:
    """Owns worker-thread lifecycle for game analysis requests."""

    __slots__ = (
        "__weakref__",
        "_on_progress",
        "_on_finished",
        "_on_failed",
        "_on_cancelled",
        "_command_bus",
        "_thread",
        "_worker",
        "_is_started",
        "_is_shutting_down",
        "_pending_request_id",
        "_next_request_id",
    )

    def __init__(
        self,
        *,
        on_progress: Callable[[int, int], None],
        on_finished: Callable[[GameAnalysisReport], None],
        on_failed: Callable[[str], None],
        on_cancelled: Callable[[], None],
        parent: QObject | None = None,
    ) -> None:
        self._on_progress = on_progress
        self._on_finished = on_finished
        self._on_failed = on_failed
        self._on_cancelled = on_cancelled

        self._command_bus = _AnalysisCommandBus(parent)
        self._thread = QThread(parent)
        self._worker = _AnalysisWorker()
        self._is_started = False
        self._is_shutting_down = False
        self._pending_request_id: int | None = None
        self._next_request_id = 0

    def setup(self) -> None:
        """Start worker thread and connect cross-thread signals."""
        if self._is_started:
            return
        self._is_shutting_down = False
        self._worker.moveToThread(self._thread)
        self._command_bus.analyze_requested.connect(self._worker.analyze)
        self._command_bus.cancel_requested.connect(self._worker.cancel)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.cancelled.connect(self._on_worker_cancelled)
        self._thread.start()
        self._is_started = True

    def shutdown(self) -> None:
        """Cancel active work and stop worker thread."""
        if not self._is_started:
            return
        self._is_shutting_down = True
        self.cancel_analysis()
        self._thread.quit()
        self._thread.wait(2000)
        self._is_started = False

    def start_analysis(
        self,
        *,
        start_fen: str,
        move_history: list[MoveRecord],
        max_depth: int,
        time_limit_ms: int,
    ) -> bool:
        """Start (or restart) a background game analysis."""
        if not move_history:
            return False
        if not self._is_started:
            self.setup()
        if self._is_shutting_down:
            return False

        self.cancel_analysis()
        self._next_request_id += 1
        request_id = self._next_request_id
        self._pending_request_id = request_id
        self._command_bus.analyze_requested.emit(
            request_id,
            start_fen,
            list(move_history),
            max_depth,
            time_limit_ms,
        )
        return True

    def cancel_analysis(self) -> None:
        """Cancel any active analysis request."""
        self._pending_request_id = None
        if self._is_started:
            self._command_bus.cancel_requested.emit()

    def _on_worker_progress(self, request_id: int, done: int, total: int) -> None:
        if request_id != self._pending_request_id:
            return
        self._on_progress(done, total)

    def _on_worker_finished(self, request_id: int, report_obj: object) -> None:
        if self._is_shutting_down:
            return
        if request_id != self._pending_request_id:
            return
        if not isinstance(report_obj, GameAnalysisReport):
            self._pending_request_id = None
            self._on_failed("Analysis worker produced invalid report")
            return
        self._pending_request_id = None
        self._on_finished(report_obj)

    def _on_worker_failed(self, request_id: int, message: str) -> None:
        if self._is_shutting_down:
            return
        if request_id != self._pending_request_id:
            return
        self._pending_request_id = None
        self._on_failed(message)

    def _on_worker_cancelled(self, request_id: int) -> None:
        if self._is_shutting_down:
            return
        if request_id != self._pending_request_id:
            return
        self._pending_request_id = None
        self._on_cancelled()
