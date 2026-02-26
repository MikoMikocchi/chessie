"""Tests for MainWindow move-history jump behavior."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast

from chessie.ui.main_window import MainWindow


@dataclass
class _Record:
    move: object
    fen_after: str


class _StubScene:
    def __init__(self) -> None:
        self.positions: list[object] = []
        self.last_moves: list[object] = []
        self.check_calls = 0
        self.interactive_values: list[bool] = []

    def set_position(self, position: object) -> None:
        self.positions.append(position)

    def highlight_last_move(self, move: object) -> None:
        self.last_moves.append(move)

    def highlight_check(self) -> None:
        self.check_calls += 1

    def set_interactive(self, interactive: bool) -> None:
        self.interactive_values.append(interactive)


def _make_window() -> tuple[MainWindow, _StubScene, list[bool], list[bool], object]:
    scene = _StubScene()
    sync_calls: list[bool] = []
    status_calls: list[bool] = []
    live_position = object()

    history = [
        _Record(
            move="e2e4",
            fen_after="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        ),
        _Record(
            move="e7e5",
            fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
        ),
    ]

    window = cast(
        MainWindow,
        SimpleNamespace(
            _controller=SimpleNamespace(
                state=SimpleNamespace(
                    move_history=history,
                    position=live_position,
                )
            ),
            _board_view=SimpleNamespace(board_scene=scene),
            _history_view_ply=None,
            _sync_board_interactivity=lambda: sync_calls.append(True),
            _update_status=lambda: status_calls.append(True),
        ),
    )
    return window, scene, sync_calls, status_calls, live_position


class TestMainWindowHistoryJump:
    def test_select_old_ply_enters_preview_and_disables_interaction(self) -> None:
        window, scene, sync_calls, status_calls, live_position = _make_window()

        MainWindow._on_move_history_selected(window, 0)

        assert window._history_view_ply == 0
        assert scene.positions
        assert scene.positions[-1] is not live_position
        assert scene.last_moves == ["e2e4"]
        assert scene.check_calls == 1
        assert scene.interactive_values == [False]
        assert sync_calls == []
        assert status_calls == []

    def test_select_latest_ply_returns_to_live_position(self) -> None:
        window, scene, sync_calls, status_calls, live_position = _make_window()
        window._history_view_ply = 0

        MainWindow._on_move_history_selected(window, 1)

        assert window._history_view_ply is None
        assert scene.positions == [live_position]
        assert scene.last_moves == ["e7e5"]
        assert scene.check_calls == 1
        assert sync_calls == [True]
        assert status_calls == [True]

    def test_out_of_range_ply_is_ignored(self) -> None:
        window, scene, sync_calls, status_calls, _live_position = _make_window()

        MainWindow._on_move_history_selected(window, 5)

        assert window._history_view_ply is None
        assert scene.positions == []
        assert scene.last_moves == []
        assert scene.check_calls == 0
        assert scene.interactive_values == []
        assert sync_calls == []
        assert status_calls == []
