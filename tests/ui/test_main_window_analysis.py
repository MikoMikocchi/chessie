"""Tests for MainWindow analysis actions."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast

from chessie.analysis import (
    GameAnalysisReport,
    MoveAnalysis,
    MoveJudgment,
    SideAnalysisSummary,
)
from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.types import parse_square
from chessie.ui.i18n import t
from chessie.ui.main_window import MainWindow


@dataclass
class _ActionStub:
    enabled: bool = True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


class _AnalysisSessionStub:
    def __init__(self, *, should_start: bool = True) -> None:
        self.should_start = should_start
        self.calls: list[dict[str, object]] = []

    def start_analysis(self, **kwargs: object) -> bool:
        self.calls.append(kwargs)
        return self.should_start


class _WidgetStub:
    """Stub for analysis UI widgets (EvalGraph, AnalysisPanel, etc.)."""

    def __init__(self) -> None:
        self.visible = False
        self._data: object = None
        self._report: object = None
        self._active_ply: int | None = None
        self._annotations: dict[int, object] = {}
        self.ply_clicked = _SignalStub()

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def clear(self) -> None:
        self._data = None
        self._report = None

    def set_data(self, *args: object, **kwargs: object) -> None:
        self._data = args

    def set_active_ply(self, ply: int | None) -> None:
        self._active_ply = ply

    def set_report(self, report: object) -> None:
        self._report = report

    def show_move_info(self, ply: int) -> None:
        self._active_ply = ply

    def set_annotations(self, annotations: dict[int, object]) -> None:
        self._annotations = annotations

    def clear_annotations(self) -> None:
        self._annotations.clear()

    def retranslate_ui(self) -> None:
        pass


class _SignalStub:
    """Stub for pyqtSignal.connect/disconnect."""

    def __init__(self) -> None:
        self._slots: list[object] = []

    def connect(self, slot: object) -> None:
        self._slots.append(slot)

    def disconnect(self, slot: object) -> None:
        self._slots = [s for s in self._slots if s is not slot]


def _report() -> GameAnalysisReport:
    move = Move(parse_square("e2"), parse_square("e4"))
    return GameAnalysisReport(
        start_fen="start-fen",
        total_plies=1,
        moves=(
            MoveAnalysis(
                ply=0,
                color=Color.WHITE,
                played_move=move,
                played_san="e4",
                best_move=Move(parse_square("d2"), parse_square("d4")),
                best_san="d4",
                eval_before_white_cp=50,
                eval_after_white_cp=-150,
                cp_loss=200,
                judgment=MoveJudgment.MISTAKE,
            ),
        ),
        white=SideAnalysisSummary(1, 200.0, 0, 1, 0),
        black=SideAnalysisSummary(0, 0.0, 0, 0, 0),
        critical_plies=(0,),
    )


class TestMainWindowAnalysisActions:
    def test_on_analyze_game_handles_empty_history(self) -> None:
        status_updates: list[str] = []
        window = cast(
            MainWindow,
            SimpleNamespace(
                _controller=SimpleNamespace(
                    state=SimpleNamespace(move_history=[], start_fen="start-fen")
                ),
                _analysis_session=_AnalysisSessionStub(),
                _settings=SimpleNamespace(
                    engine_depth=4,
                    engine_time_ms=900,
                    analysis_depth=4,
                    analysis_time_ms=200,
                ),
                _act_analyze_game=_ActionStub(),
                _status_label=SimpleNamespace(
                    setText=lambda text: status_updates.append(text)
                ),
            ),
        )

        MainWindow._on_analyze_game(window)

        assert status_updates
        assert status_updates[-1] == t().status_analysis_no_moves

    def test_on_analyze_game_starts_background_analysis(self) -> None:
        status_updates: list[str] = []
        analysis_session = _AnalysisSessionStub(should_start=True)
        history = [SimpleNamespace(move=Move(parse_square("e2"), parse_square("e4")))]
        window = cast(
            MainWindow,
            SimpleNamespace(
                _controller=SimpleNamespace(
                    state=SimpleNamespace(move_history=history, start_fen="start-fen")
                ),
                _analysis_session=analysis_session,
                _settings=SimpleNamespace(
                    engine_depth=5,
                    engine_time_ms=1_200,
                    analysis_depth=3,
                    analysis_time_ms=250,
                ),
                _act_analyze_game=_ActionStub(),
                _status_label=SimpleNamespace(
                    setText=lambda text: status_updates.append(text)
                ),
                _analysis_report=None,
            ),
        )

        MainWindow._on_analyze_game(window)

        assert analysis_session.calls
        assert analysis_session.calls[0]["max_depth"] == 3
        assert analysis_session.calls[0]["time_limit_ms"] == 250
        assert window._act_analyze_game.enabled is False
        assert status_updates[-1] == t().status_analysis_started.format(total=1)

    def test_on_analysis_finished_enters_analysis_mode(self) -> None:
        status_updates: list[str] = []
        report = _report()
        history = [SimpleNamespace(move=report.moves[0].played_move)]

        eval_graph = _WidgetStub()
        analysis_panel = _WidgetStub()
        move_panel = _WidgetStub()
        exit_btn = _WidgetStub()

        window = cast(
            MainWindow,
            SimpleNamespace(
                _analysis_report=None,
                _analysis_mode=False,
                _controller=SimpleNamespace(
                    state=SimpleNamespace(
                        start_fen="start-fen",
                        move_history=history,
                    )
                ),
                _act_analyze_game=_ActionStub(enabled=False),
                _pgn_move_comments=[None],
                _status_label=SimpleNamespace(
                    setText=lambda text: status_updates.append(text)
                ),
                _on_move_history_selected=lambda _ply: None,
                _on_analysis_ply_selected=lambda _ply: None,
                _eval_graph=eval_graph,
                _analysis_panel=analysis_panel,
                _move_panel=move_panel,
                _exit_analysis_btn=exit_btn,
                _clock_widget=_WidgetStub(),
                _control_panel=_WidgetStub(),
            ),
        )

        from chessie.ui.main_window_parts import analysis as analysis_part

        analysis_part.on_analysis_finished(window, report)

        assert window._analysis_report is report
        assert window._act_analyze_game.enabled is True
        assert window._pgn_move_comments[0] is not None
        assert "Mistake" in (window._pgn_move_comments[0] or "")
        assert status_updates
        # Analysis mode is entered
        assert window._analysis_mode is True
        assert eval_graph.visible is True
        assert analysis_panel.visible is True
        assert exit_btn.visible is True

    def test_on_exit_analysis_restores_normal_ui(self) -> None:
        eval_graph = _WidgetStub()
        eval_graph.visible = True
        analysis_panel = _WidgetStub()
        analysis_panel.visible = True
        move_panel = _WidgetStub()
        exit_btn = _WidgetStub()
        exit_btn.visible = True
        clock_widget = _WidgetStub()
        clock_widget.visible = False
        control_panel = _WidgetStub()
        control_panel.visible = False

        window = cast(
            MainWindow,
            SimpleNamespace(
                _analysis_mode=True,
                _analysis_report=_report(),
                _eval_graph=eval_graph,
                _analysis_panel=analysis_panel,
                _move_panel=move_panel,
                _exit_analysis_btn=exit_btn,
                _clock_widget=clock_widget,
                _control_panel=control_panel,
                _sync_board_interactivity=lambda: None,
                _update_status=lambda: None,
            ),
        )

        from chessie.ui.main_window_parts import analysis as analysis_part

        analysis_part.on_exit_analysis(window)

        assert window._analysis_mode is False
        # Report is intentionally preserved for cache re-use on next "Analyze" click.
        assert window._analysis_report is not None
        assert eval_graph.visible is False
        assert analysis_panel.visible is False
        assert exit_btn.visible is False
        assert clock_widget.visible is True
        assert control_panel.visible is True
