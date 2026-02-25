"""MainWindow — top-level window assembling all UI components."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

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

TCallback = TypeVar("TCallback", bound=Callable[..., None])


class MainWindow(QMainWindow):
    """Main application window for Chessie."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Chessie")
        self.setMinimumSize(900, 640)
        self.resize(1100, 750)

        self._controller = GameController()
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        self._connect_game_events()

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
            white = HumanPlayer(Color.WHITE, "White")
            black = HumanPlayer(Color.BLACK, "Black")
        else:
            # AI — placeholder: for now AI does nothing until engine is integrated
            if settings.player_color == Color.WHITE:
                white = HumanPlayer(Color.WHITE, "You")
                black = AIPlayer(
                    Color.BLACK,
                    "Chessie AI",
                    on_request_move=lambda pos: None,
                    on_cancel=lambda: None,
                )
            else:
                white = AIPlayer(
                    Color.WHITE,
                    "Chessie AI",
                    on_request_move=lambda pos: None,
                    on_cancel=lambda: None,
                )
                black = HumanPlayer(Color.BLACK, "You")

        self._connect_game_events()
        self._controller.new_game(white, black, settings.time_control)
        self._after_new_game()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._disconnect_game_events()
        super().closeEvent(event)

    def _after_new_game(self) -> None:
        """Sync UI after a new game starts."""
        state = self._controller.state
        self._board_view.board_scene.set_position(state.position)
        self._board_view.board_scene.set_interactive(True)
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

        self._update_status()

    # ── User actions ─────────────────────────────────────────────────────

    def _on_user_move(self, move: Move) -> None:
        """Handle a move from the board UI."""
        self._controller.submit_move(move)

    def _on_resign(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            return
        # Determine which side the human is playing
        human_color = self._find_human_color()
        reply = QMessageBox.question(
            self,
            "Resign",
            "Are you sure you want to resign?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._controller.resign(human_color)

    def _on_draw(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            return
        self._controller.offer_draw(state.side_to_move)
        # For human–human, auto-accept
        white_p = self._controller.player(Color.WHITE)
        black_p = self._controller.player(Color.BLACK)
        if white_p and black_p and white_p.is_human and black_p.is_human:
            self._controller.accept_draw()

    def _on_undo(self) -> None:
        if self._controller.undo_move():
            state = self._controller.state
            self._board_view.board_scene.set_position(state.position)
            self._board_view.board_scene.highlight_last_move(
                state.move_history[-1].move if state.move_history else None
            )
            self._board_view.board_scene.highlight_check()
            self._move_panel.remove_last()
            self._update_status()

    def _on_flip(self) -> None:
        scene = self._board_view.board_scene
        scene.set_flipped(not scene.is_flipped())

    # ── Game event callbacks ─────────────────────────────────────────────

    def _on_game_move(self, move: Move, san: str, state: GameState) -> None:
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

    def _on_phase_changed(self, phase: GamePhase) -> None:
        self._update_status()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _update_status(self) -> None:
        state = self._controller.state
        if state.is_game_over:
            return
        side = "White" if state.side_to_move == Color.WHITE else "Black"
        phase = state.phase.name.replace("_", " ").capitalize()
        self._status_label.setText(f"{side} · {phase} · Move {state.fullmove_display}")

    def _find_human_color(self) -> Color:
        """Return the color of the first human player found."""
        for c in (Color.WHITE, Color.BLACK):
            p = self._controller.player(c)
            if p and p.is_human:
                return c
        return Color.WHITE
