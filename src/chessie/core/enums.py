"""Core enumerations and flags for chess domain."""

from __future__ import annotations

from enum import IntEnum, IntFlag, auto


class Color(IntEnum):
    """Side color."""

    WHITE = 0
    BLACK = 1

    @property
    def opposite(self) -> Color:
        return Color(1 - self.value)

    def __str__(self) -> str:
        return self.name.lower()


class PieceType(IntEnum):
    """Chess piece types ordered by conventional value."""

    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6


class MoveFlag(IntEnum):
    """Special move classification."""

    NORMAL = 0
    DOUBLE_PAWN = 1
    EN_PASSANT = 2
    CASTLE_KINGSIDE = 3
    CASTLE_QUEENSIDE = 4
    PROMOTION = 5


class CastlingRights(IntFlag):
    """Bitmask for castling availability."""

    NONE = 0
    WHITE_KINGSIDE = auto()
    WHITE_QUEENSIDE = auto()
    BLACK_KINGSIDE = auto()
    BLACK_QUEENSIDE = auto()

    WHITE_BOTH = WHITE_KINGSIDE | WHITE_QUEENSIDE
    BLACK_BOTH = BLACK_KINGSIDE | BLACK_QUEENSIDE
    ALL = WHITE_BOTH | BLACK_BOTH


class GameResult(IntEnum):
    """Outcome of a game."""

    IN_PROGRESS = 0
    WHITE_WINS = 1
    BLACK_WINS = 2
    DRAW = 3
