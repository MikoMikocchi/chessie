"""MainWindow — top-level window assembling all UI components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from chessie.core.enums import Color, GameResult
from chessie.core.move import Move
from chessie.game.controller import GameController
from chessie.game.interfaces import GameEndReason, GamePhase
from chessie.game.player import AIPlayer
from chessie.game.state import GameState
from chessie.ui.analysis_session import AnalysisSession
from chessie.ui.dialogs.settings_dialog import AppSettings, SettingsDialog
from chessie.ui.engine_session import EngineSession
from chessie.ui.game_sync import GameSync
from chessie.ui.main_window_parts import analysis as analysis_part
from chessie.ui.main_window_parts import game as game_part
from chessie.ui.main_window_parts import lifecycle as lifecycle_part
from chessie.ui.main_window_parts import pgn as pgn_part
from chessie.ui.main_window_parts import settings as settings_part
from chessie.ui.main_window_parts import ui as ui_part
from chessie.ui.sounds import SoundPlayer

TCallback = TypeVar("TCallback", bound=Callable[..., None])


class MainWindow(QMainWindow):
    """Main application window for Chessie."""

    engine_request = pyqtSignal(object, int)
    _board_view: Any
    _move_panel: Any
    _eval_bar: Any
    _eval_graph: Any
    _analysis_panel: Any
    _exit_analysis_btn: Any
    _control_panel: Any
    _clock_widget: Any
    _status: Any
    _status_label: Any
    _menu_game: Any
    _menu_settings: Any
    _act_new_game: Any
    _act_open_pgn: Any
    _act_save_pgn: Any
    _act_analyze_game: Any
    _act_flip: Any
    _act_quit: Any
    _act_settings: Any

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Chessie")
        self.setMinimumSize(900, 640)
        self.resize(1100, 750)

        self._controller = GameController()
        self._settings = AppSettings()
        self._sound_player = SoundPlayer()
        self._is_loading_pgn = False
        self._pgn_move_comments: list[str | None] = []
        self._history_view_ply: int | None = None
        self._analysis_report: Any = None
        self._analysis_mode: bool = False

        self._setup_ui()

        def _show_game_over_dialog(text: str) -> None:
            lifecycle_part.show_game_over_dialog(
                self,
                text,
                message_box_cls=QMessageBox,
            )

        self._game_sync = GameSync(
            controller=self._controller,
            board_scene=self._board_view.board_scene,
            move_panel=self._move_panel,
            eval_bar=self._eval_bar,
            control_panel=self._control_panel,
            clock_widget=self._clock_widget,
            sound_player=self._sound_player,
            set_status=self._status_label.setText,
            show_game_over_dialog=_show_game_over_dialog,
        )
        self._engine_session = EngineSession(
            controller=self._controller,
            engine_request=self.engine_request,
            set_eval=self._eval_bar.set_eval,
            set_status=self._status_label.setText,
            sync_board_interactivity=self._sync_board_interactivity,
            parent=self,
            max_depth=4,
            time_limit_ms=900,
        )
        self._analysis_session = AnalysisSession(
            on_progress=self._on_analysis_progress,
            on_finished=self._on_analysis_finished,
            on_failed=self._on_analysis_failed,
            on_cancelled=self._on_analysis_cancelled,
            parent=self,
        )
        self._setup_menu()
        self._connect_signals()
        self._connect_game_events()
        self._setup_engine()

        # Start with a default game
        self._start_default_game()

    # ── UI setup ─────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        ui_part.setup_ui(self)

    def _setup_menu(self) -> None:
        ui_part.setup_menu(self)

    # ── Signal wiring ────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        lifecycle_part.connect_signals(self)

    def _setup_engine(self) -> None:
        lifecycle_part.setup_engine(self)

    def _connect_game_events(self) -> None:
        lifecycle_part.connect_game_events(self)

    def _disconnect_game_events(self) -> None:
        lifecycle_part.disconnect_game_events(self)

    @staticmethod
    def _replace_callback(
        callbacks: list[TCallback],
        callback: TCallback,
    ) -> None:
        callbacks[:] = [cb for cb in callbacks if cb != callback]
        callbacks.append(callback)

    @staticmethod
    def _remove_callback(callbacks: list[TCallback], callback: TCallback) -> None:
        callbacks[:] = [cb for cb in callbacks if cb != callback]

    # ── Game lifecycle ───────────────────────────────────────────────────

    def _start_default_game(self) -> None:
        game_part.start_default_game(self)

    def _on_new_game_dialog(self) -> None:
        game_part.on_new_game_dialog(self)

    def _on_open_pgn(self) -> None:
        pgn_part.on_open_pgn(
            self,
            file_dialog_cls=QFileDialog,
            message_box_cls=QMessageBox,
        )

    def _on_save_pgn(self) -> None:
        pgn_part.on_save_pgn(
            self,
            file_dialog_cls=QFileDialog,
            message_box_cls=QMessageBox,
        )

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._disconnect_game_events()
        self._analysis_session.shutdown()
        self._engine_session.shutdown()
        super().closeEvent(event)

    def _after_new_game(self) -> None:
        lifecycle_part.after_new_game(self)

    # ── User actions ─────────────────────────────────────────────────────

    def _on_user_move(self, move: Move) -> None:
        game_part.on_user_move(self, move)

    def _on_resign(self) -> None:
        game_part.on_resign(self, message_box_cls=QMessageBox)

    def _on_draw(self) -> None:
        game_part.on_draw(self, message_box_cls=QMessageBox)

    def _on_undo(self) -> None:
        game_part.on_undo(self)

    def _on_flip(self) -> None:
        game_part.on_flip(self)

    def _on_analyze_game(self) -> None:
        analysis_part.on_analyze_game(self, message_box_cls=QMessageBox)

    def _on_exit_analysis(self) -> None:
        analysis_part.on_exit_analysis(self)

    def _on_analysis_ply_selected(self, ply: int) -> None:
        analysis_part.on_analysis_ply_selected(self, ply)

    def _on_move_history_selected(self, ply: int) -> None:
        game_part.on_move_history_selected(self, ply)

    def _on_settings(self) -> None:
        settings_part.on_settings(self, settings_dialog_cls=SettingsDialog)

    def _apply_settings(self) -> None:
        settings_part.apply_settings(self)

    def retranslate_ui(self) -> None:
        ui_part.retranslate_ui(self)

    # ── Game event callbacks ─────────────────────────────────────────────

    def _on_game_move(self, move: Move, _san: str, state: GameState) -> None:
        lifecycle_part.on_game_move(self, move, state)

    def _on_game_over(self, result: GameResult) -> None:
        lifecycle_part.on_game_over(self, result)

    def _on_phase_changed(self, phase: GamePhase) -> None:
        lifecycle_part.on_phase_changed(self, phase)

    # ── Analysis callbacks ────────────────────────────────────────────────

    def _on_analysis_progress(self, done: int, total: int) -> None:
        analysis_part.on_analysis_progress(self, done, total)

    def _on_analysis_finished(self, report: Any) -> None:
        analysis_part.on_analysis_finished(
            self,
            report,
        )

    def _on_analysis_failed(self, message: str) -> None:
        analysis_part.on_analysis_failed(self, message)

    def _on_analysis_cancelled(self) -> None:
        analysis_part.on_analysis_cancelled(self)

    # ── Engine callbacks ──────────────────────────────────────────────────

    def _create_ai_player(self, color: Color) -> AIPlayer:
        return lifecycle_part.create_ai_player(self, color)

    def _cancel_ai_search(self) -> None:
        lifecycle_part.cancel_ai_search(self)

    # ── Helpers ──────────────────────────────────────────────────────────

    def _sync_board_interactivity(self) -> None:
        if self._history_view_ply is not None:
            self._board_view.board_scene.set_interactive(False)
            return
        lifecycle_part.sync_board_interactivity(self)

    @staticmethod
    def _termination_from_end_reason(reason: GameEndReason) -> str:
        return pgn_part.termination_from_end_reason(reason)

    @staticmethod
    def _end_reason_from_termination(termination: str | None) -> GameEndReason:
        return pgn_part.end_reason_from_termination(termination)

    def _update_status(self) -> None:
        lifecycle_part.update_status(self)

    def _resolve_resign_color(self) -> Color:
        return game_part.resolve_resign_color(self)

    def _is_human_vs_ai(self) -> bool:
        return game_part.is_human_vs_ai(self)

    def _is_human_vs_human(self) -> bool:
        return game_part.is_human_vs_human(self)
