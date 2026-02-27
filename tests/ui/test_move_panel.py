"""Tests for move history panel behavior."""

from __future__ import annotations

from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.types import parse_square
from chessie.game.state import MoveRecord
from chessie.ui.panels.move_panel import MovePanel, _figurine_san


def _rec(san: str) -> MoveRecord:
    move = Move(parse_square("e2"), parse_square("e4"))
    return MoveRecord(move=move, san=san, fen_after="")


def test_figurine_san_replaces_leading_piece_and_promotion() -> None:
    assert _figurine_san("Nf3", color=Color.WHITE) == "♘f3"
    assert _figurine_san("e8=Q+", color=Color.WHITE) == "e8=♕+"


def test_set_history_and_toggle_notation_rebuilds_text() -> None:
    panel = MovePanel()
    panel.set_history([_rec("Nf3"), _rec("Nc6")])

    white_btn_text = panel._move_buttons[0].text()
    black_btn_text = panel._move_buttons[1].text()
    assert white_btn_text == "♘f3"
    assert black_btn_text == "♞c6"

    panel.set_use_figurine_notation(False)
    assert panel._move_buttons[0].text() == "Nf3"
    assert panel._move_buttons[1].text() == "Nc6"


def test_clicking_move_emits_ply_and_sets_active_state() -> None:
    panel = MovePanel()
    panel.set_history([_rec("e4"), _rec("e5"), _rec("Nf3")])

    clicked: list[int] = []
    panel.move_clicked.connect(clicked.append)
    panel._on_move_clicked(1)

    assert clicked == [1]
    assert panel._active_ply == 1
    assert panel._move_buttons[1].property("activeMove") is True


def test_remove_last_updates_active_ply() -> None:
    panel = MovePanel()
    panel.set_history([_rec("e4"), _rec("e5")])

    panel.remove_last()
    assert len(panel._records) == 1
    assert panel._active_ply == 0

    panel.remove_last()
    assert len(panel._records) == 0
    assert panel._active_ply is None


def test_add_move_and_clear_cycle() -> None:
    panel = MovePanel()
    panel.add_move(_rec("e4"), move_number=1, color=Color.WHITE)
    assert len(panel._records) == 1
    assert panel._active_ply == 0

    panel.clear()
    assert panel._records == []
    assert panel._move_buttons == {}
    assert panel._active_ply is None


def test_set_use_figurine_notation_noop_when_value_unchanged() -> None:
    panel = MovePanel()
    panel.set_history([_rec("Nf3")])
    first_button = panel._move_buttons[0]

    panel.set_use_figurine_notation(True)

    assert panel._move_buttons[0] is first_button
