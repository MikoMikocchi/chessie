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
