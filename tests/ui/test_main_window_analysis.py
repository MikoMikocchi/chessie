"""Tests for MainWindow analysis actions."""

from __future__ import annotations

from collections.abc import Callable
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


class _DialogStub:
    called = 0

    def __init__(
        self,
        _report: object,
        *,
        on_jump_to_ply: Callable[[int], None] | None,
        parent: object,
    ) -> None:
        self._on_jump = on_jump_to_ply
        self._parent = parent

    def exec(self) -> int:
        _DialogStub.called += 1
        return 0


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
                _settings=SimpleNamespace(engine_depth=4, engine_time_ms=900),
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
                _settings=SimpleNamespace(engine_depth=5, engine_time_ms=1_200),
                _act_analyze_game=_ActionStub(),
                _status_label=SimpleNamespace(
                    setText=lambda text: status_updates.append(text)
                ),
            ),
        )

        MainWindow._on_analyze_game(window)

        assert analysis_session.calls
        assert window._act_analyze_game.enabled is False
        assert status_updates[-1] == t().status_analysis_started.format(total=1)

    def test_on_analysis_finished_merges_comments_and_opens_dialog(self) -> None:
        _DialogStub.called = 0
        status_updates: list[str] = []
        report = _report()
        history = [SimpleNamespace(move=report.moves[0].played_move)]

        window = cast(
            MainWindow,
            SimpleNamespace(
                _analysis_report=None,
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
            ),
        )

        from chessie.ui.main_window_parts import analysis as analysis_part

        analysis_part.on_analysis_finished(
            window,
            report,
            analysis_dialog_cls=_DialogStub,
        )

        assert window._analysis_report is report
        assert window._act_analyze_game.enabled is True
        assert window._pgn_move_comments[0] is not None
        assert "Mistake" in (window._pgn_move_comments[0] or "")
        assert _DialogStub.called == 1
        assert status_updates
