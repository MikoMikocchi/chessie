"""Shared engine search models and protocol."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from chessie.core.move import Move
    from chessie.core.position import Position

CancelCheck = Callable[[], bool]


@dataclass(slots=True, frozen=True)
class SearchLimits:
    """Search constraints for a single move computation."""

    max_depth: int = 3
    time_limit_ms: int | None = 700


@dataclass(slots=True, frozen=True)
class SearchResult:
    """Result produced by the engine search."""

    best_move: Move | None
    score_cp: int
    depth: int
    nodes: int


class IEngine(Protocol):
    """Protocol for chess engines used by the UI/game layer."""

    def search(
        self,
        position: Position,
        limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
    ) -> SearchResult: ...
