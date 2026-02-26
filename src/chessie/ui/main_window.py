"""MainWindow — top-level window assembling all UI components."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from chessie.core.enums import Color, GameResult
from chessie.core.move import Move
from chessie.core.notation import (
    STARTING_FEN,
    build_pgn,
    game_result_from_pgn,
    parse_pgn_game,
    parse_san,
    pgn_result_token,
    position_to_fen,
)
from chessie.engine import EngineWorker
from chessie.game.controller import GameController
from chessie.game.interfaces import GameEndReason, GamePhase, IPlayer, TimeControl
from chessie.game.player import AIPlayer, HumanPlayer
from chessie.game.state import GameState
from chessie.ui.board.board_view import BoardView
from chessie.ui.dialogs.new_game_dialog import NewGameDialog
from chessie.ui.dialogs.settings_dialog import AppSettings, SettingsDialog
from chessie.ui.i18n import set_language, t
from chessie.ui.panels.clock_widget import ClockWidget
from chessie.ui.panels.control_panel import ControlPanel
from chessie.ui.panels.eval_bar import EvalBar
from chessie.ui.panels.move_panel import MovePanel
from chessie.ui.sounds import SoundPlayer
from chessie.ui.styles.theme import BoardTheme

if TYPE_CHECKING:
    from chessie.core.position import Position

TCallback = TypeVar("TCallback", bound=Callable[..., None])


class MainWindow(QMainWindow):
    """Main application window for Chessie."""

    engine_request = pyqtSignal(object, int)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Chessie")
        self.setMinimumSize(900, 640)
        self.resize(1100, 750)

        self._controller = GameController()
        self._settings = AppSettings()
        self._sound_player = SoundPlayer()
        self._engine_thread = QThread(self)
        self._engine_worker = EngineWorker(max_depth=4, time_limit_ms=900)
        self._engine_request_id = 0
        self._pending_engine_request: int | None = None
        self._pending_engine_fen: str | None = None
        self._is_loading_pgn = False
        self._pgn_move_comments: list[str | None] = []

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        self._connect_game_events()
        self._setup_engine()

        # Start with a default game
        self._start_default_game()

    # ── UI setup ─────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # Eval bar (left)
        self._eval_bar = EvalBar()
        root.addWidget(self._eval_bar)

        # Board (center)
        self._board_view = BoardView()
        root.addWidget(self._board_view, stretch=3)

        # Right panel
        right = QVBoxLayout()
        right.setSpacing(6)

        self._clock_widget = ClockWidget()
        right.addWidget(self._clock_widget)

        self._move_panel = MovePanel()
        right.addWidget(self._move_panel, stretch=1)

        self._control_panel = ControlPanel()
        right.addWidget(self._control_panel)

        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(280)
        root.addWidget(right_widget)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel(t().status_ready)
        self._status.addWidget(self._status_label)

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()
        assert menu_bar is not None
        s = t()

        # Game menu
        self._menu_game = menu_bar.addMenu(s.menu_game)
        assert self._menu_game is not None

        self._act_new_game = QAction(s.menu_new_game, self)
        self._act_new_game.setShortcut("Ctrl+N")
        self._act_new_game.triggered.connect(self._on_new_game_dialog)
        self._menu_game.addAction(self._act_new_game)

        self._act_open_pgn = QAction(s.menu_open_pgn, self)
        self._act_open_pgn.setShortcut("Ctrl+O")
        self._act_open_pgn.triggered.connect(self._on_open_pgn)
        self._menu_game.addAction(self._act_open_pgn)

        self._act_save_pgn = QAction(s.menu_save_pgn, self)
        self._act_save_pgn.setShortcut("Ctrl+S")
        self._act_save_pgn.triggered.connect(self._on_save_pgn)
        self._menu_game.addAction(self._act_save_pgn)

        self._menu_game.addSeparator()

        self._act_flip = QAction(s.menu_flip_board, self)
        self._act_flip.setShortcut("F")
        self._act_flip.triggered.connect(self._on_flip)
        self._menu_game.addAction(self._act_flip)

        self._menu_game.addSeparator()

        self._act_quit = QAction(s.menu_quit, self)
        self._act_quit.setShortcut("Ctrl+Q")
        self._act_quit.triggered.connect(self.close)
        self._menu_game.addAction(self._act_quit)

        # Settings menu
        self._menu_settings = menu_bar.addMenu(s.menu_settings)
        assert self._menu_settings is not None

        self._act_settings = QAction(s.menu_settings_action, self)
        self._act_settings.setShortcut("Ctrl+,")
        self._act_settings.triggered.connect(self._on_settings)
        self._menu_settings.addAction(self._act_settings)

    # ── Signal wiring ────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect Qt widget signals."""
        self._board_view.move_made.connect(self._on_user_move)
        self._control_panel.new_game_clicked.connect(self._on_new_game_dialog)
        self._control_panel.resign_clicked.connect(self._on_resign)
        self._control_panel.draw_clicked.connect(self._on_draw)
        self._control_panel.undo_clicked.connect(self._on_undo)
        self._control_panel.flip_clicked.connect(self._on_flip)

    def _setup_engine(self) -> None:
        """Set up engine worker in a dedicated QThread."""
        self._engine_worker.moveToThread(self._engine_thread)
        self.engine_request.connect(self._engine_worker.request_move)
        self._engine_worker.best_move_ready.connect(self._on_engine_best_move)
        self._engine_worker.search_cancelled.connect(self._on_engine_cancelled)
        self._engine_worker.search_error.connect(self._on_engine_error)
        self._engine_thread.start()

    def _connect_game_events(self) -> None:
        """Subscribe to GameController callbacks (idempotent)."""
        events = self._controller.events
        self._replace_callback(events.on_move, self._on_game_move)
        self._replace_callback(events.on_game_over, self._on_game_over)
        self._replace_callback(events.on_phase_changed, self._on_phase_changed)

    def _disconnect_game_events(self) -> None:
        """Detach this window from GameController callbacks."""
        events = self._controller.events
        self._remove_callback(events.on_move, self._on_game_move)
        self._remove_callback(events.on_game_over, self._on_game_over)
        self._remove_callback(events.on_phase_changed, self._on_phase_changed)

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
        """Start a quick human-vs-human unlimited game."""
        self._cancel_ai_search()
        white = HumanPlayer(Color.WHITE, t().color_white)
        black = HumanPlayer(Color.BLACK, t().color_black)
        self._connect_game_events()
        self._controller.new_game(white, black, TimeControl.unlimited())
        self._after_new_game()

    def _on_new_game_dialog(self) -> None:
        settings = NewGameDialog.ask(self)
        if settings is None:
            return

        white: IPlayer
        black: IPlayer
        if settings.opponent == "human":
            self._cancel_ai_search()
            white = HumanPlayer(Color.WHITE, t().color_white)
            black = HumanPlayer(Color.BLACK, t().color_black)
        else:
            self._cancel_ai_search()
            if settings.player_color == Color.WHITE:
                white = HumanPlayer(Color.WHITE, t().new_game_white)
                black = self._create_ai_player(Color.BLACK)
            else:
                white = self._create_ai_player(Color.WHITE)
                black = HumanPlayer(Color.BLACK, t().new_game_black)

        self._connect_game_events()
        self._controller.new_game(white, black, settings.time_control)
        self._after_new_game()

    def _on_open_pgn(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t().open_pgn_title,
            "",
            f"{t().pgn_filter};;{t().pgn_all_files}",
        )
        if not file_path:
            return

        try:
            pgn_text = Path(file_path).read_text(encoding="utf-8")
            parsed = parse_pgn_game(pgn_text)
            headers = parsed.headers
            result_token = parsed.result_token

            start_fen = STARTING_FEN
            if headers.get("SetUp") == "1" and "FEN" in headers:
                start_fen = headers["FEN"]

            self._cancel_ai_search()
            white = HumanPlayer(Color.WHITE, headers.get("White", "White"))
            black = HumanPlayer(Color.BLACK, headers.get("Black", "Black"))

            self._connect_game_events()
            self._controller.new_game(
                white=white,
                black=black,
                time_control=TimeControl.unlimited(),
                fen=start_fen,
            )
            self._after_new_game()

            self._is_loading_pgn = True
            try:
                for pgn_move in parsed.moves:
                    move = parse_san(self._controller.state.position, pgn_move.san)
                    if not self._controller.submit_move(move):
                        raise ValueError(f"Illegal move in PGN: {pgn_move.san}")

                self._pgn_move_comments = [
                    pgn_move.comment or None for pgn_move in parsed.moves
                ]

                declared_result = game_result_from_pgn(result_token)
                if (
                    declared_result != GameResult.IN_PROGRESS
                    and not self._controller.state.is_game_over
                ):
                    state = self._controller.state
                    state.result = declared_result
                    state.phase = GamePhase.GAME_OVER
                    state.end_reason = self._end_reason_from_termination(
                        headers.get("Termination")
                    )
                    self._on_game_over(declared_result)
            finally:
                self._is_loading_pgn = False

            self._sync_board_interactivity()
            self._update_status()
            self._status_label.setText(t().status_loaded_pgn.format(name=Path(file_path).name))
        except Exception as exc:
            self._is_loading_pgn = False
            QMessageBox.warning(self, t().open_pgn_title, t().open_pgn_failed.format(exc=exc))

    def _on_save_pgn(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t().save_pgn_title,
            "game.pgn",
            f"{t().pgn_filter};;{t().pgn_all_files}",
        )
        if not file_path:
            return

        try:
            save_path = Path(file_path)
            if save_path.suffix.lower() != ".pgn":
                save_path = save_path.with_suffix(".pgn")

            state = self._controller.state
            white_player = self._controller.player(Color.WHITE)
            black_player = self._controller.player(Color.BLACK)
            result_token = pgn_result_token(state.result)

            headers: dict[str, str] = {
                "Event": "Casual Game",
                "Site": "Chessie",
                "Date": datetime.now().strftime("%Y.%m.%d"),
                "Round": "-",
                "White": white_player.name if white_player is not None else "White",
                "Black": black_player.name if black_player is not None else "Black",
                "Result": result_token,
                "Termination": self._termination_from_end_reason(state.end_reason),
            }
            if state.start_fen != STARTING_FEN:
                headers["SetUp"] = "1"
                headers["FEN"] = state.start_fen

            comments = self._pgn_move_comments[: len(state.move_history)]
            if len(comments) < len(state.move_history):
                comments += [None] * (len(state.move_history) - len(comments))

            pgn_text = build_pgn(
                headers=headers,
                sans=[record.san for record in state.move_history],
                result_token=result_token,
                comments=comments,
            )
            save_path.write_text(pgn_text, encoding="utf-8")
            self._status_label.setText(t().status_saved_pgn.format(name=save_path.name))
        except Exception as exc:
            QMessageBox.warning(self, t().save_pgn_title, t().save_pgn_failed.format(exc=exc))

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._cancel_ai_search()
        self._disconnect_game_events()
        self._engine_thread.quit()
        self._engine_thread.wait(2000)
        super().closeEvent(event)

    def _after_new_game(self) -> None:
        """Sync UI after a new game starts."""
        state = self._controller.state
        self._pgn_move_comments = []
        self._board_view.board_scene.set_position(state.position)
        self._move_panel.clear()
        self._eval_bar.reset()
        self._control_panel.set_game_active(True)

        # Clock
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

        self._sync_board_interactivity()
        self._update_status()

    # ── User actions ─────────────────────────────────────────────────────

    def _on_user_move(self, move: Move) -> None:
        """Handle a move from the board UI."""
        self._controller.submit_move(move)

    def _on_resign(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            return
        resigning_color = self._resolve_resign_color()
        reply = QMessageBox.question(
            self,
            t().resign_title,
            t().resign_confirm,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._controller.resign(resigning_color)

    def _on_draw(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            return
        offering_color = state.side_to_move
        self._controller.offer_draw(offering_color)

        if self._is_human_vs_human():
            side = t().color_white if offering_color == Color.WHITE else t().color_black
            reply = QMessageBox.question(
                self,
                t().draw_offer_title,
                t().draw_offer_question.format(color=side),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._controller.accept_draw(offering_color.opposite)
            else:
                self._controller.decline_draw()
            return

        # MVP policy for AI: always decline human draw offers.
        self._controller.decline_draw()
        self._status_label.setText(t().status_draw_declined)

    def _on_undo(self) -> None:
        if not self._controller.undo_move():
            return

        state = self._controller.state
        # Human-vs-AI UX: one click should roll back the full turn pair.
        if self._is_human_vs_ai():
            current = self._controller.current_player
            if (
                current is not None
                and not current.is_human
                and state.move_history
                and self._controller.undo_move()
            ):
                state = self._controller.state

        self._board_view.board_scene.set_position(state.position)
        self._board_view.board_scene.highlight_last_move(
            state.move_history[-1].move if state.move_history else None
        )
        self._board_view.board_scene.highlight_check()
        self._move_panel.set_history(state.move_history)
        if len(self._pgn_move_comments) > len(state.move_history):
            self._pgn_move_comments = self._pgn_move_comments[: len(state.move_history)]
        self._sync_board_interactivity()
        self._update_status()

    def _on_flip(self) -> None:
        scene = self._board_view.board_scene
        scene.set_flipped(not scene.is_flipped())

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec():
            self._apply_settings()

    def _apply_settings(self) -> None:
        s = self._settings

        # Language must come first so all retranslate calls use the new locale
        set_language(s.language)
        self.retranslate_ui()

        scene = self._board_view.board_scene

        # Board
        theme_map = {
            "Classic": BoardTheme.default(),
            "Blue": BoardTheme.blue(),
        }
        scene.set_theme(theme_map.get(s.board_theme, BoardTheme.default()))
        scene.set_show_coordinates(s.show_coordinates)
        scene.set_show_legal_moves(s.show_legal_moves)

        # Sound
        self._sound_player.set_enabled(s.sound_enabled)
        self._sound_player.set_volume(s.sound_volume)

        # Engine (applied to subsequent searches; doesn't interrupt current)
        self._engine_worker.set_limits(s.engine_depth, s.engine_time_ms)

    def retranslate_ui(self) -> None:
        """Update all translatable strings when the locale changes."""
        s = t()
        # Menu bar
        self._menu_game.setTitle(s.menu_game)
        self._act_new_game.setText(s.menu_new_game)
        self._act_open_pgn.setText(s.menu_open_pgn)
        self._act_save_pgn.setText(s.menu_save_pgn)
        self._act_flip.setText(s.menu_flip_board)
        self._act_quit.setText(s.menu_quit)
        self._menu_settings.setTitle(s.menu_settings)
        self._act_settings.setText(s.menu_settings_action)
        # Child widgets
        self._move_panel.retranslate_ui()
        self._control_panel.retranslate_ui()
        self._clock_widget.retranslate_ui()
        self._update_status()

    # ── Game event callbacks ─────────────────────────────────────────────

    def _on_game_move(self, move: Move, _san: str, state: GameState) -> None:
        """Called after every move (both human and AI)."""
        if len(self._pgn_move_comments) < len(state.move_history):
            self._pgn_move_comments.append(None)
        elif len(self._pgn_move_comments) > len(state.move_history):
            self._pgn_move_comments = self._pgn_move_comments[: len(state.move_history)]

        if state.move_history and not self._is_loading_pgn:
            self._sound_player.play_move_sound(state.move_history[-1], state)

        self._board_view.board_scene.set_position(state.position)
        self._board_view.board_scene.highlight_last_move(move)
        self._board_view.board_scene.highlight_check()

        record = state.move_history[-1]
        ply = len(state.move_history) - 1
        move_num = ply // 2 + 1
        color = Color.WHITE if ply % 2 == 0 else Color.BLACK
        self._move_panel.add_move(record, move_num, color)

        # Update clock display
        if self._controller.clock and not self._controller.clock.is_unlimited:
            self._clock_widget.set_active(state.side_to_move)

        self._sync_board_interactivity()
        self._update_status()

    def _on_game_over(self, result: GameResult) -> None:
        self._clock_widget.stop()
        self._board_view.board_scene.set_interactive(False)
        self._control_panel.set_game_active(False)
        text = self._game_over_text(result)
        self._status_label.setText(f"{t().status_game_over}{text}")
        if not self._is_loading_pgn:
            QMessageBox.information(self, t().game_over_title, text)

    def _on_phase_changed(self, _phase: GamePhase) -> None:
        self._sync_board_interactivity()
        self._update_status()

    # ── Engine callbacks ──────────────────────────────────────────────────

    def _create_ai_player(self, color: Color) -> AIPlayer:
        return AIPlayer(
            color,
            "Chessie AI",
            on_request_move=self._request_ai_move,
            on_cancel=self._cancel_ai_search,
        )

    def _request_ai_move(self, position: Position) -> None:
        self._cancel_ai_search()
        self._engine_request_id += 1
        request_id = self._engine_request_id

        self._pending_engine_request = request_id
        self._pending_engine_fen = position_to_fen(position)
        self.engine_request.emit(position.copy(), request_id)

    def _cancel_ai_search(self) -> None:
        self._pending_engine_request = None
        self._pending_engine_fen = None
        self._engine_worker.cancel()

    def _on_engine_best_move(
        self,
        request_id: int,
        move_obj: object,
        score_cp: int,
        _depth: int,
        _nodes: int,
    ) -> None:
        if request_id != self._pending_engine_request:
            return
        if not isinstance(move_obj, Move):
            return

        state = self._controller.state
        if state.phase != GamePhase.THINKING:
            return
        if self._pending_engine_fen != position_to_fen(state.position):
            return

        # Eval bar is white-centric; engine score is side-to-move-centric.
        white_cp = score_cp if state.side_to_move == Color.WHITE else -score_cp

        self._pending_engine_request = None
        self._pending_engine_fen = None
        ok = self._controller.submit_move(move_obj)
        if ok:
            self._eval_bar.set_eval(float(white_cp))
        self._sync_board_interactivity()

    def _on_engine_error(self, request_id: int, message: str) -> None:
        if request_id != self._pending_engine_request:
            return
        self._pending_engine_request = None
        self._pending_engine_fen = None

        state = self._controller.state
        if state.phase != GamePhase.THINKING:
            return

        legal = state.legal_moves()
        if legal:
            self._controller.submit_move(legal[0])
            return

        self._status_label.setText(t().status_engine_error.format(msg=message))
        self._sync_board_interactivity()

    def _on_engine_cancelled(self, request_id: int) -> None:
        if request_id != self._pending_engine_request:
            return
        self._pending_engine_request = None
        self._pending_engine_fen = None
        self._sync_board_interactivity()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _sync_board_interactivity(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            self._board_view.board_scene.set_interactive(False)
            return

        current = self._controller.current_player
        interactive = current is not None and current.is_human
        self._board_view.board_scene.set_interactive(interactive)

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

    @staticmethod
    def _termination_from_end_reason(reason: GameEndReason) -> str:
        mapping = {
            GameEndReason.NONE: "unterminated",
            GameEndReason.CHECKMATE: "checkmate",
            GameEndReason.STALEMATE: "stalemate",
            GameEndReason.RESIGN: "resignation",
            GameEndReason.FLAG_FALL: "time forfeit",
            GameEndReason.DRAW_AGREED: "draw agreed",
            GameEndReason.DRAW_RULE: "draw rule",
        }
        return mapping.get(reason, "unterminated")

    @staticmethod
    def _end_reason_from_termination(termination: str | None) -> GameEndReason:
        if termination is None:
            return GameEndReason.NONE

        normalized = " ".join(
            termination.strip().lower().replace("_", " ").replace("-", " ").split()
        )
        mapping = {
            "checkmate": GameEndReason.CHECKMATE,
            "mate": GameEndReason.CHECKMATE,
            "stalemate": GameEndReason.STALEMATE,
            "resign": GameEndReason.RESIGN,
            "resigned": GameEndReason.RESIGN,
            "resignation": GameEndReason.RESIGN,
            "time forfeit": GameEndReason.FLAG_FALL,
            "flag fall": GameEndReason.FLAG_FALL,
            "time": GameEndReason.FLAG_FALL,
            "draw agreed": GameEndReason.DRAW_AGREED,
            "draw agreement": GameEndReason.DRAW_AGREED,
            "agreement": GameEndReason.DRAW_AGREED,
            "draw rule": GameEndReason.DRAW_RULE,
            "threefold repetition": GameEndReason.DRAW_RULE,
            "fivefold repetition": GameEndReason.DRAW_RULE,
            "50 move rule": GameEndReason.DRAW_RULE,
            "75 move rule": GameEndReason.DRAW_RULE,
            "insufficient material": GameEndReason.DRAW_RULE,
            "unterminated": GameEndReason.NONE,
            "normal": GameEndReason.NONE,
        }
        return mapping.get(normalized, GameEndReason.NONE)

    def _update_status(self) -> None:
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
        phase = phase_map.get(state.phase.name, state.phase.name.replace("_", " ").capitalize())
        self._status_label.setText(f"{side} | {phase} | {state.fullmove_display}")

    def _resolve_resign_color(self) -> Color:
        """
        Resolve who is resigning from UI intent.

        Human vs Human: current side to move resigns.
        Human vs AI: human side resigns.
        """
        white_player = self._controller.player(Color.WHITE)
        black_player = self._controller.player(Color.BLACK)
        white_is_human = bool(white_player and white_player.is_human)
        black_is_human = bool(black_player and black_player.is_human)

        if white_is_human and black_is_human:
            return self._controller.state.side_to_move
        if white_is_human:
            return Color.WHITE
        if black_is_human:
            return Color.BLACK
        return self._controller.state.side_to_move

    def _is_human_vs_ai(self) -> bool:
        white_player = self._controller.player(Color.WHITE)
        black_player = self._controller.player(Color.BLACK)
        return bool(
            white_player is not None
            and black_player is not None
            and white_player.is_human != black_player.is_human
        )

    def _is_human_vs_human(self) -> bool:
        white_player = self._controller.player(Color.WHITE)
        black_player = self._controller.player(Color.BLACK)
        return bool(
            white_player is not None
            and black_player is not None
            and white_player.is_human
            and black_player.is_human
        )
