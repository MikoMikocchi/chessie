"""C++ engine wrapper implementing the ``IEngine`` protocol.

Communication with the native library uses FEN strings and compact move
tuples to keep Python/C++ mapping simple and deterministic.
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


def _parse_sq(name: str) -> int:
    """Parse a square name like 'e4' to index 0-63."""
    return (ord(name[0]) - ord("a")) + (int(name[1]) - 1) * 8


def _legacy_uci_to_move(uci: str, position: Position) -> Move | None:
    """Decode legacy pybind ``search`` result where best move is a UCI string."""
    if len(uci) < 4:
        return None

    from_sq = _parse_sq(uci[0:2])
    to_sq = _parse_sq(uci[2:4])
    promo: PieceType | None = _PROMO_MAP.get(uci[4]) if len(uci) >= 5 else None

    # Map to the exact legal move to preserve special flags.
    for move in MoveGenerator(position).generate_legal_moves():
        if move.from_sq == from_sq and move.to_sq == to_sq and move.promotion == promo:
            return move

    flag = MoveFlag.PROMOTION if promo is not None else MoveFlag.NORMAL
    return Move(from_sq, to_sq, flag, promo)


def is_available() -> bool:
    """Return *True* if the native C++ engine is importable."""
    return _chessie_engine is not None


class CppSearchEngine(IEngine):
    """Chess engine backed by the native C++ search.

    Implements the :class:`IEngine` protocol used by the application.
    """

    __slots__ = ("_engine",)

    def __init__(self, *, tt_mb: int = 64) -> None:
        if _chessie_engine is None:
            msg = (
                "Native C++ engine module (_chessie_engine) is not available. "
                "Build/install Chessie with BUILD_PYBIND=ON."
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

        native_result = self._engine.search(
            fen,
            limits.max_depth,
            time_ms,
        )
        best_move: Move | None

        if len(native_result) == 8:
            (
                has_move,
                from_sq,
                to_sq,
                move_flag,
                promotion,
                score_cp,
                depth,
                nodes,
            ) = native_result
            best_move = None
            if has_move:
                promo = PieceType(promotion) if promotion else None
                best_move = Move(from_sq, to_sq, MoveFlag(move_flag), promo)
        elif len(native_result) == 4:
            uci_move, score_cp, depth, nodes = native_result
            best_move = _legacy_uci_to_move(uci_move, position)
        else:
            raise RuntimeError(
                "Unsupported _chessie_engine.search result format. "
                "Rebuild native module with current bindings."
            )

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
