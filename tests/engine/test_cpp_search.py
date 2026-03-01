"""Tests for the C++ engine wrapper (``CppSearchEngine``).

Mirrors the key behavioural tests from ``test_search.py`` but exercises
the native C++ search through the pybind11 bridge.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pytest

from chessie.core.enums import MoveFlag, PieceType
from chessie.core.move_generator import MoveGenerator
from chessie.core.notation import STARTING_FEN, position_from_fen
from chessie.core.rules import Rules
from chessie.core.types import parse_square
from chessie.engine.search import SearchLimits, SearchResult

if TYPE_CHECKING:
    pass

# Skip the entire module when the native extension is not available.
pytest.importorskip(
    "chessie.engine.cpp_search",
    reason="C++ engine not built (BUILD_PYBIND=ON required)",
)
from chessie.engine.cpp_search import CppSearchEngine, is_available

# ── Helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def engine() -> CppSearchEngine:
    return CppSearchEngine(tt_mb=1)


NO_TIME_LIMIT = SearchLimits(max_depth=3, time_limit_ms=None)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestCppSearchEngine:
    """Behavioural tests for the native C++ engine wrapper."""

    # ── availability ─────────────────────────────────────────────────────

    def test_is_available(self) -> None:
        assert is_available()

    # ── basic search ─────────────────────────────────────────────────────

    def test_returns_legal_move_from_start(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(pos, SearchLimits(max_depth=2, time_limit_ms=None))
        legal = MoveGenerator(pos).generate_legal_moves()

        assert result.best_move in legal
        assert result.depth >= 1
        assert result.nodes > 0

    def test_depth_one_returns_move(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(pos, SearchLimits(max_depth=1, time_limit_ms=None))
        assert result.best_move is not None
        assert result.depth == 1

    def test_depth_four_returns_move(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(pos, SearchLimits(max_depth=4, time_limit_ms=None))
        assert result.best_move is not None
        assert result.depth == 4
        assert result.nodes > 100

    # ── mate detection ───────────────────────────────────────────────────

    def test_finds_mate_in_one(self, engine: CppSearchEngine) -> None:
        # Kg6, Qh7 vs Kg8.  Qh8# is mate in 1.
        pos = position_from_fen("6k1/7Q/6K1/8/8/8/8/8 w - - 0 1")
        result = engine.search(pos, SearchLimits(max_depth=3, time_limit_ms=None))
        assert result.best_move is not None
        assert result.score_cp > 90_000

        # Verify the move is actually checkmate.
        pos.make_move(result.best_move)
        assert Rules.is_checkmate(pos)

    def test_returns_none_for_checkmated_side(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen("3k4/3Q4/3K4/8/8/8/8/8 b - - 0 1")
        result = engine.search(pos, SearchLimits(max_depth=1, time_limit_ms=None))
        assert result.best_move is None
        assert result.score_cp <= -90_000

    def test_returns_none_for_stalemate(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen("k7/2Q5/1K6/8/8/8/8/8 b - - 0 1")
        result = engine.search(pos, SearchLimits(max_depth=1, time_limit_ms=None))
        assert result.best_move is None
        assert result.score_cp == 0

    # ── tactical positions ───────────────────────────────────────────────

    def test_captures_hanging_queen(self, engine: CppSearchEngine) -> None:
        # Black queen can capture undefended white queen.
        pos = position_from_fen("3q4/8/8/3Q4/8/8/8/4K2k b - - 0 1")
        result = engine.search(pos, NO_TIME_LIMIT)
        assert result.best_move is not None
        assert result.best_move.from_sq == parse_square("d8")
        assert result.best_move.to_sq == parse_square("d5")

    def test_finds_back_rank_mate(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen("7k/5ppp/8/8/8/8/8/R3K3 w - - 0 1")
        result = engine.search(pos, NO_TIME_LIMIT)
        assert result.best_move is not None
        assert str(result.best_move) == "a1a8"
        assert result.score_cp > 90_000

    # ── promotion ────────────────────────────────────────────────────────

    def test_finds_promotion(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen("7k/4P3/8/8/8/8/8/4K3 w - - 0 1")
        result = engine.search(pos, NO_TIME_LIMIT)
        assert result.best_move is not None
        assert result.best_move.from_sq == parse_square("e7")
        assert result.best_move.to_sq == parse_square("e8")
        assert result.best_move.flag == MoveFlag.PROMOTION
        assert result.best_move.promotion == PieceType.QUEEN

    # ── draw detection ───────────────────────────────────────────────────

    def test_draw_k_vs_k(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        result = engine.search(pos, NO_TIME_LIMIT)
        assert result.score_cp == 0

    def test_draw_50_move_rule(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen("4k3/8/8/8/4K3/8/8/R7 w - - 100 50")
        result = engine.search(pos, SearchLimits(max_depth=2, time_limit_ms=None))
        assert result.score_cp == 0

    # ── score sanity ─────────────────────────────────────────────────────

    def test_starting_position_roughly_equal(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(pos, NO_TIME_LIMIT)
        assert -200 < result.score_cp < 200

    # ── cancellation ─────────────────────────────────────────────────────

    def test_honors_cancel_callback(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(
            pos,
            SearchLimits(max_depth=6, time_limit_ms=None),
            is_cancelled=lambda: True,
        )
        # Pre-cancelled: should return immediately.
        assert result.nodes == 0
        assert result.depth == 0

    def test_cancel_via_thread(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        limits = SearchLimits(max_depth=64, time_limit_ms=None)

        result_holder: list[SearchResult] = []

        def run_search() -> None:
            result_holder.append(engine.search(pos, limits))

        t = threading.Thread(target=run_search)
        t.start()

        # Give the search a moment to start, then cancel.
        import time

        time.sleep(0.05)
        engine.cancel()
        t.join(timeout=5)

        assert not t.is_alive(), "Search thread did not finish in time"
        assert len(result_holder) == 1
        assert result_holder[0].depth < 20

    def test_time_limit(self, engine: CppSearchEngine) -> None:
        pos = position_from_fen(STARTING_FEN)
        import time

        start = time.monotonic()
        result = engine.search(pos, SearchLimits(max_depth=64, time_limit_ms=100))
        elapsed = time.monotonic() - start

        assert result.best_move is not None
        assert result.depth > 0
        assert elapsed < 2.0

    # ── engine controls ──────────────────────────────────────────────────

    def test_set_tt_size(self, engine: CppSearchEngine) -> None:
        engine.set_tt_size(2)
        engine.clear_tt()
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(pos, SearchLimits(max_depth=2, time_limit_ms=None))
        assert result.best_move is not None

    # ── move object consistency ──────────────────────────────────────────

    def test_move_has_correct_flag(self, engine: CppSearchEngine) -> None:
        """Returned Move objects should have the correct MoveFlag, not just NORMAL."""
        pos = position_from_fen(STARTING_FEN)
        result = engine.search(pos, SearchLimits(max_depth=3, time_limit_ms=None))
        assert result.best_move is not None
        # The move should be a valid Move with a proper flag.
        legal = MoveGenerator(pos).generate_legal_moves()
        assert result.best_move in legal

    # ── Python/C++ parity ────────────────────────────────────────────────

    def test_agrees_with_python_on_mate(self) -> None:
        """Both engines must find checkmate in the same position."""
        from chessie.engine import PythonSearchEngine

        pos_fen = "6k1/7Q/6K1/8/8/8/8/8 w - - 0 1"
        limits = SearchLimits(max_depth=3, time_limit_ms=None)

        py_result = PythonSearchEngine().search(position_from_fen(pos_fen), limits)
        cpp_result = CppSearchEngine(tt_mb=1).search(position_from_fen(pos_fen), limits)

        # Both must find it.
        assert py_result.best_move is not None
        assert cpp_result.best_move is not None
        assert py_result.score_cp > 90_000
        assert cpp_result.score_cp > 90_000
