"""Board - piece placement on an 8x8 board."""

from __future__ import annotations

from chessie.core.enums import Color, PieceType
from chessie.core.piece import Piece
from chessie.core.types import Square, make_square

_PIECE_TYPE_COUNT = 6
_COLOR_COUNT = 2


class Board:
    """Mutable 64-square board with incremental piece indexes."""

    __slots__ = ("_squares", "_piece_bitboards", "_color_bitboards", "_king_squares")

    def __init__(self) -> None:
        self._squares: list[Piece | None] = [None] * 64
        # [color][piece_type-1] -> bitboard of occupied squares.
        self._piece_bitboards: list[list[int]] = [
            [0] * _PIECE_TYPE_COUNT for _ in range(_COLOR_COUNT)
        ]
        # [color] -> bitboard of all occupied squares for that color.
        self._color_bitboards: list[int] = [0] * _COLOR_COUNT
        # [color] -> king square cache (None if king missing).
        self._king_squares: list[Square | None] = [None] * _COLOR_COUNT

    @staticmethod
    def _piece_type_index(piece_type: PieceType) -> int:
        return int(piece_type) - 1

    @staticmethod
    def _squares_from_bitboard(bitboard: int) -> list[Square]:
        squares: list[Square] = []
        while bitboard:
            lsb = bitboard & -bitboard
            squares.append(lsb.bit_length() - 1)
            bitboard ^= lsb
        return squares

    # -- Element access -----------------------------------------------------

    def __getitem__(self, sq: Square) -> Piece | None:
        return self._squares[sq]

    def __setitem__(self, sq: Square, piece: Piece | None) -> None:
        old_piece = self._squares[sq]
        if old_piece == piece:
            return

        mask = 1 << sq

        if old_piece is not None:
            old_color_idx = int(old_piece.color)
            old_piece_idx = self._piece_type_index(old_piece.piece_type)
            self._piece_bitboards[old_color_idx][old_piece_idx] &= ~mask
            self._color_bitboards[old_color_idx] &= ~mask
            if (
                old_piece.piece_type == PieceType.KING
                and self._king_squares[old_color_idx] == sq
            ):
                self._king_squares[old_color_idx] = None

        self._squares[sq] = piece

        if piece is None:
            return

        color_idx = int(piece.color)
        piece_idx = self._piece_type_index(piece.piece_type)
        self._piece_bitboards[color_idx][piece_idx] |= mask
        self._color_bitboards[color_idx] |= mask
        if piece.piece_type == PieceType.KING:
            self._king_squares[color_idx] = sq

    def is_empty(self, sq: Square) -> bool:
        return self._squares[sq] is None

    # -- Query helpers ------------------------------------------------------

    def pieces(self, color: Color, piece_type: PieceType) -> list[Square]:
        """Squares occupied by *color*'s *piece_type*."""
        bitboard = self._piece_bitboards[int(color)][self._piece_type_index(piece_type)]
        return self._squares_from_bitboard(bitboard)

    def pieces_bitboard(self, color: Color, piece_type: PieceType) -> int:
        """Bitboard of squares occupied by *color*'s *piece_type*."""
        return self._piece_bitboards[int(color)][self._piece_type_index(piece_type)]

    def has_piece(self, color: Color, piece_type: PieceType) -> bool:
        """Whether *color* has at least one piece of *piece_type*."""
        return bool(self.pieces_bitboard(color, piece_type))

    def all_pieces_bitboard(self, color: Color) -> int:
        """Bitboard of all squares occupied by *color*."""
        return self._color_bitboards[int(color)]

    def all_pieces(self, color: Color) -> list[Square]:
        """All squares occupied by *color*."""
        return self._squares_from_bitboard(self.all_pieces_bitboard(color))

    def king_square(self, color: Color) -> Square:
        """Return the single king square for *color*."""
        sq = self._king_squares[int(color)]
        if sq is None:
            raise ValueError(f"No {color.name} king on board")
        return sq

    # -- Mutation / copying -------------------------------------------------

    def copy(self) -> Board:
        b = Board()
        b._squares = self._squares.copy()
        b._piece_bitboards = [row.copy() for row in self._piece_bitboards]
        b._color_bitboards = self._color_bitboards.copy()
        b._king_squares = self._king_squares.copy()
        return b

    def clear(self) -> None:
        self._squares = [None] * 64
        self._piece_bitboards = [[0] * _PIECE_TYPE_COUNT for _ in range(_COLOR_COUNT)]
        self._color_bitboards = [0] * _COLOR_COUNT
        self._king_squares = [None] * _COLOR_COUNT

    # -- Factory ------------------------------------------------------------

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

    # -- Dunder helpers -----------------------------------------------------

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
