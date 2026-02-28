"""Game analyzer service based on the built-in search engine."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from chessie.analysis.models import (
    GameAnalysisReport,
    MoveAnalysis,
    MoveJudgment,
    SideAnalysisSummary,
)
from chessie.core.enums import Color
from chessie.core.notation import move_to_san, position_from_fen
from chessie.engine import PythonSearchEngine, SearchLimits
from chessie.engine.search import CancelCheck, IEngine

if TYPE_CHECKING:
    from chessie.game.state import MoveRecord

_BRILLIANT_MAX_CP_LOSS = 0
_GREAT_MAX_CP_LOSS = 10
_BEST_MAX_CP_LOSS = 20
_GOOD_MAX_CP_LOSS = 60
_INACCURACY_MAX_CP_LOSS = 120
_MISTAKE_MAX_CP_LOSS = 250
_CRITICAL_MOVE_COUNT = 3

ProgressCallback = Callable[[int, int], None]


class AnalysisCancelled(Exception):
    """Raised when a running game analysis was cancelled."""


@dataclass(slots=True)
class _SideAcc:
    moves: int = 0
    cp_loss_sum: int = 0
    brilliant: int = 0
    great: int = 0
    best: int = 0
    good: int = 0
    inaccuracies: int = 0
    mistakes: int = 0
    blunders: int = 0


class GameAnalyzer:
    """Analyzes a played move list with per-move engine evaluations."""

    __slots__ = ("_engine",)

    def __init__(self, engine: IEngine | None = None) -> None:
        self._engine = engine or PythonSearchEngine()

    def analyze_game(
        self,
        *,
        start_fen: str,
        move_history: Iterable[MoveRecord],
        limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> GameAnalysisReport:
        """Analyze a game snapshot and return a structured report."""
        history = list(move_history)
        position = position_from_fen(start_fen)
        cancelled = is_cancelled or (lambda: False)

        analyses: list[MoveAnalysis] = []
        total = len(history)
        before_result = None
        if total > 0:
            if cancelled():
                raise AnalysisCancelled
            before_result = self._engine.search(position.copy(), limits, cancelled)

        for ply, record in enumerate(history):
            if cancelled():
                raise AnalysisCancelled

            mover = position.side_to_move
            assert before_result is not None
            best_white_cp = _to_white_cp(before_result.score_cp, mover)
            best_move = before_result.best_move
            best_san = move_to_san(position, best_move) if best_move else None

            position.make_move(record.move)
            if cancelled():
                raise AnalysisCancelled
            after_result = self._engine.search(position.copy(), limits, cancelled)
            after_white_cp = _to_white_cp(after_result.score_cp, position.side_to_move)

            best_for_mover = best_white_cp if mover == Color.WHITE else -best_white_cp
            after_for_mover = (
                after_white_cp if mover == Color.WHITE else -after_white_cp
            )
            cp_loss = max(0, best_for_mover - after_for_mover)
            judgment = _classify_cp_loss(cp_loss)

            analyses.append(
                MoveAnalysis(
                    ply=ply,
                    color=mover,
                    played_move=record.move,
                    played_san=record.san,
                    best_move=best_move,
                    best_san=best_san,
                    eval_before_white_cp=best_white_cp,
                    eval_after_white_cp=after_white_cp,
                    cp_loss=cp_loss,
                    judgment=judgment,
                )
            )
            if on_progress is not None:
                on_progress(ply + 1, total)
            before_result = after_result

        white_summary = _build_side_summary(
            a for a in analyses if a.color == Color.WHITE
        )
        black_summary = _build_side_summary(
            a for a in analyses if a.color == Color.BLACK
        )
        critical = tuple(
            a.ply
            for a in sorted(analyses, key=lambda m: m.cp_loss, reverse=True)[
                :_CRITICAL_MOVE_COUNT
            ]
            if a.cp_loss > 0
        )

        return GameAnalysisReport(
            start_fen=start_fen,
            total_plies=total,
            moves=tuple(analyses),
            white=white_summary,
            black=black_summary,
            critical_plies=critical,
        )


def _to_white_cp(score_cp: int, side_to_move: Color) -> int:
    return score_cp if side_to_move == Color.WHITE else -score_cp


def _classify_cp_loss(
    cp_loss: int,
    *,
    is_sacrifice: bool = False,
) -> MoveJudgment:
    if cp_loss <= _BRILLIANT_MAX_CP_LOSS and is_sacrifice:
        return MoveJudgment.BRILLIANT
    if cp_loss <= _GREAT_MAX_CP_LOSS:
        return MoveJudgment.GREAT
    if cp_loss <= _BEST_MAX_CP_LOSS:
        return MoveJudgment.BEST
    if cp_loss <= _GOOD_MAX_CP_LOSS:
        return MoveJudgment.GOOD
    if cp_loss <= _INACCURACY_MAX_CP_LOSS:
        return MoveJudgment.INACCURACY
    if cp_loss <= _MISTAKE_MAX_CP_LOSS:
        return MoveJudgment.MISTAKE
    return MoveJudgment.BLUNDER


def _build_side_summary(analyses: Iterable[MoveAnalysis]) -> SideAnalysisSummary:
    acc = _SideAcc()
    for move in analyses:
        acc.moves += 1
        acc.cp_loss_sum += move.cp_loss
        if move.judgment == MoveJudgment.BRILLIANT:
            acc.brilliant += 1
        elif move.judgment == MoveJudgment.GREAT:
            acc.great += 1
        elif move.judgment == MoveJudgment.BEST:
            acc.best += 1
        elif move.judgment == MoveJudgment.GOOD:
            acc.good += 1
        elif move.judgment == MoveJudgment.INACCURACY:
            acc.inaccuracies += 1
        elif move.judgment == MoveJudgment.MISTAKE:
            acc.mistakes += 1
        elif move.judgment == MoveJudgment.BLUNDER:
            acc.blunders += 1

    avg = (acc.cp_loss_sum / acc.moves) if acc.moves > 0 else 0.0
    accuracy = max(0.0, 100.0 - avg * 0.1) if acc.moves > 0 else 100.0
    return SideAnalysisSummary(
        moves=acc.moves,
        avg_cp_loss=avg,
        inaccuracies=acc.inaccuracies,
        mistakes=acc.mistakes,
        blunders=acc.blunders,
        brilliant=acc.brilliant,
        great=acc.great,
        best=acc.best,
        good=acc.good,
        accuracy=accuracy,
    )
