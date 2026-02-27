"""Zobrist hashing keys for incremental position hashing."""

from __future__ import annotations

from typing import Final

from chessie.core.enums import CastlingRights
from chessie.core.piece import Piece
from chessie.core.types import Square

_SEED: Final = 0xA5B3C7D9E1F23412
_MASK_64: Final = 0xFFFFFFFFFFFFFFFF


def _splitmix64(state: int) -> int:
    """Deterministic 64-bit bit-mixer suitable for static key generation."""
    z = (state + 0x9E3779B97F4A7C15) & _MASK_64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK_64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK_64
    return z ^ (z >> 31)


def _nth_key(index: int) -> int:
    return _splitmix64(_SEED + index)


_PIECE_KEYS: Final = tuple(
    tuple(
        tuple(_nth_key((color * 384) + (ptype * 64) + sq) for sq in range(64))
        for ptype in range(6)
    )
    for color in range(2)
)
_SIDE_TO_MOVE_KEY: Final = _nth_key(2 * 6 * 64)
_CASTLING_KEYS: Final = tuple(_nth_key((2 * 6 * 64) + 1 + idx) for idx in range(16))
_EN_PASSANT_KEYS: Final = tuple(
    _nth_key((2 * 6 * 64) + 1 + 16 + idx) for idx in range(64)
)


def piece_key(piece: Piece, sq: Square) -> int:
    """Hash key for a specific piece on a square."""
    return _PIECE_KEYS[int(piece.color)][int(piece.piece_type) - 1][sq]


def side_to_move_key() -> int:
    """Hash toggle key for side to move."""
    return _SIDE_TO_MOVE_KEY


def castling_key(castling: CastlingRights) -> int:
    """Hash key for castling rights state."""
    return _CASTLING_KEYS[int(castling) & 0xF]


def en_passant_key(ep_square: Square) -> int:
    """Hash key for an en passant target square."""
    return _EN_PASSANT_KEYS[ep_square]
