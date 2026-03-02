"""Compatibility tests for ``CppSearchEngine`` pybind result formats."""

from __future__ import annotations

import pytest

from chessie.core.enums import MoveFlag
from chessie.core.notation import STARTING_FEN, position_from_fen
from chessie.core.types import parse_square
from chessie.engine import cpp_search
from chessie.engine.search import SearchLimits


class _NativeNewTuple:
    class Engine:
        def __init__(self, _tt_mb: int) -> None:
            pass

        def search(
            self,
            _fen: str,
            _max_depth: int,
            _time_limit_ms: int,
        ) -> tuple[bool, int, int, int, int, int, int, int]:
            return (
                True,
                parse_square("e2"),
                parse_square("e4"),
                int(MoveFlag.DOUBLE_PAWN),
                0,
                17,
                2,
                123,
            )

        def cancel(self) -> None:
            pass

        def set_tt_size(self, _mb: int) -> None:
            pass

        def clear_tt(self) -> None:
            pass


class _NativeLegacyTuple:
    class Engine:
        def __init__(self, _tt_mb: int) -> None:
            pass

        def search(
            self,
            _fen: str,
            _max_depth: int,
            _time_limit_ms: int,
        ) -> tuple[str, int, int, int]:
            return ("e2e4", 23, 2, 99)

        def cancel(self) -> None:
            pass

        def set_tt_size(self, _mb: int) -> None:
            pass

        def clear_tt(self) -> None:
            pass


class _NativeBadTuple:
    class Engine:
        def __init__(self, _tt_mb: int) -> None:
            pass

        def search(
            self,
            _fen: str,
            _max_depth: int,
            _time_limit_ms: int,
        ) -> tuple[int, int, int]:
            return (1, 2, 3)

        def cancel(self) -> None:
            pass

        def set_tt_size(self, _mb: int) -> None:
            pass

        def clear_tt(self) -> None:
            pass


def test_search_accepts_new_native_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cpp_search, "_chessie_engine", _NativeNewTuple)
    engine = cpp_search.CppSearchEngine(tt_mb=1)

    result = engine.search(
        position_from_fen(STARTING_FEN),
        SearchLimits(max_depth=2, time_limit_ms=None),
    )

    assert result.best_move is not None
    assert result.best_move.from_sq == parse_square("e2")
    assert result.best_move.to_sq == parse_square("e4")
    assert result.best_move.flag == MoveFlag.DOUBLE_PAWN
    assert result.depth == 2
    assert result.nodes == 123


def test_search_accepts_legacy_native_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cpp_search, "_chessie_engine", _NativeLegacyTuple)
    engine = cpp_search.CppSearchEngine(tt_mb=1)

    result = engine.search(
        position_from_fen(STARTING_FEN),
        SearchLimits(max_depth=2, time_limit_ms=None),
    )

    assert result.best_move is not None
    assert result.best_move.from_sq == parse_square("e2")
    assert result.best_move.to_sq == parse_square("e4")
    assert result.best_move.flag == MoveFlag.DOUBLE_PAWN
    assert result.depth == 2
    assert result.nodes == 99


def test_search_raises_on_unknown_native_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cpp_search, "_chessie_engine", _NativeBadTuple)
    engine = cpp_search.CppSearchEngine(tt_mb=1)

    with pytest.raises(RuntimeError, match="Unsupported _chessie_engine.search result"):
        engine.search(
            position_from_fen(STARTING_FEN),
            SearchLimits(max_depth=2, time_limit_ms=None),
        )
