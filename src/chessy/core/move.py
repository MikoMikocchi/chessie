"""Move value object (UCI-style representation)."""

from __future__ import annotations

from dataclasses import dataclass

from chessy.core.enums import MoveFlag, PieceType
from chessy.core.types import Square, square_name

_PROMO_CHARS: dict[PieceType, str] = {
    PieceType.KNIGHT: "n",
    PieceType.BISHOP: "b",
    PieceType.ROOK: "r",
    PieceType.QUEEN: "q",
}


@dataclass(frozen=True, slots=True)
class Move:
    """Immutable value object representing a single chess move."""

    from_sq: Square
    to_sq: Square
    flag: MoveFlag = MoveFlag.NORMAL
    promotion: PieceType | None = None

    # ── Display ──────────────────────────────────────────────────────────

    def __str__(self) -> str:
        base = f"{square_name(self.from_sq)}{square_name(self.to_sq)}"
        if self.promotion is not None:
            base += _PROMO_CHARS.get(self.promotion, "")
        return base

    @property
    def uci(self) -> str:
        """UCI long-algebraic notation."""
        return str(self)
