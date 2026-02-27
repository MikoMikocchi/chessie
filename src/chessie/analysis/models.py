"""Data models produced by game analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from chessie.core.enums import Color
from chessie.core.move import Move


class MoveJudgment(StrEnum):
    """Human-friendly move quality buckets."""

    BEST = "Best"
    GOOD = "Good"
    INACCURACY = "Inaccuracy"
    MISTAKE = "Mistake"
    BLUNDER = "Blunder"


@dataclass(slots=True, frozen=True)
class SideAnalysisSummary:
    """Aggregate quality metrics for one side."""

    moves: int
    avg_cp_loss: float
    inaccuracies: int
    mistakes: int
    blunders: int


@dataclass(slots=True, frozen=True)
class MoveAnalysis:
    """Engine-backed analysis for a single played move."""

    ply: int
    color: Color
    played_move: Move
    played_san: str
    best_move: Move | None
    best_san: str | None
    eval_before_white_cp: int
    eval_after_white_cp: int
    cp_loss: int
    judgment: MoveJudgment


@dataclass(slots=True, frozen=True)
class GameAnalysisReport:
    """Full move-by-move analysis with side summaries."""

    start_fen: str
    total_plies: int
    moves: tuple[MoveAnalysis, ...]
    white: SideAnalysisSummary
    black: SideAnalysisSummary
    critical_plies: tuple[int, ...]
