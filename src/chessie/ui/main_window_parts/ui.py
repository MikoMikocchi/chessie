"""MainWindow UI construction and retranslation helpers."""

from __future__ import annotations

from typing import Any

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from chessie.ui.board.board_view import BoardView
from chessie.ui.i18n import t
from chessie.ui.panels.clock_widget import ClockWidget
from chessie.ui.panels.control_panel import ControlPanel
from chessie.ui.panels.eval_bar import EvalBar
from chessie.ui.panels.move_panel import MovePanel


def setup_ui(host: Any) -> None:
    """Build the central layout and status bar widgets."""
    central = QWidget()
    host.setCentralWidget(central)
    root = QHBoxLayout(central)
    root.setContentsMargins(6, 6, 6, 6)
    root.setSpacing(6)

    # Eval bar (left)
    host._eval_bar = EvalBar()
    root.addWidget(host._eval_bar)

    # Board (center)
    host._board_view = BoardView()
    root.addWidget(host._board_view, stretch=3)

    # Right panel
    right = QVBoxLayout()
    right.setSpacing(6)

    host._clock_widget = ClockWidget()
    right.addWidget(host._clock_widget)

    host._move_panel = MovePanel()
    right.addWidget(host._move_panel, stretch=1)

    host._control_panel = ControlPanel()
    right.addWidget(host._control_panel)

    right_widget = QWidget()
    right_widget.setLayout(right)
    right_widget.setFixedWidth(280)
    root.addWidget(right_widget)

    # Status bar
    host._status = QStatusBar()
    host.setStatusBar(host._status)
    host._status_label = QLabel(t().status_ready)
    host._status.addWidget(host._status_label)


def setup_menu(host: Any) -> None:
    """Build menu actions and bind action handlers."""
    menu_bar = host.menuBar()
    assert menu_bar is not None
    s = t()

    # Game menu
    host._menu_game = menu_bar.addMenu(s.menu_game)
    assert host._menu_game is not None

    host._act_new_game = QAction(s.menu_new_game, host)
    host._act_new_game.setShortcut("Ctrl+N")
    host._act_new_game.triggered.connect(host._on_new_game_dialog)
    host._menu_game.addAction(host._act_new_game)

    host._act_open_pgn = QAction(s.menu_open_pgn, host)
    host._act_open_pgn.setShortcut("Ctrl+O")
    host._act_open_pgn.triggered.connect(host._on_open_pgn)
    host._menu_game.addAction(host._act_open_pgn)

    host._act_save_pgn = QAction(s.menu_save_pgn, host)
    host._act_save_pgn.setShortcut("Ctrl+S")
    host._act_save_pgn.triggered.connect(host._on_save_pgn)
    host._menu_game.addAction(host._act_save_pgn)

    host._act_analyze_game = QAction(s.menu_analyze_game, host)
    host._act_analyze_game.setShortcut("Ctrl+Shift+A")
    host._act_analyze_game.triggered.connect(host._on_analyze_game)
    host._menu_game.addAction(host._act_analyze_game)

    host._menu_game.addSeparator()

    host._act_flip = QAction(s.menu_flip_board, host)
    host._act_flip.setShortcut("F")
    host._act_flip.triggered.connect(host._on_flip)
    host._menu_game.addAction(host._act_flip)

    host._menu_game.addSeparator()

    host._act_quit = QAction(s.menu_quit, host)
    host._act_quit.setShortcut("Ctrl+Q")
    host._act_quit.setMenuRole(QAction.MenuRole.QuitRole)
    host._act_quit.triggered.connect(host.close)
    host._menu_game.addAction(host._act_quit)

    # Settings menu
    host._menu_settings = menu_bar.addMenu(s.menu_settings)
    assert host._menu_settings is not None

    host._act_settings = QAction(s.menu_settings_action, host)
    host._act_settings.setShortcut("Ctrl+,")
    # Keep this action inside our custom Settings menu across locales/platforms.
    host._act_settings.setMenuRole(QAction.MenuRole.NoRole)
    host._act_settings.triggered.connect(host._on_settings)
    host._menu_settings.addAction(host._act_settings)


def retranslate_ui(host: Any) -> None:
    """Update all translatable strings when the locale changes."""
    s = t()
    assert host._menu_game is not None
    assert host._menu_settings is not None

    # Menu bar
    host._menu_game.setTitle(s.menu_game)
    host._act_new_game.setText(s.menu_new_game)
    host._act_open_pgn.setText(s.menu_open_pgn)
    host._act_save_pgn.setText(s.menu_save_pgn)
    host._act_analyze_game.setText(s.menu_analyze_game)
    host._act_flip.setText(s.menu_flip_board)
    host._act_quit.setText(s.menu_quit)
    host._menu_settings.setTitle(s.menu_settings)
    host._act_settings.setText(s.menu_settings_action)

    # Child widgets
    host._move_panel.retranslate_ui()
    host._control_panel.retranslate_ui()
    host._clock_widget.retranslate_ui()
    host._update_status()
