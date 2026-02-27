"""Tests for BoardScene helpers and promotion move resolution."""

from __future__ import annotations

import pytest

from chessie.core.enums import PieceType
from chessie.core.move import Move
from chessie.core.notation import STARTING_FEN, position_from_fen
from chessie.core.types import parse_square
from chessie.ui.board.board_scene import BoardScene


def test_pos_to_square_respects_orientation() -> None:
    scene = BoardScene()
    scene.set_flipped(False)
    assert scene._pos_to_square(scene.sceneRect().topLeft()) == parse_square("a8")

    scene.set_flipped(True)
    assert scene._pos_to_square(scene.sceneRect().topLeft()) == parse_square("h1")


def test_set_show_coordinates_toggles_all_labels_visibility() -> None:
    scene = BoardScene()
    assert scene._coord_items

    scene.set_show_coordinates(False)
    assert all(not item.isVisible() for item in scene._coord_items)

    scene.set_show_coordinates(True)
    assert all(item.isVisible() for item in scene._coord_items)


def test_set_show_legal_moves_false_clears_existing_dots() -> None:
    scene = BoardScene()
    dot = scene._make_highlight(parse_square("e4"), scene._theme.highlight_to)
    scene._legal_dot_items.append(dot)

    scene.set_show_legal_moves(False)

    assert scene._legal_dot_items == []


def test_find_legal_move_promotion_cancel_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scene = BoardScene()
    scene.set_position(position_from_fen("1k6/P7/8/8/8/8/8/K7 w - - 0 1"))

    monkeypatch.setattr(
        "chessie.ui.board.board_scene.PromotionDialog.ask",
        lambda _color, _parent: None,
    )

    move = scene._find_legal_move(parse_square("a7"), parse_square("a8"))
    assert move is None


def test_find_legal_move_promotion_uses_selected_piece(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scene = BoardScene()
    scene.set_position(position_from_fen("1k6/P7/8/8/8/8/8/K7 w - - 0 1"))

    monkeypatch.setattr(
        "chessie.ui.board.board_scene.PromotionDialog.ask",
        lambda _color, _parent: PieceType.KNIGHT,
    )

    move = scene._find_legal_move(parse_square("a7"), parse_square("a8"))
    assert move is not None
    assert move.promotion == PieceType.KNIGHT


def test_find_legal_move_single_and_missing_candidate() -> None:
    scene = BoardScene()
    scene.set_position(position_from_fen(STARTING_FEN))

    assert scene._find_legal_move(parse_square("e2"), parse_square("e4")) is not None
    assert scene._find_legal_move(parse_square("e2"), parse_square("e5")) is None


def test_set_position_syncs_piece_items_count() -> None:
    scene = BoardScene()
    scene.set_position(position_from_fen(STARTING_FEN))
    assert len(scene._piece_items) == 32


def test_highlight_last_move_adds_and_clears() -> None:
    scene = BoardScene()
    scene.highlight_last_move(Move(parse_square("e2"), parse_square("e4")))
    assert len(scene._last_move_highlights) == 2

    scene.highlight_last_move(None)
    assert scene._last_move_highlights == []


def test_highlight_check_marks_king_in_check() -> None:
    scene = BoardScene()
    scene.set_position(position_from_fen("4k3/8/8/8/8/8/4R3/4K3 b - - 0 1"))

    scene.highlight_check()

    assert len(scene._highlight_items) == 1


def test_animate_and_sync_falls_back_when_animation_disabled() -> None:
    scene = BoardScene()
    start = position_from_fen(STARTING_FEN)
    scene.set_position(start)
    scene.set_animate_moves(False)

    move = Move(parse_square("e2"), parse_square("e4"))
    nxt = start.copy()
    nxt.make_move(move)
    done: list[bool] = []

    scene.animate_and_sync(move, nxt, on_done=lambda: done.append(True))

    assert done == [True]
    assert scene._position is nxt


def test_animate_and_sync_with_active_anim_stops_and_syncs() -> None:
    class _Anim:
        def __init__(self) -> None:
            self.stopped = False

        def stop(self) -> None:
            self.stopped = True

    scene = BoardScene()
    start = position_from_fen(STARTING_FEN)
    scene.set_position(start)

    move = Move(parse_square("e2"), parse_square("e4"))
    nxt = start.copy()
    nxt.make_move(move)
    done: list[bool] = []

    anim = _Anim()
    scene._active_anim = anim  # type: ignore[assignment]
    scene.animate_and_sync(move, nxt, on_done=lambda: done.append(True))

    assert anim.stopped is True
    assert scene._active_anim is None
    assert done == [True]
