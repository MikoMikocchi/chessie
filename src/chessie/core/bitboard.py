"""Bitboard helpers with an optional native acceleration path."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from chessie.core.types import Square


def _scan_bits_python(bitboard: int) -> list[Square]:
    squares: list[Square] = []
    while bitboard:
        lsb = bitboard & -bitboard
        squares.append(lsb.bit_length() - 1)
        bitboard ^= lsb
    return squares


def _load_native_scan_bits() -> Callable[[int], list[Square]] | None:
    native: Any | None = None
    for module_name in ("_chessie_engine", "chessie._chessie_engine"):
        try:
            native = import_module(module_name)
            break
        except ImportError:
            continue
    if native is None:
        return None

    scan_bits = getattr(native, "scan_bits", None)
    if not callable(scan_bits):
        return None
    return cast(Callable[[int], list[Square]], scan_bits)


_NATIVE_SCAN_BITS: Callable[[int], list[Square]] | None = None
_NATIVE_SCAN_BITS_RESOLVED = False


def _native_scan_bits() -> Callable[[int], list[Square]] | None:
    global _NATIVE_SCAN_BITS, _NATIVE_SCAN_BITS_RESOLVED
    if not _NATIVE_SCAN_BITS_RESOLVED:
        _NATIVE_SCAN_BITS = _load_native_scan_bits()
        _NATIVE_SCAN_BITS_RESOLVED = True
    return _NATIVE_SCAN_BITS


def squares_from_bitboard(bitboard: int) -> list[Square]:
    """Return set-bit squares in ascending order (LSB -> MSB)."""
    if bitboard == 0:
        return []

    scan_bits = _native_scan_bits()
    if scan_bits is not None:
        # Safety fallback in case caller passes values outside uint64.
        try:
            return scan_bits(bitboard)
        except OverflowError:
            pass

    return _scan_bits_python(bitboard)
