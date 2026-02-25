"""Piece value object."""

from __future__ import annotations

from dataclasses import dataclass

from chessie.core.enums import Color, PieceType

# FEN character ↔ (Color, PieceType)
_CHAR_MAP: dict[str, tuple[Color, PieceType]] = {
    "P": (Color.WHITE, PieceType.PAWN),
    "N": (Color.WHITE, PieceType.KNIGHT),
    "B": (Color.WHITE, PieceType.BISHOP),
    "R": (Color.WHITE, PieceType.ROOK),
    "Q": (Color.WHITE, PieceType.QUEEN),
    "K": (Color.WHITE, PieceType.KING),
    "p": (Color.BLACK, PieceType.PAWN),
    "n": (Color.BLACK, PieceType.KNIGHT),
    "b": (Color.BLACK, PieceType.BISHOP),
    "r": (Color.BLACK, PieceType.ROOK),
    "q": (Color.BLACK, PieceType.QUEEN),
    "k": (Color.BLACK, PieceType.KING),
}

_UNICODE: dict[tuple[Color, PieceType], str] = {
    (Color.WHITE, PieceType.PAWN): "♙",
    (Color.WHITE, PieceType.KNIGHT): "♘",
    (Color.WHITE, PieceType.BISHOP): "♗",
    (Color.WHITE, PieceType.ROOK): "♖",
    (Color.WHITE, PieceType.QUEEN): "♕",
    (Color.WHITE, PieceType.KING): "♔",
    (Color.BLACK, PieceType.PAWN): "♟",
    (Color.BLACK, PieceType.KNIGHT): "♞",
    (Color.BLACK, PieceType.BISHOP): "♝",
    (Color.BLACK, PieceType.ROOK): "♜",
    (Color.BLACK, PieceType.QUEEN): "♛",
    (Color.BLACK, PieceType.KING): "♚",
}

_FEN_CHARS: dict[tuple[Color, PieceType], str] = {v: k for k, v in _CHAR_MAP.items()}


@dataclass(frozen=True, slots=True)
class Piece:
    """Immutable value object representing a chess piece."""

    color: Color
    piece_type: PieceType

    # ── Serialisation ────────────────────────────────────────────────────

    def __str__(self) -> str:
        """FEN character (uppercase = white, lowercase = black)."""
        return _FEN_CHARS[(self.color, self.piece_type)]

    @classmethod
    def from_char(cls, char: str) -> Piece:
        """Create piece from FEN character, e.g. 'N' → white knight."""
        try:
            color, ptype = _CHAR_MAP[char]
        except KeyError:
            raise ValueError(f"Invalid piece character: {char!r}") from None
        return cls(color, ptype)

    @property
    def symbol(self) -> str:
        """Unicode chess symbol, e.g. ♞."""
        return _UNICODE[(self.color, self.piece_type)]
