"""Square type alias and coordinate helpers.

Board layout (Little-Endian Rank-File mapping):
    a1=0, b1=1, ..., h1=7
    a2=8, b2=9, ..., h2=15
    ...
    a8=56, b8=57, ..., h8=63
"""

from __future__ import annotations

from typing import TypeAlias

Square: TypeAlias = int  # 0–63


def file_of(sq: Square) -> int:
    """File index 0–7 (a–h)."""
    return sq & 7


def rank_of(sq: Square) -> int:
    """Rank index 0–7 (1–8)."""
    return sq >> 3


def make_square(file: int, rank: int) -> Square:
    """Create square from file (0–7) and rank (0–7)."""
    return rank * 8 + file


def square_name(sq: Square) -> str:
    """Human-readable name, e.g. 0 → 'a1', 63 → 'h8'."""
    return chr(ord("a") + file_of(sq)) + str(rank_of(sq) + 1)


def parse_square(name: str) -> Square:
    """Parse square name, e.g. 'e4' → 28."""
    if len(name) != 2 or name[0] not in "abcdefgh" or name[1] not in "12345678":
        raise ValueError(f"Invalid square name: {name!r}")
    return make_square(ord(name[0]) - ord("a"), int(name[1]) - 1)


def is_valid_square(sq: int) -> bool:
    """Check whether integer is a valid square index."""
    return 0 <= sq < 64


# ── Named square constants ──────────────────────────────────────────────────

A1, B1, C1, D1, E1, F1, G1, H1 = range(0, 8)
A2, B2, C2, D2, E2, F2, G2, H2 = range(8, 16)
A3, B3, C3, D3, E3, F3, G3, H3 = range(16, 24)
A4, B4, C4, D4, E4, F4, G4, H4 = range(24, 32)
A5, B5, C5, D5, E5, F5, G5, H5 = range(32, 40)
A6, B6, C6, D6, E6, F6, G6, H6 = range(40, 48)
A7, B7, C7, D7, E7, F7, G7, H7 = range(48, 56)
A8, B8, C8, D8, E8, F8, G8, H8 = range(56, 64)
