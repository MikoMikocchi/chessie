"""Tests for game analysis service."""

from __future__ import annotations

import pytest

from chessie.analysis import AnalysisCancelled, GameAnalyzer, MoveJudgment
from chessie.core.move import Move
from chessie.core.types import parse_square
from chessie.engine.search import SearchLimits, SearchResult
from chessie.game.state import GameState, MoveRecord


class _StubEngine:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = list(results)
        self.seen_limits: list[SearchLimits] = []

    def search(
        self,
        _position: object,
        _limits: SearchLimits,
        _is_cancelled: object | None = None,
    ) -> SearchResult:
        self.seen_limits.append(_limits)
        if not self._results:
            raise AssertionError("No more stubbed engine results")
        return self._results.pop(0)


def _sample_history() -> tuple[str, list[MoveRecord]]:
    state = GameState()
    state.setup()
    state.apply_move(Move(parse_square("e2"), parse_square("e4")))
    state.apply_move(Move(parse_square("e7"), parse_square("e5")))
    return state.start_fen, state.move_history


def test_analyze_game_builds_move_metrics_and_side_summaries() -> None:
    start_fen, history = _sample_history()
    engine = _StubEngine(
        [
            SearchResult(Move(parse_square("d2"), parse_square("d4")), 40, 4, 1_000),
            SearchResult(Move(parse_square("c7"), parse_square("c5")), 40, 4, 1_000),
            SearchResult(None, 0, 4, 1_100),
        ]
    )
    analyzer = GameAnalyzer(engine=engine)
    progress: list[tuple[int, int]] = []

    report = analyzer.analyze_game(
        start_fen=start_fen,
        move_history=history,
        limits=SearchLimits(max_depth=4, time_limit_ms=None),
        on_progress=lambda done, total: progress.append((done, total)),
    )

    assert report.total_plies == 2
    assert len(report.moves) == 2
    assert progress == [(1, 2), (2, 2)]

    first = report.moves[0]
    assert first.played_san == "e4"
    assert first.best_san == "d4"
    assert first.cp_loss == 80
    assert first.judgment == MoveJudgment.INACCURACY

    second = report.moves[1]
    assert second.played_san == "e5"
    assert second.best_san == "c5"
    assert second.cp_loss == 40
    assert second.judgment == MoveJudgment.GOOD

    assert report.white.moves == 1
    assert report.white.avg_cp_loss == pytest.approx(80.0)
    assert report.white.inaccuracies == 1
    assert report.black.moves == 1
    assert report.black.avg_cp_loss == pytest.approx(40.0)
    assert report.critical_plies == (0, 1)


def test_analyze_game_honors_cancel_callback() -> None:
    start_fen, history = _sample_history()
    analyzer = GameAnalyzer(engine=_StubEngine([]))

    with pytest.raises(AnalysisCancelled):
        analyzer.analyze_game(
            start_fen=start_fen,
            move_history=history,
            limits=SearchLimits(max_depth=2, time_limit_ms=None),
            is_cancelled=lambda: True,
        )


def test_analyze_game_scales_time_limit_per_position() -> None:
    start_fen, history = _sample_history()
    engine = _StubEngine(
        [
            SearchResult(Move(parse_square("d2"), parse_square("d4")), 10, 4, 100),
            SearchResult(Move(parse_square("c7"), parse_square("c5")), 8, 4, 100),
            SearchResult(None, 6, 4, 100),
        ]
    )
    analyzer = GameAnalyzer(engine=engine)

    _ = analyzer.analyze_game(
        start_fen=start_fen,
        move_history=history,
        limits=SearchLimits(max_depth=4, time_limit_ms=200),
    )

    assert [limits.max_depth for limits in engine.seen_limits] == [4, 4, 4]
    assert [limits.time_limit_ms for limits in engine.seen_limits] == [160, 130, 130]
