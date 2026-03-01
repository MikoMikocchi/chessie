"""MainWindow analysis actions and report application helpers."""

from __future__ import annotations

import contextlib
from typing import Any

from PyQt6.QtGui import QColor

from chessie.analysis import (
    GameAnalysisReport,
    MoveAnalysis,
    MoveJudgment,
    compute_move_fingerprint,
)
from chessie.ui.i18n import t


def on_analyze_game(host: Any, *, message_box_cls: type[Any]) -> None:
    state = host._controller.state
    if not state.move_history:
        host._status_label.setText(t().status_analysis_no_moves)
        return

    # Re-use cached report if it matches the current game exactly.
    cached: GameAnalysisReport | None = host._analysis_report
    if (
        cached is not None
        and cached.start_fen == state.start_fen
        and cached.total_plies == len(state.move_history)
        and cached.move_fingerprint
        and cached.move_fingerprint
        == compute_move_fingerprint(state.start_fen, state.move_history)
    ):
        _enter_analysis_mode(host, cached)
        host._status_label.setText(
            t().status_analysis_done.format(
                white_avg=f"{cached.white.avg_cp_loss:.1f}",
                black_avg=f"{cached.black.avg_cp_loss:.1f}",
            )
        )
        return

    analysis_depth = max(
        1,
        int(
            getattr(
                host._settings,
                "analysis_depth",
                getattr(host._settings, "engine_depth", 4),
            )
        ),
    )
    analysis_time_ms = max(
        50,
        int(
            getattr(
                host._settings,
                "analysis_time_ms",
                getattr(host._settings, "engine_time_ms", 900),
            )
        ),
    )

    started = host._analysis_session.start_analysis(
        start_fen=state.start_fen,
        move_history=state.move_history,
        max_depth=analysis_depth,
        time_limit_ms=analysis_time_ms,
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
) -> None:
    host._analysis_report = report
    host._act_analyze_game.setEnabled(True)

    state = host._controller.state
    if (
        state.start_fen == report.start_fen
        and len(state.move_history) == report.total_plies
        and (
            not report.move_fingerprint
            or report.move_fingerprint
            == compute_move_fingerprint(state.start_fen, state.move_history)
        )
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

    _enter_analysis_mode(host, report)


def on_analysis_failed(host: Any, message: str) -> None:
    host._act_analyze_game.setEnabled(True)
    host._status_label.setText(t().status_analysis_failed.format(msg=message))


def on_analysis_cancelled(host: Any) -> None:
    host._act_analyze_game.setEnabled(True)
    host._status_label.setText(t().status_analysis_cancelled)


def on_exit_analysis(host: Any) -> None:
    """Leave analysis mode and restore normal game UI.

    The analysis report is intentionally kept in ``host._analysis_report`` so
    that re-clicking "Analyze Game" for the same position shows the result
    immediately without re-running the engine.
    """
    host._analysis_mode = False
    # _analysis_report is preserved for cache re-use (not cleared here).

    # Hide analysis widgets
    host._eval_graph.hide()
    host._eval_graph.clear()
    host._analysis_panel.hide()
    host._analysis_panel.clear()
    host._exit_analysis_btn.hide()

    # Show normal game widgets
    host._clock_widget.show()
    host._control_panel.show()

    # Clear annotations from move panel
    host._move_panel.clear_annotations()

    host._sync_board_interactivity()
    host._update_status()


def on_analysis_ply_selected(host: Any, ply: int) -> None:
    """Handle ply selection in analysis mode (from graph or move panel)."""
    if not host._analysis_mode or host._analysis_report is None:
        return

    host._analysis_panel.show_move_info(ply)
    host._eval_graph.set_active_ply(ply)

    # Jump the board to the selected ply
    host._on_move_history_selected(ply)


# ── Internal helpers ─────────────────────────────────────────────────────


def _enter_analysis_mode(host: Any, report: GameAnalysisReport) -> None:
    """Switch the UI into analysis mode."""
    host._analysis_mode = True

    # Hide normal game widgets
    host._clock_widget.hide()
    host._control_panel.hide()

    # Populate and show analysis widgets
    host._analysis_panel.set_report(report)
    host._analysis_panel.show()

    # Populate eval graph
    evals = [float(m.eval_after_white_cp) for m in report.moves]
    marker_colors: list[QColor | None] = []
    for m in report.moves:
        if m.judgment in (
            MoveJudgment.BLUNDER,
            MoveJudgment.MISTAKE,
            MoveJudgment.INACCURACY,
            MoveJudgment.BRILLIANT,
        ):
            marker_colors.append(QColor(m.judgment.color_hex))
        else:
            marker_colors.append(None)
    host._eval_graph.set_data(evals, marker_colors)
    host._eval_graph.show()

    host._exit_analysis_btn.show()

    # Annotate moves in the move panel
    annotations: dict[int, MoveJudgment] = {}
    for m in report.moves:
        if m.judgment.nag:  # only annotate non-trivial judgments
            annotations[m.ply] = m.judgment
    host._move_panel.set_annotations(annotations)

    # Connect graph click to analysis handler
    # Disconnect first to avoid double connections
    with contextlib.suppress(TypeError, RuntimeError):
        host._eval_graph.ply_clicked.disconnect(host._on_analysis_ply_selected)
    host._eval_graph.ply_clicked.connect(host._on_analysis_ply_selected)

    # Show info for the last move by default
    if report.moves:
        last_ply = len(report.moves) - 1
        host._analysis_panel.show_move_info(last_ply)
        host._eval_graph.set_active_ply(last_ply)


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
    nag = analysis.judgment.nag
    label = analysis.judgment.value
    if analysis.judgment in (
        MoveJudgment.BEST,
        MoveJudgment.GOOD,
        MoveJudgment.GREAT,
        MoveJudgment.BRILLIANT,
    ):
        suffix = f" (CPL {analysis.cp_loss})" if analysis.cp_loss > 0 else ""
        return f"{nag}{label}{suffix}" if nag else f"{label}{suffix}"
    best = analysis.best_san if analysis.best_san else "-"
    return f"{nag} {label} (CPL {analysis.cp_loss}, best {best})"
