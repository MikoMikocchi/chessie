"""Tests for MainWindow PGN load/save logic."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from chessie.core.enums import Color, GameResult, MoveFlag
from chessie.core.move import Move
from chessie.core.types import E2, E4, E5, E7
from chessie.game.controller import GameController
from chessie.game.interfaces import GameEndReason, GamePhase, TimeControl
from chessie.game.player import HumanPlayer
from chessie.ui.main_window import MainWindow


def _make_pgn_window(controller: GameController) -> tuple[MainWindow, list[str]]:
    status_updates: list[str] = []
    window = cast(
        MainWindow,
        SimpleNamespace(
            _controller=controller,
            _is_loading_pgn=False,
            _pgn_move_comments=[],
            _status_label=SimpleNamespace(
                setText=lambda text: status_updates.append(text)
            ),
            _cancel_ai_search=lambda: None,
            _connect_game_events=lambda: None,
            _after_new_game=lambda: None,
            _sync_board_interactivity=lambda: None,
            _update_status=lambda: None,
            _on_game_over=lambda _result: None,
            _termination_from_end_reason=MainWindow._termination_from_end_reason,
            _end_reason_from_termination=MainWindow._end_reason_from_termination,
        ),
    )
    return window, status_updates


class TestMainWindowPgn:
    def test_save_pgn(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        ctrl = GameController()
        ctrl.new_game(
            HumanPlayer(Color.WHITE, "White"),
            HumanPlayer(Color.BLACK, "Black"),
            TimeControl.unlimited(),
        )
        ctrl.submit_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        ctrl.submit_move(Move(E7, E5, MoveFlag.DOUBLE_PAWN))

        window, status_updates = _make_pgn_window(ctrl)
        save_path = tmp_path / "saved-game.pgn"

        monkeypatch.setattr(
            "chessie.ui.main_window.QFileDialog.getSaveFileName",
            lambda *args, **kwargs: (str(save_path), "PGN Files (*.pgn)"),
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.QMessageBox.warning",
            lambda *args, **kwargs: None,
        )

        MainWindow._on_save_pgn(window)

        text = save_path.read_text(encoding="utf-8")
        assert '[White "White"]' in text
        assert '[Black "Black"]' in text
        assert '[Termination "unterminated"]' in text
        assert "1. e4 e5 *" in text
        assert status_updates[-1] == f"Saved PGN: {save_path.name}"

    def test_open_pgn(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        pgn_path = tmp_path / "loaded-game.pgn"
        pgn_path.write_text(
            "\n".join(
                [
                    '[Event "Casual"]',
                    '[White "Alice"]',
                    '[Black "Bob"]',
                    '[Result "*"]',
                    "",
                    "1. e4 e5 *",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ctrl = GameController()
        window, status_updates = _make_pgn_window(ctrl)

        monkeypatch.setattr(
            "chessie.ui.main_window.QFileDialog.getOpenFileName",
            lambda *args, **kwargs: (str(pgn_path), "PGN Files (*.pgn)"),
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.QMessageBox.warning",
            lambda *args, **kwargs: None,
        )

        MainWindow._on_open_pgn(window)

        assert ctrl.state.ply_count == 2
        assert [rec.san for rec in ctrl.state.move_history] == ["e4", "e5"]
        assert status_updates[-1] == f"Loaded PGN: {pgn_path.name}"

    def test_open_pgn_applies_termination_reason(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        pgn_path = tmp_path / "time-forfeit.pgn"
        pgn_path.write_text(
            "\n".join(
                [
                    '[Event "Timeout"]',
                    '[Result "1-0"]',
                    '[Termination "time forfeit"]',
                    "",
                    "1-0",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ctrl = GameController()
        window, _status_updates = _make_pgn_window(ctrl)

        monkeypatch.setattr(
            "chessie.ui.main_window.QFileDialog.getOpenFileName",
            lambda *args, **kwargs: (str(pgn_path), "PGN Files (*.pgn)"),
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.QMessageBox.warning",
            lambda *args, **kwargs: None,
        )

        MainWindow._on_open_pgn(window)

        assert ctrl.state.result == GameResult.WHITE_WINS
        assert ctrl.state.phase == GamePhase.GAME_OVER
        assert ctrl.state.end_reason == GameEndReason.FLAG_FALL

    def test_open_then_save_preserves_comments(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        src_path = tmp_path / "commented-src.pgn"
        src_path.write_text(
            "\n".join(
                [
                    '[Event "Commented"]',
                    '[Result "*"]',
                    "",
                    "1. e4 {center} e5 2. Nf3 {develop} *",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        dst_path = tmp_path / "commented-dst.pgn"

        ctrl = GameController()
        window, _status_updates = _make_pgn_window(ctrl)

        monkeypatch.setattr(
            "chessie.ui.main_window.QFileDialog.getOpenFileName",
            lambda *args, **kwargs: (str(src_path), "PGN Files (*.pgn)"),
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.QFileDialog.getSaveFileName",
            lambda *args, **kwargs: (str(dst_path), "PGN Files (*.pgn)"),
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.QMessageBox.warning",
            lambda *args, **kwargs: None,
        )

        MainWindow._on_open_pgn(window)
        MainWindow._on_save_pgn(window)

        saved = dst_path.read_text(encoding="utf-8")
        assert "{center}" in saved
        assert "{develop}" in saved
