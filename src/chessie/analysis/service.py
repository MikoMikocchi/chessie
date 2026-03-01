"""Game analyzer service based on the built-in search engine."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from chessie.analysis.models import (
    GameAnalysisReport,
    MoveAnalysis,
    MoveJudgment,
    SideAnalysisSummary,
)
from chessie.core.enums import Color, MoveFlag
from chessie.core.notation import move_to_san, position_from_fen
from chessie.engine._default import DefaultEngine
from chessie.engine.search import CancelCheck, IEngine, SearchLimits

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
        self._engine = engine or DefaultEngine()

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
            before_limits = _analysis_limits_for_position(limits, previous_move=None)
            before_result = self._engine.search(
                position.copy(),
                before_limits,
                cancelled,
            )

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
            after_limits = _analysis_limits_for_position(limits, previous_move=record)
            after_result = self._engine.search(position.copy(), after_limits, cancelled)
            after_white_cp = _to_white_cp(after_result.score_cp, position.side_to_move)

            best_for_mover = best_white_cp if mover == Color.WHITE else -best_white_cp
            after_for_mover = (
                after_white_cp if mover == Color.WHITE else -after_white_cp
            )

            # If the played move IS the engine's best move, cp_loss is 0
            # regardless of search noise between different evaluations.
            if best_move is not None and record.move == best_move:
                cp_loss = 0
            else:
                raw_loss = _clamp_cp(best_for_mover) - _clamp_cp(after_for_mover)
                cp_loss = max(0, raw_loss)
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

        fingerprint = _compute_move_fingerprint(start_fen, history)

        return GameAnalysisReport(
            start_fen=start_fen,
            total_plies=total,
            moves=tuple(analyses),
            white=white_summary,
            black=black_summary,
            critical_plies=critical,
            move_fingerprint=fingerprint,
        )


def _to_white_cp(score_cp: int, side_to_move: Color) -> int:
    return score_cp if side_to_move == Color.WHITE else -score_cp


# Cap centipawn values so mate scores don't blow up ACPL/accuracy.
_CP_CAP = 1500


def _clamp_cp(cp: int) -> int:
    """Clamp a centipawn value to ±_CP_CAP to bound mate-score effects."""
    return max(-_CP_CAP, min(_CP_CAP, cp))


def _compute_move_fingerprint(
    start_fen: str,
    history: list[MoveRecord],
) -> str:
    """Compute a content-based fingerprint for the game move sequence.

    Uses the FEN after each move (which encodes the full board state)
    together with the starting FEN to produce a deterministic hash.
    """
    h = hashlib.sha256(start_fen.encode(), usedforsecurity=False)
    for rec in history:
        h.update(rec.fen_after.encode())
    return h.hexdigest()


def compute_move_fingerprint(
    start_fen: str,
    history: Iterable[MoveRecord],
) -> str:
    """Public helper: compute the fingerprint for cache validation."""
    h = hashlib.sha256(start_fen.encode(), usedforsecurity=False)
    for rec in history:
        h.update(rec.fen_after.encode())
    return h.hexdigest()


def _analysis_limits_for_position(
    base_limits: SearchLimits,
    *,
    previous_move: MoveRecord | None,
) -> SearchLimits:
    """Scale analysis time for the current position based on tactical cues."""
    base_time_ms = base_limits.time_limit_ms
    if base_time_ms is None:
        return base_limits

    factor = 0.8 if previous_move is None else 0.65
    if previous_move is not None:
        if previous_move.was_capture:
            factor += 0.35
        if previous_move.was_check:
            factor += 0.35
        flag = previous_move.move.flag
        if flag in (MoveFlag.PROMOTION, MoveFlag.EN_PASSANT):
            factor += 0.25
        elif flag in (MoveFlag.CASTLE_KINGSIDE, MoveFlag.CASTLE_QUEENSIDE):
            factor += 0.1

    factor = max(0.5, min(1.8, factor))
    scaled_time_ms = max(25, int(round(base_time_ms * factor)))
    if scaled_time_ms == base_time_ms:
        return base_limits
    return SearchLimits(
        max_depth=base_limits.max_depth,
        time_limit_ms=scaled_time_ms,
    )


def _classify_cp_loss(
    cp_loss: int,
    *,
    is_sacrifice: bool = False,
) -> MoveJudgment:
    if cp_loss <= _BEST_MAX_CP_LOSS:
        if cp_loss <= _BRILLIANT_MAX_CP_LOSS and is_sacrifice:
            return MoveJudgment.BRILLIANT
        if cp_loss <= _GREAT_MAX_CP_LOSS:
            return MoveJudgment.BEST
        return MoveJudgment.GREAT
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
    accuracy = _accuracy_from_avg_cp_loss(avg) if acc.moves > 0 else 100.0
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


def _accuracy_from_avg_cp_loss(avg_cp_loss: float) -> float:
    """Convert average centipawn loss to an accuracy percentage.

    Uses a win-probability-inspired formula that is more robust than a
    linear mapping.  ``103.1668 * exp(-0.04354 * ACPL) - 3.1669`` is a
    well-known approximation (Lichess / chess.com style).
    """
    import math

    if avg_cp_loss <= 0:
        return 100.0
    raw = 103.1668 * math.exp(-0.04354 * avg_cp_loss) - 3.1669
    return max(0.0, min(100.0, raw))
