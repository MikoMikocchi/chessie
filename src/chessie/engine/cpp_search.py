"""C++ engine wrapper implementing the ``IEngine`` protocol.

Communication with the native library uses FEN strings (position) and
UCI strings (moves), keeping the coupling between Python and C++ types
to an absolute minimum.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from chessie.core.enums import MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.notation import position_to_fen
from chessie.engine.search import CancelCheck, IEngine, SearchLimits, SearchResult

if TYPE_CHECKING:
    from chessie.core.position import Position

try:
    import _chessie_engine
except ImportError:
    try:
        from chessie import _chessie_engine  # type: ignore[attr-defined]
    except ImportError:
        _chessie_engine = None

_PROMO_MAP: dict[str, PieceType] = {
    "n": PieceType.KNIGHT,
    "b": PieceType.BISHOP,
    "r": PieceType.ROOK,
    "q": PieceType.QUEEN,
}


def _uci_to_move(uci: str, position: Position) -> Move | None:
    """Convert a UCI move string to a Python :class:`Move`.

    Uses the position's legal move list to find the exact move object
    (with the correct :class:`MoveFlag`) matching the UCI string.
    """
    if not uci:
        return None

    from_sq = _parse_sq(uci[0:2])
    to_sq = _parse_sq(uci[2:4])
    promo: PieceType | None = _PROMO_MAP.get(uci[4]) if len(uci) >= 5 else None

    for move in MoveGenerator(position).generate_legal_moves():
        if move.from_sq == from_sq and move.to_sq == to_sq and move.promotion == promo:
            return move

    # Fallback: construct a plain move (should only happen if movegen
    # differs between Python and C++, which should not occur).
    flag = MoveFlag.PROMOTION if promo is not None else MoveFlag.NORMAL
    return Move(from_sq, to_sq, flag, promo)


def _parse_sq(name: str) -> int:
    """Parse a square name like 'e4' to index 0-63."""
    return (ord(name[0]) - ord("a")) + (int(name[1]) - 1) * 8


def is_available() -> bool:
    """Return *True* if the native C++ engine is importable."""
    return _chessie_engine is not None


class CppSearchEngine(IEngine):
    """Chess engine backed by the native C++ search.

    Implements the :class:`IEngine` protocol so it can be used as a
    drop-in replacement for :class:`PythonSearchEngine`.
    """

    __slots__ = ("_engine",)

    def __init__(self, *, tt_mb: int = 64) -> None:
        if _chessie_engine is None:
            msg = (
                "Native C++ engine module (_chessie_engine) is not available. "
                "Build it with BUILD_PYBIND=ON or fall back to PythonSearchEngine."
            )
            raise ImportError(msg)
        self._engine: _chessie_engine.Engine = _chessie_engine.Engine(tt_mb)

    # ── IEngine protocol ─────────────────────────────────────────────────

    def search(
        self,
        position: Position,
        limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
    ) -> SearchResult:
        """Search the given *position* and return the best move.

        The *is_cancelled* callback is checked before the search starts.
        During the search, cancellation is handled via :meth:`cancel` from
        another thread (the C++ engine releases the GIL).
        """
        if is_cancelled is not None and is_cancelled():
            return SearchResult(best_move=None, score_cp=0, depth=0, nodes=0)

        fen = position_to_fen(position)
        time_ms = limits.time_limit_ms if limits.time_limit_ms is not None else -1

        uci_move, score_cp, depth, nodes = self._engine.search(
            fen,
            limits.max_depth,
            time_ms,
        )

        best_move = _uci_to_move(uci_move, position)

        return SearchResult(
            best_move=best_move,
            score_cp=score_cp,
            depth=depth,
            nodes=nodes,
        )

    # ── Extra controls ───────────────────────────────────────────────────

    def cancel(self) -> None:
        """Cancel a running search (thread-safe)."""
        self._engine.cancel()

    def set_tt_size(self, mb: int) -> None:
        """Resize the transposition table (clears it)."""
        self._engine.set_tt_size(mb)

    def clear_tt(self) -> None:
        """Clear the transposition table."""
        self._engine.clear_tt()
