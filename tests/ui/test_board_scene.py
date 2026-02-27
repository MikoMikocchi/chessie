"""Tests for BoardScene helpers and promotion move resolution."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QPointF

from chessie.core.enums import MoveFlag, PieceType
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


def test_set_theme_and_interactive_flags() -> None:
    scene = BoardScene()
    original = scene._theme
    scene.set_interactive(False)
    assert scene._interactive is False

    scene.set_theme(original)
    assert scene._theme == original


def test_select_square_builds_legal_dots_and_clear_selection_resets() -> None:
    scene = BoardScene()
    scene.set_position(position_from_fen(STARTING_FEN))

    scene._select_square(parse_square("e2"))
    assert scene._selected_sq == parse_square("e2")
    assert len(scene._legal_dot_items) >= 1

    scene._clear_selection()
    assert scene._selected_sq is None
    assert scene._legal_moves == []
    assert scene._legal_dot_items == []


def test_highlight_check_with_no_position_is_safe() -> None:
    scene = BoardScene()
    scene.highlight_check()
    assert scene._highlight_items == []


def test_find_legal_move_without_position_returns_none() -> None:
    scene = BoardScene()
    assert scene._find_legal_move(parse_square("e2"), parse_square("e4")) is None


def test_pos_to_square_outside_board_returns_none() -> None:
    scene = BoardScene()
    assert scene._pos_to_square(QPointF(-1, -1)) is None


def test_animate_and_sync_uses_animation_path_with_fake_animation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    callbacks: list[object] = []

    class _Signal:
        def connect(self, cb):
            callbacks.append(cb)

    class _FakeAnim:
        def __init__(self, *_args, **_kwargs) -> None:
            self.finished = _Signal()

        def setDuration(self, _v: int) -> None:
            return

        def setStartValue(self, _v: object) -> None:
            return

        def setEndValue(self, _v: object) -> None:
            return

        def setEasingCurve(self, _v: object) -> None:
            return

        def start(self, _policy: object) -> None:
            for cb in callbacks:
                cb()

    monkeypatch.setattr("chessie.ui.board.board_scene.QPropertyAnimation", _FakeAnim)

    scene = BoardScene()
    pos = position_from_fen(STARTING_FEN)
    scene.set_position(pos)
    move = Move(parse_square("e2"), parse_square("e4"), MoveFlag.DOUBLE_PAWN)
    nxt = pos.copy()
    nxt.make_move(move)
    done: list[bool] = []

    scene.animate_and_sync(move, nxt, on_done=lambda: done.append(True))

    assert done == [True]
    assert scene._position is nxt
    assert scene._active_anim is None


def test_animate_and_sync_handles_castling_rook_reposition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    callbacks: list[object] = []

    class _Signal:
        def connect(self, cb):
            callbacks.append(cb)

    class _FakeAnim:
        def __init__(self, *_args, **_kwargs) -> None:
            self.finished = _Signal()

        def setDuration(self, _v: int) -> None:
            return

        def setStartValue(self, _v: object) -> None:
            return

        def setEndValue(self, _v: object) -> None:
            return

        def setEasingCurve(self, _v: object) -> None:
            return

        def start(self, _policy: object) -> None:
            for cb in callbacks:
                cb()

    monkeypatch.setattr("chessie.ui.board.board_scene.QPropertyAnimation", _FakeAnim)

    scene = BoardScene()
    pos = position_from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    scene.set_position(pos)

    move = Move(
        parse_square("e1"),
        parse_square("g1"),
        MoveFlag.CASTLE_KINGSIDE,
    )
    nxt = pos.copy()
    nxt.make_move(move)

    scene.animate_and_sync(move, nxt)

    assert parse_square("f1") in scene._piece_items
    assert parse_square("h1") not in scene._piece_items


def test_animate_and_sync_handles_en_passant_capture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    callbacks: list[object] = []

    class _Signal:
        def connect(self, cb):
            callbacks.append(cb)

    class _FakeAnim:
        def __init__(self, *_args, **_kwargs) -> None:
            self.finished = _Signal()

        def setDuration(self, _v: int) -> None:
            return

        def setStartValue(self, _v: object) -> None:
            return

        def setEndValue(self, _v: object) -> None:
            return

        def setEasingCurve(self, _v: object) -> None:
            return

        def start(self, _policy: object) -> None:
            for cb in callbacks:
                cb()

    monkeypatch.setattr("chessie.ui.board.board_scene.QPropertyAnimation", _FakeAnim)

    scene = BoardScene()
    pos = position_from_fen("7k/8/8/3pP3/8/8/8/K7 w - d6 0 1")
    scene.set_position(pos)

    move = Move(parse_square("e5"), parse_square("d6"), MoveFlag.EN_PASSANT)
    nxt = pos.copy()
    nxt.make_move(move)

    scene.animate_and_sync(move, nxt)

    assert len(scene._piece_items) == 3
