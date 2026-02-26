"""UI/game state synchronisation helpers for MainWindow."""

from __future__ import annotations

from collections.abc import Callable

from chessie.core.enums import Color, GameResult
from chessie.core.move import Move
from chessie.game.controller import GameController
from chessie.game.interfaces import GameEndReason, GamePhase
from chessie.game.state import GameState
from chessie.ui.board.board_scene import BoardScene
from chessie.ui.i18n import t
from chessie.ui.panels.clock_widget import ClockWidget
from chessie.ui.panels.control_panel import ControlPanel
from chessie.ui.panels.eval_bar import EvalBar
from chessie.ui.panels.move_panel import MovePanel
from chessie.ui.sounds import SoundPlayer


class GameSync:
    """Applies game-state changes to UI widgets."""

    __slots__ = (
        "_controller",
        "_board_scene",
        "_move_panel",
        "_eval_bar",
        "_control_panel",
        "_clock_widget",
        "_sound_player",
        "_set_status",
        "_show_game_over_dialog",
    )

    def __init__(
        self,
        *,
        controller: GameController,
        board_scene: BoardScene,
        move_panel: MovePanel,
        eval_bar: EvalBar,
        control_panel: ControlPanel,
        clock_widget: ClockWidget,
        sound_player: SoundPlayer,
        set_status: Callable[[str], None],
        show_game_over_dialog: Callable[[str], None],
    ) -> None:
        self._controller = controller
        self._board_scene = board_scene
        self._move_panel = move_panel
        self._eval_bar = eval_bar
        self._control_panel = control_panel
        self._clock_widget = clock_widget
        self._sound_player = sound_player
        self._set_status = set_status
        self._show_game_over_dialog = show_game_over_dialog

    def after_new_game(self) -> None:
        """Sync UI state after a new game starts."""
        state = self._controller.state
        self._board_scene.set_position(state.position)
        self._move_panel.clear()
        self._eval_bar.reset()
        self._control_panel.set_game_active(True)

        clock = self._controller.clock
        if clock is not None and not clock.is_unlimited:
            self._clock_widget.reset(clock.remaining(Color.WHITE))
            self._clock_widget.set_active(state.side_to_move)
            self._clock_widget.start(
                lambda: (
                    clock.remaining(Color.WHITE),
                    clock.remaining(Color.BLACK),
                )
            )
        else:
            self._clock_widget.reset(0)

        self.sync_board_interactivity()
        self.update_status()

    def on_game_move(
        self,
        move: Move,
        state: GameState,
        *,
        pgn_move_comments: list[str | None],
        is_loading_pgn: bool,
    ) -> list[str | None]:
        """Sync UI after a move and return updated PGN comments list."""
        comments = pgn_move_comments
        if len(comments) < len(state.move_history):
            comments.append(None)
        elif len(comments) > len(state.move_history):
            comments = comments[: len(state.move_history)]

        if state.move_history and not is_loading_pgn:
            self._sound_player.play_move_sound(state.move_history[-1], state)

        self._board_scene.set_position(state.position)
        self._board_scene.highlight_last_move(move)
        self._board_scene.highlight_check()

        record = state.move_history[-1]
        ply = len(state.move_history) - 1
        move_num = ply // 2 + 1
        color = Color.WHITE if ply % 2 == 0 else Color.BLACK
        self._move_panel.add_move(record, move_num, color)

        if self._controller.clock and not self._controller.clock.is_unlimited:
            self._clock_widget.set_active(state.side_to_move)

        self.sync_board_interactivity()
        self.update_status()
        return comments

    def on_game_over(self, result: GameResult, *, is_loading_pgn: bool) -> None:
        """Sync UI when the game reaches a terminal state."""
        self._clock_widget.stop()
        self._board_scene.set_interactive(False)
        self._control_panel.set_game_active(False)
        text = self._game_over_text(result)
        self._set_status(f"{t().status_game_over}{text}")
        if not is_loading_pgn:
            self._show_game_over_dialog(text)

    def on_phase_changed(self, _phase: GamePhase) -> None:
        """Sync UI after a phase transition."""
        self.sync_board_interactivity()
        self.update_status()

    def sync_board_interactivity(self) -> None:
        """Enable board input only when current player is human."""
        state = self._controller.state
        if state.is_game_over:
            self._board_scene.set_interactive(False)
            return

        current = self._controller.current_player
        interactive = current is not None and current.is_human
        self._board_scene.set_interactive(interactive)

    def update_status(self) -> None:
        """Update the status line from current state."""
        state = self._controller.state
        if state.is_game_over:
            return

        s = t()
        side = s.color_white if state.side_to_move == Color.WHITE else s.color_black
        phase_map = {
            "NOT_STARTED": s.phase_not_started,
            "AWAITING_MOVE": s.phase_awaiting_move,
            "THINKING": s.phase_thinking,
            "GAME_OVER": s.phase_game_over,
        }
        phase = phase_map.get(
            state.phase.name,
            state.phase.name.replace("_", " ").capitalize(),
        )
        self._set_status(f"{side} | {phase} | {state.fullmove_display}")

    def _game_over_text(self, result: GameResult) -> str:
        reason = self._controller.state.end_reason
        s = t()

        if result == GameResult.DRAW:
            if reason == GameEndReason.STALEMATE:
                return s.draw_stalemate
            if reason == GameEndReason.DRAW_AGREED:
                return s.draw_agreed
            if reason == GameEndReason.DRAW_RULE:
                return s.draw_rule
            return s.draw_generic

        winner = s.color_white if result == GameResult.WHITE_WINS else s.color_black
        if reason == GameEndReason.CHECKMATE:
            return s.wins_checkmate.format(color=winner)
        if reason == GameEndReason.RESIGN:
            return s.wins_resign.format(color=winner)
        if reason == GameEndReason.FLAG_FALL:
            return s.wins_time.format(color=winner)
        return s.wins_generic.format(color=winner)
