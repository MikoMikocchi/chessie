"""MainWindow lifecycle, callbacks, and synchronization helpers."""

from __future__ import annotations

from typing import Any, cast

from chessie.core.enums import Color, GameResult
from chessie.core.move import Move
from chessie.game.interfaces import GamePhase
from chessie.game.player import AIPlayer
from chessie.game.state import GameState
from chessie.ui.i18n import t


def connect_signals(host: Any) -> None:
    """Connect Qt widget signals."""
    host._board_view.move_made.connect(host._on_user_move)
    host._move_panel.move_clicked.connect(host._on_move_history_selected)
    host._control_panel.new_game_clicked.connect(host._on_new_game_dialog)
    host._control_panel.resign_clicked.connect(host._on_resign)
    host._control_panel.draw_clicked.connect(host._on_draw)
    host._control_panel.undo_clicked.connect(host._on_undo)
    host._control_panel.flip_clicked.connect(host._on_flip)


def setup_engine(host: Any) -> None:
    """Set up engine worker session in a dedicated QThread."""
    host._engine_session.setup()


def connect_game_events(host: Any) -> None:
    """Subscribe to GameController callbacks (idempotent)."""
    events = host._controller.events
    host._replace_callback(events.on_move, host._on_game_move)
    host._replace_callback(events.on_game_over, host._on_game_over)
    host._replace_callback(events.on_phase_changed, host._on_phase_changed)


def disconnect_game_events(host: Any) -> None:
    """Detach this window from GameController callbacks."""
    events = host._controller.events
    host._remove_callback(events.on_move, host._on_game_move)
    host._remove_callback(events.on_game_over, host._on_game_over)
    host._remove_callback(events.on_phase_changed, host._on_phase_changed)


def after_new_game(host: Any) -> None:
    """Reset auxiliary UI state after creating a new game."""
    # Exit analysis mode if active
    if getattr(host, "_analysis_mode", False):
        from chessie.ui.main_window_parts import analysis as analysis_part

        analysis_part.on_exit_analysis(host)

    host._analysis_session.cancel_analysis()
    host._analysis_report = None
    host._act_analyze_game.setEnabled(True)
    host._pgn_move_comments = []
    host._history_view_ply = None
    host._game_sync.after_new_game()


def on_game_move(host: Any, move: Move, state: GameState) -> None:
    """Handle post-move synchronization for both human and AI moves."""
    host._history_view_ply = None
    host._pgn_move_comments = host._game_sync.on_game_move(
        move,
        state,
        pgn_move_comments=host._pgn_move_comments,
        is_loading_pgn=host._is_loading_pgn,
    )


def on_game_over(host: Any, result: GameResult) -> None:
    host._game_sync.on_game_over(result, is_loading_pgn=host._is_loading_pgn)


def on_phase_changed(host: Any, phase: GamePhase) -> None:
    host._game_sync.on_phase_changed(phase)


def create_ai_player(host: Any, color: Color) -> AIPlayer:
    return cast(AIPlayer, host._engine_session.create_ai_player(color))


def cancel_ai_search(host: Any) -> None:
    host._engine_session.cancel_ai_search()


def sync_board_interactivity(host: Any) -> None:
    host._game_sync.sync_board_interactivity()


def update_status(host: Any) -> None:
    host._game_sync.update_status()


def show_game_over_dialog(host: Any, text: str, message_box_cls: type[Any]) -> None:
    message_box_cls.information(host, t().game_over_title, text)
