"""Tests for MainWindow draw handling logic."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast

import pytest
from PyQt6.QtWidgets import QMessageBox

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
        self.declined = 0

    def offer_draw(self, color: Color) -> None:
        self.offered.append(color)

    def accept_draw(self, color: Color) -> None:
        self.accepted.append(color)

    def decline_draw(self) -> None:
        self.declined += 1

    def player(self, color: Color) -> _StubPlayer | None:
        return self._players.get(color)


def _make_window(controller: _StubController) -> MainWindow:
    return cast(
        MainWindow,
        SimpleNamespace(
            _controller=controller,
            _status_label=SimpleNamespace(setText=lambda _text: None),
            _is_human_vs_human=lambda: (
                (white := controller.player(Color.WHITE)) is not None
                and (black := controller.player(Color.BLACK)) is not None
                and white.is_human
                and black.is_human
            ),
        ),
    )


class TestMainWindowDraw:
    def test_human_vs_human_accepts_draw_on_confirm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )
        ctrl = _StubController()
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == [Color.WHITE]
        assert ctrl.accepted == [Color.BLACK]
        assert ctrl.declined == 0

    def test_human_vs_human_declines_draw_on_confirm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.No,
        )
        ctrl = _StubController(side_to_move=Color.BLACK)
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == [Color.BLACK]
        assert ctrl.accepted == []
        assert ctrl.declined == 1

    def test_draw_declined_when_not_human_vs_human(self) -> None:
        ctrl = _StubController(black_human=False)
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == [Color.WHITE]
        assert ctrl.accepted == []
        assert ctrl.declined == 1

    def test_draw_click_ignored_when_game_is_over(self) -> None:
        ctrl = _StubController(is_game_over=True)
        MainWindow._on_draw(_make_window(ctrl))

        assert ctrl.offered == []
        assert ctrl.accepted == []
        assert ctrl.declined == 0
