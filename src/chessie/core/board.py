"""Board — piece placement on an 8×8 board."""

from __future__ import annotations

from chessie.core.enums import Color, PieceType
from chessie.core.piece import Piece
from chessie.core.types import Square, make_square


class Board:
    """Mutable 64-square array storing :class:`Piece` or ``None``."""

    __slots__ = ("_squares",)

    def __init__(self) -> None:
        self._squares: list[Piece | None] = [None] * 64

    # ── Element access ───────────────────────────────────────────────────

    def __getitem__(self, sq: Square) -> Piece | None:
        return self._squares[sq]

    def __setitem__(self, sq: Square, piece: Piece | None) -> None:
        self._squares[sq] = piece

    def is_empty(self, sq: Square) -> bool:
        return self._squares[sq] is None

    # ── Query helpers ────────────────────────────────────────────────────

    def pieces(self, color: Color, piece_type: PieceType) -> list[Square]:
        """Squares occupied by *color*'s *piece_type*."""
        return [
            sq
            for sq, p in enumerate(self._squares)
            if p is not None and p.color == color and p.piece_type == piece_type
        ]

    def all_pieces(self, color: Color) -> list[Square]:
        """All squares occupied by *color*."""
        return [
            sq
            for sq, p in enumerate(self._squares)
            if p is not None and p.color == color
        ]

    def king_square(self, color: Color) -> Square:
        """Return the single king square for *color*."""
        kings = self.pieces(color, PieceType.KING)
        if not kings:
            raise ValueError(f"No {color.name} king on board")
        return kings[0]

    # ── Mutation / copying ───────────────────────────────────────────────

    def copy(self) -> Board:
        b = Board()
        b._squares = self._squares.copy()
        return b

    def clear(self) -> None:
        self._squares = [None] * 64

    # ── Factory ──────────────────────────────────────────────────────────

    @classmethod
    def initial(cls) -> Board:
        """Standard starting position."""
        b = cls()
        for f in range(8):
            b[make_square(f, 1)] = Piece(Color.WHITE, PieceType.PAWN)
            b[make_square(f, 6)] = Piece(Color.BLACK, PieceType.PAWN)

        back_rank = [
            PieceType.ROOK,
            PieceType.KNIGHT,
            PieceType.BISHOP,
            PieceType.QUEEN,
            PieceType.KING,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
        ]
        for f, pt in enumerate(back_rank):
            b[make_square(f, 0)] = Piece(Color.WHITE, pt)
            b[make_square(f, 7)] = Piece(Color.BLACK, pt)
        return b

    # ── Dunder helpers ───────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return NotImplemented
        return self._squares == other._squares

    def __repr__(self) -> str:
        rows: list[str] = []
        for rank in range(7, -1, -1):
            row = []
            for file in range(8):
                p = self[make_square(file, rank)]
                row.append(str(p) if p else ".")
            rows.append(f"{rank + 1} {' '.join(row)}")
        rows.append("  a b c d e f g h")
        return "\n".join(rows)
