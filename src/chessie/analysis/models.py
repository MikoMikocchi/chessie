"""Data models produced by game analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from chessie.core.enums import Color
from chessie.core.move import Move


class MoveJudgment(StrEnum):
    """Human-friendly move quality buckets."""

    BRILLIANT = "Brilliant"
    GREAT = "Great"
    BEST = "Best"
    GOOD = "Good"
    INACCURACY = "Inaccuracy"
    MISTAKE = "Mistake"
    BLUNDER = "Blunder"

    @property
    def nag(self) -> str:
        """Chess NAG annotation symbol."""
        return _JUDGMENT_NAG[self]

    @property
    def color_hex(self) -> str:
        """Hex colour string for UI display."""
        return _JUDGMENT_COLOR[self]


_JUDGMENT_NAG: dict[MoveJudgment, str] = {
    MoveJudgment.BRILLIANT: "!!",
    MoveJudgment.GREAT: "!",
    MoveJudgment.BEST: "",
    MoveJudgment.GOOD: "",
    MoveJudgment.INACCURACY: "?!",
    MoveJudgment.MISTAKE: "?",
    MoveJudgment.BLUNDER: "??",
}

_JUDGMENT_COLOR: dict[MoveJudgment, str] = {
    MoveJudgment.BRILLIANT: "#1baaa7",
    MoveJudgment.GREAT: "#5c8bb0",
    MoveJudgment.BEST: "#9bc700",
    MoveJudgment.GOOD: "#97af8b",
    MoveJudgment.INACCURACY: "#f7c631",
    MoveJudgment.MISTAKE: "#e68a2e",
    MoveJudgment.BLUNDER: "#ca3431",
}


@dataclass(slots=True, frozen=True)
class SideAnalysisSummary:
    """Aggregate quality metrics for one side."""

    moves: int
    avg_cp_loss: float
    inaccuracies: int
    mistakes: int
    blunders: int
    brilliant: int = 0
    great: int = 0
    best: int = 0
    good: int = 0
    accuracy: float = 0.0


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
