"""Tests for Qt engine bridge worker."""

from __future__ import annotations

from PyQt6.QtTest import QSignalSpy

from chessie.core.move_generator import MoveGenerator
from chessie.core.notation import STARTING_FEN, position_from_fen
from chessie.core.position import Position
from chessie.engine.qt_bridge import EngineWorker
from chessie.engine.search import CancelCheck, SearchLimits, SearchResult


class _CancellingEngine:
    def __init__(self, worker: EngineWorker) -> None:
        self._worker = worker

    def search(
        self,
        position: Position,
        _limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
    ) -> SearchResult:
        del is_cancelled
        legal = MoveGenerator(position).generate_legal_moves()
        self._worker.cancel()
        return SearchResult(
            best_move=legal[0],
            score_cp=0,
            depth=1,
            nodes=1,
        )


class TestEngineWorker:
    def test_emits_cancelled_when_search_is_cancelled(self) -> None:
        position = position_from_fen(STARTING_FEN)
        worker = EngineWorker()
        worker._engine = _CancellingEngine(worker)  # type: ignore[assignment]

        cancelled = QSignalSpy(worker.search_cancelled)
        best_moves = QSignalSpy(worker.best_move_ready)

        worker.request_move(position, 7)

        assert len(cancelled) == 1
        assert cancelled[0][0] == 7
        assert len(best_moves) == 0
