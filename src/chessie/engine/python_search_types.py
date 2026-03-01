"""Internal dataclasses for the Python search engine."""

from __future__ import annotations

from dataclasses import dataclass

from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.types import Square


@dataclass(slots=True)
class TTEntry:
    depth: int
    score: int
    bound: int
    best_move: Move | None


@dataclass(slots=True)
class NullMoveState:
    side_to_move: Color
    en_passant: Square | None
    halfmove_clock: int
    fullmove_number: int
