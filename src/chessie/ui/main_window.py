"""MainWindow — top-level window assembling all UI components."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
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
from chessie.core.notation import position_to_fen
from chessie.engine import EngineWorker
from chessie.game.controller import GameController
from chessie.game.interfaces import GamePhase, IPlayer, TimeControl
from chessie.game.player import AIPlayer, HumanPlayer
from chessie.game.state import GameState
from chessie.ui.board.board_view import BoardView
from chessie.ui.dialogs.new_game_dialog import NewGameDialog
from chessie.ui.panels.clock_widget import ClockWidget
from chessie.ui.panels.control_panel import ControlPanel
from chessie.ui.panels.eval_bar import EvalBar
from chessie.ui.panels.move_panel import MovePanel

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
        self._engine_thread = QThread(self)
        self._engine_worker = EngineWorker(max_depth=4, time_limit_ms=900)
        self._engine_request_id = 0
        self._pending_engine_request: int | None = None
        self._pending_engine_fen: str | None = None

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
        self._status_label = QLabel("Ready")
        self._status.addWidget(self._status_label)

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()
        assert menu_bar is not None

        # Game menu
        game_menu = menu_bar.addMenu("&Game")
        assert game_menu is not None

        new_act = QAction("&New Game...", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self._on_new_game_dialog)
        game_menu.addAction(new_act)

        game_menu.addSeparator()

        flip_act = QAction("&Flip Board", self)
        flip_act.setShortcut("F")
        flip_act.triggered.connect(self._on_flip)
        game_menu.addAction(flip_act)

        game_menu.addSeparator()

        quit_act = QAction("&Quit", self)
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)
        game_menu.addAction(quit_act)

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
        white = HumanPlayer(Color.WHITE, "White")
        black = HumanPlayer(Color.BLACK, "Black")
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
            white = HumanPlayer(Color.WHITE, "White")
            black = HumanPlayer(Color.BLACK, "Black")
        else:
            self._cancel_ai_search()
            if settings.player_color == Color.WHITE:
                white = HumanPlayer(Color.WHITE, "You")
                black = self._create_ai_player(Color.BLACK)
            else:
                white = self._create_ai_player(Color.WHITE)
                black = HumanPlayer(Color.BLACK, "You")

        self._connect_game_events()
        self._controller.new_game(white, black, settings.time_control)
        self._after_new_game()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._cancel_ai_search()
        self._disconnect_game_events()
        self._engine_thread.quit()
        self._engine_thread.wait(2000)
        super().closeEvent(event)

    def _after_new_game(self) -> None:
        """Sync UI after a new game starts."""
        state = self._controller.state
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
            "Resign",
            "Are you sure you want to resign?",
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

        # In human-vs-human mode, draw is immediate (no second-side confirmation).
        white_p = self._controller.player(Color.WHITE)
        black_p = self._controller.player(Color.BLACK)
        is_human_vs_human = (
            white_p is not None
            and black_p is not None
            and white_p.is_human
            and black_p.is_human
        )
        if is_human_vs_human:
            self._controller.accept_draw(offering_color.opposite)

    def _on_undo(self) -> None:
        if self._controller.undo_move():
            state = self._controller.state
            self._board_view.board_scene.set_position(state.position)
            self._board_view.board_scene.highlight_last_move(
                state.move_history[-1].move if state.move_history else None
            )
            self._board_view.board_scene.highlight_check()
            self._move_panel.remove_last()
            self._sync_board_interactivity()
            self._update_status()

    def _on_flip(self) -> None:
        scene = self._board_view.board_scene
        scene.set_flipped(not scene.is_flipped())

    # ── Game event callbacks ─────────────────────────────────────────────

    def _on_game_move(self, move: Move, _san: str, state: GameState) -> None:
        """Called after every move (both human and AI)."""
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

        msg_map = {
            GameResult.WHITE_WINS: "White wins!",
            GameResult.BLACK_WINS: "Black wins!",
            GameResult.DRAW: "Draw!",
        }
        text = msg_map.get(result, str(result))
        self._status_label.setText(f"Game over — {text}")

        QMessageBox.information(self, "Game Over", text)

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

        self._status_label.setText(f"Engine error: {message}")
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

    def _update_status(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            return
        side = "White" if state.side_to_move == Color.WHITE else "Black"
        phase = state.phase.name.replace("_", " ").capitalize()
        self._status_label.setText(f"{side} · {phase} · Move {state.fullmove_display}")

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
