"""Tests for MainWindow draw handling logic."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast

from chessie.core.enums import Color
from chessie.ui.main_window import MainWindow


@dataclass
class _StubPlayer:
    is_human: bool


class _StubController:
    def __init__(
        self,
        *,
        white_human: bool = True,
        black_human: bool = True,
        is_game_over: bool = False,
        side_to_move: Color = Color.WHITE,
    ) -> None:
        self.state = SimpleNamespace(
            is_game_over=is_game_over,
            side_to_move=side_to_move,
        )
        self._players = {
            Color.WHITE: _StubPlayer(is_human=white_human),
            Color.BLACK: _StubPlayer(is_human=black_human),
        }
        self.offered: list[Color] = []
        self.accepted: list[Color] = []

    def offer_draw(self, color: Color) -> None:
        self.offered.append(color)

    def accept_draw(self, color: Color) -> None:
        self.accepted.append(color)

    def player(self, color: Color) -> _StubPlayer | None:
        return self._players.get(color)


def _make_window(controller: _StubController) -> MainWindow:
    return cast(MainWindow, SimpleNamespace(_controller=controller))


class TestMainWindowDraw:
    def test_human_vs_human_auto_accepts_draw(self) -> None:
        ctrl = _StubController()
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == [Color.WHITE]
        assert ctrl.accepted == [Color.BLACK]

    def test_human_vs_human_auto_accepts_for_black_turn(self) -> None:
        ctrl = _StubController(side_to_move=Color.BLACK)
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == [Color.BLACK]
        assert ctrl.accepted == [Color.WHITE]

    def test_not_auto_accepted_when_not_human_vs_human(self) -> None:
        ctrl = _StubController(black_human=False)
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == [Color.WHITE]
        assert ctrl.accepted == []

    def test_draw_click_ignored_when_game_is_over(self) -> None:
        ctrl = _StubController(is_game_over=True)
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == []
        assert ctrl.accepted == []


@dataclass
class _UndoStep:
    ok: bool
    side_is_human: bool
    move_history: list[SimpleNamespace]
    position: object


class _UndoController:
    def __init__(
        self,
        *,
        white_human: bool,
        black_human: bool,
        steps: list[_UndoStep],
    ) -> None:
        self._players = {
            Color.WHITE: _StubPlayer(is_human=white_human),
            Color.BLACK: _StubPlayer(is_human=black_human),
        }
        self._steps = steps
        self.undo_calls = 0
        self.current_player = _StubPlayer(is_human=True)
        self.state = SimpleNamespace(move_history=[], position="start")

    def player(self, color: Color) -> _StubPlayer | None:
        return self._players.get(color)

    def undo_move(self) -> bool:
        step = self._steps[self.undo_calls]
        self.undo_calls += 1
        if not step.ok:
            return False

        self.current_player = _StubPlayer(is_human=step.side_is_human)
        self.state = SimpleNamespace(
            move_history=step.move_history,
            position=step.position,
        )
        return True


class _StubBoardScene:
    def __init__(self) -> None:
        self.positions: list[object] = []
        self.last_moves: list[object | None] = []
        self.check_highlights = 0

    def set_position(self, position: object) -> None:
        self.positions.append(position)

    def highlight_last_move(self, move: object | None) -> None:
        self.last_moves.append(move)

    def highlight_check(self) -> None:
        self.check_highlights += 1


class _StubMovePanel:
    def __init__(self) -> None:
        self.histories: list[list[SimpleNamespace]] = []

    def set_history(self, records: list[SimpleNamespace]) -> None:
        self.histories.append(records)


def _make_undo_window(
    controller: _UndoController,
) -> tuple[MainWindow, _StubBoardScene, _StubMovePanel, list[bool], list[bool]]:
    scene = _StubBoardScene()
    sync_calls: list[bool] = []
    status_calls: list[bool] = []
    move_panel = _StubMovePanel()

    window = cast(
        MainWindow,
        SimpleNamespace(
            _controller=controller,
            _board_view=SimpleNamespace(board_scene=scene),
            _move_panel=move_panel,
            _is_human_vs_ai=lambda: (
                (white := controller.player(Color.WHITE)) is not None
                and (black := controller.player(Color.BLACK)) is not None
                and white.is_human != black.is_human
            ),
            _sync_board_interactivity=lambda: sync_calls.append(True),
            _update_status=lambda: status_calls.append(True),
        ),
    )
    return window, scene, move_panel, sync_calls, status_calls


class TestMainWindowUndo:
    def test_human_vs_ai_undo_rolls_back_full_turn(self) -> None:
        rec = SimpleNamespace(move="e2e4")
        ctrl = _UndoController(
            white_human=True,
            black_human=False,
            steps=[
                _UndoStep(
                    ok=True,
                    side_is_human=False,
                    move_history=[rec],
                    position="after_first_undo",
                ),
                _UndoStep(
                    ok=True,
                    side_is_human=True,
                    move_history=[],
                    position="after_second_undo",
                ),
            ],
        )
        window, scene, move_panel, sync_calls, status_calls = _make_undo_window(ctrl)

        MainWindow._on_undo(window)

        assert ctrl.undo_calls == 2
        assert scene.positions == ["after_second_undo"]
        assert scene.last_moves == [None]
        assert scene.check_highlights == 1
        assert move_panel.histories == [[]]
        assert len(sync_calls) == 1
        assert len(status_calls) == 1

    def test_human_vs_human_undo_stays_single(self) -> None:
        rec = SimpleNamespace(move="e2e4")
        ctrl = _UndoController(
            white_human=True,
            black_human=True,
            steps=[
                _UndoStep(
                    ok=True,
                    side_is_human=True,
                    move_history=[rec],
                    position="after_first_undo",
                )
            ],
        )
        window, scene, move_panel, _sync_calls, _status_calls = _make_undo_window(ctrl)

        MainWindow._on_undo(window)

        assert ctrl.undo_calls == 1
        assert scene.positions == ["after_first_undo"]
        assert scene.last_moves == ["e2e4"]
        assert move_panel.histories == [[rec]]

    def test_undo_noop_when_controller_refuses(self) -> None:
        ctrl = _UndoController(
            white_human=True,
            black_human=False,
            steps=[
                _UndoStep(ok=False, side_is_human=True, move_history=[], position="x")
            ],
        )
        window, scene, move_panel, sync_calls, status_calls = _make_undo_window(ctrl)

        MainWindow._on_undo(window)

        assert ctrl.undo_calls == 1
        assert scene.positions == []
        assert move_panel.histories == []
        assert len(sync_calls) == 0
        assert len(status_calls) == 0
