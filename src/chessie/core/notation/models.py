"""Shared notation-layer data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PgnMove:
    """A single mainline move extracted from PGN movetext."""

    san: str
    comment: str = ""


@dataclass(slots=True)
class ParsedPgn:
    """Structured PGN payload used by UI/game import paths."""

    headers: dict[str, str]
    moves: list[PgnMove]
    result_token: str
