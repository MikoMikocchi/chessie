"""Tests for bitboard helpers."""

from __future__ import annotations

import random

from chessie.core.bitboard import squares_from_bitboard


def _reference_squares_from_bitboard(bitboard: int) -> list[int]:
    squares: list[int] = []
    while bitboard:
        lsb = bitboard & -bitboard
        squares.append(lsb.bit_length() - 1)
        bitboard ^= lsb
    return squares


def test_squares_from_bitboard_empty() -> None:
    assert squares_from_bitboard(0) == []


def test_squares_from_bitboard_single_bit() -> None:
    assert squares_from_bitboard(1 << 63) == [63]


def test_squares_from_bitboard_matches_reference_random() -> None:
    rng = random.Random(1337)
    for _ in range(400):
        bits = rng.sample(range(64), rng.randrange(65))
        bitboard = 0
        for sq in bits:
            bitboard |= 1 << sq
        assert squares_from_bitboard(bitboard) == _reference_squares_from_bitboard(
            bitboard
        )
