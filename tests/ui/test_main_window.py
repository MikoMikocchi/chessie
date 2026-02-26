"""Tests for MainWindow draw handling logic."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast

from PyQt6.QtWidgets import QMessageBox

from chessie.core.enums import Color, MoveFlag
from chessie.core.move import Move
from chessie.core.types import E2, E4, E5, E7
from chessie.game.controller import GameController
from chessie.game.interfaces import TimeControl
from chessie.game.player import HumanPlayer
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
    def test_human_vs_human_accepts_draw_on_confirm(self, monkeypatch) -> None:
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

    def test_human_vs_human_declines_draw_on_confirm(self, monkeypatch) -> None:
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


def _make_pgn_window(controller: GameController) -> tuple[MainWindow, list[str]]:
    status_updates: list[str] = []
    window = cast(
        MainWindow,
        SimpleNamespace(
            _controller=controller,
            _is_loading_pgn=False,
            _status_label=SimpleNamespace(setText=lambda text: status_updates.append(text)),
            _cancel_ai_search=lambda: None,
            _connect_game_events=lambda: None,
            _after_new_game=lambda: None,
            _sync_board_interactivity=lambda: None,
            _update_status=lambda: None,
            _on_game_over=lambda _result: None,
        ),
    )
    return window, status_updates


class TestMainWindowPgn:
    def test_save_pgn(self, monkeypatch, tmp_path) -> None:
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
        assert "1. e4 e5 *" in text
        assert status_updates[-1] == f"Saved PGN: {save_path.name}"

    def test_open_pgn(self, monkeypatch, tmp_path) -> None:
        pgn_path = tmp_path / "loaded-game.pgn"
        pgn_path.write_text(
            '\n'.join(
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
