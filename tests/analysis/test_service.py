"""Tests for game analysis service."""

from __future__ import annotations

import pytest

from chessie.analysis import (
    AnalysisCancelled,
    GameAnalyzer,
    MoveJudgment,
    compute_move_fingerprint,
)
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


def test_played_equals_best_gives_zero_cp_loss() -> None:
    """When the played move is the engine's best, cp_loss must be 0."""
    state = GameState()
    state.setup()
    # e2e4 will be the engine's best move too
    best_move = Move(parse_square("e2"), parse_square("e4"))
    state.apply_move(best_move)

    start_fen = state.start_fen
    history = state.move_history

    engine = _StubEngine(
        [
            # Before-search returns best_move = e2e4 with score 30
            SearchResult(best_move, 30, 4, 500),
            # After-search returns a different score (search noise)
            SearchResult(None, -100, 4, 500),
        ]
    )
    analyzer = GameAnalyzer(engine=engine)

    report = analyzer.analyze_game(
        start_fen=start_fen,
        move_history=history,
        limits=SearchLimits(max_depth=4, time_limit_ms=None),
    )

    assert report.moves[0].cp_loss == 0
    assert report.moves[0].judgment == MoveJudgment.BEST


def test_mate_scores_are_capped() -> None:
    """Mate-scale evaluations should be capped so ACPL stays bounded."""
    state = GameState()
    state.setup()
    state.apply_move(Move(parse_square("e2"), parse_square("e4")))

    start_fen = state.start_fen
    history = state.move_history

    engine = _StubEngine(
        [
            # Before-search: huge mate score
            SearchResult(Move(parse_square("d2"), parse_square("d4")), 99999, 6, 1000),
            # After-search: large negative
            SearchResult(None, -99999, 6, 1000),
        ]
    )
    analyzer = GameAnalyzer(engine=engine)

    report = analyzer.analyze_game(
        start_fen=start_fen,
        move_history=history,
        limits=SearchLimits(max_depth=6, time_limit_ms=None),
    )

    # cp_loss should be bounded (capped at 2*1500 = 3000 max)
    assert report.moves[0].cp_loss <= 3000
    assert report.white.avg_cp_loss <= 3000


def test_zero_cp_loss_classified_as_best() -> None:
    """cp_loss == 0 should be BEST (not GREAT as before)."""
    from chessie.analysis.service import _classify_cp_loss

    assert _classify_cp_loss(0) == MoveJudgment.BEST


def test_classify_cp_loss_order() -> None:
    """Verify the classification boundaries produce expected judgments."""
    from chessie.analysis.service import _classify_cp_loss

    assert _classify_cp_loss(0) == MoveJudgment.BEST
    assert _classify_cp_loss(5) == MoveJudgment.BEST
    assert _classify_cp_loss(10) == MoveJudgment.BEST
    assert _classify_cp_loss(11) == MoveJudgment.GREAT
    assert _classify_cp_loss(20) == MoveJudgment.GREAT
    assert _classify_cp_loss(21) == MoveJudgment.GOOD
    assert _classify_cp_loss(60) == MoveJudgment.GOOD
    assert _classify_cp_loss(61) == MoveJudgment.INACCURACY
    assert _classify_cp_loss(120) == MoveJudgment.INACCURACY
    assert _classify_cp_loss(121) == MoveJudgment.MISTAKE
    assert _classify_cp_loss(250) == MoveJudgment.MISTAKE
    assert _classify_cp_loss(251) == MoveJudgment.BLUNDER


def test_move_fingerprint_changes_with_different_moves() -> None:
    """Different move sequences must produce different fingerprints."""
    state1 = GameState()
    state1.setup()
    state1.apply_move(Move(parse_square("e2"), parse_square("e4")))

    state2 = GameState()
    state2.setup()
    state2.apply_move(Move(parse_square("d2"), parse_square("d4")))

    fp1 = compute_move_fingerprint(state1.start_fen, state1.move_history)
    fp2 = compute_move_fingerprint(state2.start_fen, state2.move_history)

    assert fp1 != fp2


def test_move_fingerprint_same_for_same_game() -> None:
    """Same game should produce the same fingerprint."""
    state = GameState()
    state.setup()
    state.apply_move(Move(parse_square("e2"), parse_square("e4")))

    fp1 = compute_move_fingerprint(state.start_fen, state.move_history)
    fp2 = compute_move_fingerprint(state.start_fen, state.move_history)

    assert fp1 == fp2


def test_report_includes_fingerprint() -> None:
    """The analysis report should include a non-empty move fingerprint."""
    start_fen, history = _sample_history()
    engine = _StubEngine(
        [
            SearchResult(Move(parse_square("d2"), parse_square("d4")), 40, 4, 1_000),
            SearchResult(Move(parse_square("c7"), parse_square("c5")), 40, 4, 1_000),
            SearchResult(None, 0, 4, 1_100),
        ]
    )
    analyzer = GameAnalyzer(engine=engine)

    report = analyzer.analyze_game(
        start_fen=start_fen,
        move_history=history,
        limits=SearchLimits(max_depth=4, time_limit_ms=None),
    )

    assert report.move_fingerprint
    expected = compute_move_fingerprint(start_fen, history)
    assert report.move_fingerprint == expected
