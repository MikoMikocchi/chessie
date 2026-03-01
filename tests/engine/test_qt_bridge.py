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


class _NoMoveEngine:
    def search(
        self,
        _position: Position,
        _limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
    ) -> SearchResult:
        del is_cancelled
        return SearchResult(
            best_move=None,
            score_cp=-100_000,
            depth=0,
            nodes=0,
        )


class TestEngineWorker:
    def test_emits_cancelled_when_search_is_cancelled(self) -> None:
        position = position_from_fen(STARTING_FEN)
        worker = EngineWorker()
        worker._engine = _CancellingEngine(worker)

        cancelled = QSignalSpy(worker.search_cancelled)
        best_moves = QSignalSpy(worker.best_move_ready)

        worker.request_move(position, 7)

        assert len(cancelled) == 1
        assert cancelled[0][0] == 7
        assert len(best_moves) == 0

    def test_emits_no_move_when_search_returns_none(self) -> None:
        position = position_from_fen(STARTING_FEN)
        worker = EngineWorker()
        worker._engine = _NoMoveEngine()

        no_move = QSignalSpy(worker.search_no_move)
        best_moves = QSignalSpy(worker.best_move_ready)
        errors = QSignalSpy(worker.search_error)

        worker.request_move(position, 11)

        assert len(no_move) == 1
        assert no_move[0][0] == 11
        assert len(best_moves) == 0
        assert len(errors) == 0
