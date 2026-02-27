"""MainWindow game lifecycle and user interaction handlers."""

from __future__ import annotations

from typing import Any, cast

from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.notation import position_from_fen
from chessie.game.interfaces import IPlayer, TimeControl
from chessie.game.player import HumanPlayer
from chessie.ui.dialogs.new_game_dialog import NewGameDialog
from chessie.ui.i18n import t


def start_default_game(host: Any) -> None:
    """Start a quick human-vs-human unlimited game."""
    host._cancel_ai_search()
    white = HumanPlayer(Color.WHITE, t().color_white)
    black = HumanPlayer(Color.BLACK, t().color_black)
    host._connect_game_events()
    host._controller.new_game(white, black, TimeControl.unlimited())
    host._after_new_game()


def on_new_game_dialog(host: Any) -> None:
    settings = NewGameDialog.ask(host)
    if settings is None:
        return

    white: IPlayer
    black: IPlayer
    if settings.opponent == "human":
        host._cancel_ai_search()
        white = HumanPlayer(Color.WHITE, t().color_white)
        black = HumanPlayer(Color.BLACK, t().color_black)
    else:
        host._cancel_ai_search()
        if settings.player_color == Color.WHITE:
            white = HumanPlayer(Color.WHITE, t().new_game_white)
            black = host._create_ai_player(Color.BLACK)
        else:
            white = host._create_ai_player(Color.WHITE)
            black = HumanPlayer(Color.BLACK, t().new_game_black)

    host._connect_game_events()
    host._controller.new_game(white, black, settings.time_control)
    host._after_new_game()


def on_user_move(host: Any, move: Move) -> None:
    """Handle a move from the board UI."""
    host._history_view_ply = None
    host._controller.submit_move(move)


def on_resign(host: Any, message_box_cls: type[Any]) -> None:
    state = host._controller.state
    if state.is_game_over:
        return

    resigning_color = host._resolve_resign_color()
    reply = message_box_cls.question(
        host,
        t().resign_title,
        t().resign_confirm,
        message_box_cls.StandardButton.Yes | message_box_cls.StandardButton.No,
    )
    if reply == message_box_cls.StandardButton.Yes:
        host._controller.resign(resigning_color)


def on_draw(host: Any, message_box_cls: type[Any]) -> None:
    state = host._controller.state
    if state.is_game_over:
        return

    offering_color = state.side_to_move
    if host._controller.claim_draw(offering_color):
        return

    host._controller.offer_draw(offering_color)

    if host._is_human_vs_human():
        side = t().color_white if offering_color == Color.WHITE else t().color_black
        reply = message_box_cls.question(
            host,
            t().draw_offer_title,
            t().draw_offer_question.format(color=side),
            message_box_cls.StandardButton.Yes | message_box_cls.StandardButton.No,
        )
        if reply == message_box_cls.StandardButton.Yes:
            host._controller.accept_draw(offering_color.opposite)
        else:
            host._controller.decline_draw()
        return

    # MVP policy for AI: always decline human draw offers.
    host._controller.decline_draw()
    host._status_label.setText(t().status_draw_declined)


def on_undo(host: Any) -> None:
    if not host._controller.undo_move():
        return

    state = host._controller.state
    # Human-vs-AI UX: one click should roll back the full turn pair.
    if host._is_human_vs_ai():
        current = host._controller.current_player
        if (
            current is not None
            and not current.is_human
            and state.move_history
            and host._controller.undo_move()
        ):
            state = host._controller.state

    host._board_view.board_scene.set_position(state.position)
    host._board_view.board_scene.highlight_last_move(
        state.move_history[-1].move if state.move_history else None
    )
    host._board_view.board_scene.highlight_check()
    host._move_panel.set_history(state.move_history)
    host._history_view_ply = None
    if len(host._pgn_move_comments) > len(state.move_history):
        host._pgn_move_comments = host._pgn_move_comments[: len(state.move_history)]
    host._sync_board_interactivity()
    host._update_status()


def on_flip(host: Any) -> None:
    scene = host._board_view.board_scene
    scene.set_flipped(not scene.is_flipped())


def on_move_history_selected(host: Any, ply: int) -> None:
    """Jump the board view to the position right after selected *ply*."""
    state = host._controller.state
    history = state.move_history
    if not history or ply < 0 or ply >= len(history):
        return

    last_ply = len(history) - 1
    scene = host._board_view.board_scene

    # Latest ply = live board state; older ply = history preview mode.
    if ply == last_ply:
        host._history_view_ply = None
        scene.set_position(state.position)
        scene.highlight_last_move(history[-1].move)
        scene.highlight_check()
        host._sync_board_interactivity()
        host._update_status()
        return

    preview_pos = position_from_fen(history[ply].fen_after)
    host._history_view_ply = ply
    scene.set_position(preview_pos)
    scene.highlight_last_move(history[ply].move)
    scene.highlight_check()
    scene.set_interactive(False)


def resolve_resign_color(host: Any) -> Color:
    """
    Resolve who is resigning from UI intent.

    Human vs Human: current side to move resigns.
    Human vs AI: human side resigns.
    """
    white_player = host._controller.player(Color.WHITE)
    black_player = host._controller.player(Color.BLACK)
    white_is_human = bool(white_player and white_player.is_human)
    black_is_human = bool(black_player and black_player.is_human)

    if white_is_human and black_is_human:
        return cast(Color, host._controller.state.side_to_move)
    if white_is_human:
        return Color.WHITE
    if black_is_human:
        return Color.BLACK
    return cast(Color, host._controller.state.side_to_move)


def is_human_vs_ai(host: Any) -> bool:
    white_player = host._controller.player(Color.WHITE)
    black_player = host._controller.player(Color.BLACK)
    return bool(
        white_player is not None
        and black_player is not None
        and white_player.is_human != black_player.is_human
    )


def is_human_vs_human(host: Any) -> bool:
    white_player = host._controller.player(Color.WHITE)
    black_player = host._controller.player(Color.BLACK)
    return bool(
        white_player is not None
        and black_player is not None
        and white_player.is_human
        and black_player.is_human
    )
