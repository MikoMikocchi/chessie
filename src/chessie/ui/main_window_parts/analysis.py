"""MainWindow analysis actions and report application helpers."""

from __future__ import annotations

from typing import Any

from chessie.analysis import GameAnalysisReport, MoveAnalysis, MoveJudgment
from chessie.ui.i18n import t


def on_analyze_game(host: Any, *, message_box_cls: type[Any]) -> None:
    state = host._controller.state
    if not state.move_history:
        host._status_label.setText(t().status_analysis_no_moves)
        return

    started = host._analysis_session.start_analysis(
        start_fen=state.start_fen,
        move_history=state.move_history,
        max_depth=max(1, host._settings.engine_depth),
        time_limit_ms=max(50, host._settings.engine_time_ms),
    )
    if not started:
        host._status_label.setText(t().status_analysis_failed.format(msg="not started"))
        return

    host._act_analyze_game.setEnabled(False)
    host._status_label.setText(
        t().status_analysis_started.format(total=len(state.move_history))
    )


def on_analysis_progress(host: Any, done: int, total: int) -> None:
    host._status_label.setText(
        t().status_analyzing_progress.format(done=done, total=total)
    )


def on_analysis_finished(
    host: Any,
    report: GameAnalysisReport,
    *,
    analysis_dialog_cls: type[Any],
) -> None:
    host._analysis_report = report
    host._act_analyze_game.setEnabled(True)

    state = host._controller.state
    if (
        state.start_fen == report.start_fen
        and len(state.move_history) == report.total_plies
    ):
        host._pgn_move_comments = _merge_analysis_comments(
            host._pgn_move_comments,
            report.moves,
        )

    host._status_label.setText(
        t().status_analysis_done.format(
            white_avg=f"{report.white.avg_cp_loss:.1f}",
            black_avg=f"{report.black.avg_cp_loss:.1f}",
        )
    )

    dialog = analysis_dialog_cls(
        report,
        on_jump_to_ply=host._on_move_history_selected,
        parent=host,
    )
    dialog.exec()


def on_analysis_failed(host: Any, message: str) -> None:
    host._act_analyze_game.setEnabled(True)
    host._status_label.setText(t().status_analysis_failed.format(msg=message))


def on_analysis_cancelled(host: Any) -> None:
    host._act_analyze_game.setEnabled(True)
    host._status_label.setText(t().status_analysis_cancelled)


def _merge_analysis_comments(
    comments: list[str | None],
    move_analyses: tuple[MoveAnalysis, ...],
) -> list[str | None]:
    merged = comments[: len(move_analyses)]
    if len(merged) < len(move_analyses):
        merged.extend([None] * (len(move_analyses) - len(merged)))

    for analysis in move_analyses:
        annotation = _annotation_text(analysis)
        current = merged[analysis.ply]
        if current:
            if annotation in current.split(" | "):
                continue
            merged[analysis.ply] = f"{current} | {annotation}"
        else:
            merged[analysis.ply] = annotation
    return merged


def _annotation_text(analysis: MoveAnalysis) -> str:
    if analysis.judgment in (MoveJudgment.BEST, MoveJudgment.GOOD):
        return (
            f"{analysis.judgment.value} (CPL {analysis.cp_loss})"
            if analysis.cp_loss > 0
            else analysis.judgment.value
        )
    best = analysis.best_san if analysis.best_san else "-"
    return f"{analysis.judgment.value} (CPL {analysis.cp_loss}, best {best})"
