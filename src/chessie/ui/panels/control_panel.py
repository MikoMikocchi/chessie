"""ControlPanel — game action buttons."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class ControlPanel(QWidget):
    """Buttons for game actions: new game, resign, draw, undo, flip."""

    new_game_clicked = pyqtSignal()
    resign_clicked = pyqtSignal()
    draw_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    flip_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        btn_font = QFont("Helvetica Neue", 10)

        row1 = QHBoxLayout()
        self._btn_new = QPushButton("New Game")
        self._btn_new.setFont(btn_font)
        self._btn_new.setMinimumHeight(36)
        self._btn_new.clicked.connect(self.new_game_clicked)
        row1.addWidget(self._btn_new)

        self._btn_flip = QPushButton("⟲ Flip")
        self._btn_flip.setFont(btn_font)
        self._btn_flip.setMinimumHeight(36)
        self._btn_flip.clicked.connect(self.flip_clicked)
        row1.addWidget(self._btn_flip)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self._btn_undo = QPushButton("↩ Undo")
        self._btn_undo.setFont(btn_font)
        self._btn_undo.setMinimumHeight(36)
        self._btn_undo.clicked.connect(self.undo_clicked)
        row2.addWidget(self._btn_undo)

        self._btn_resign = QPushButton("Resign")
        self._btn_resign.setFont(btn_font)
        self._btn_resign.setMinimumHeight(36)
        self._btn_resign.setStyleSheet(
            "QPushButton { background-color: #6b2020; }"
            "QPushButton:hover { background-color: #8b2020; }"
        )
        self._btn_resign.clicked.connect(self.resign_clicked)
        row2.addWidget(self._btn_resign)

        self._btn_draw = QPushButton("½ Draw")
        self._btn_draw.setFont(btn_font)
        self._btn_draw.setMinimumHeight(36)
        self._btn_draw.clicked.connect(self.draw_clicked)
        row2.addWidget(self._btn_draw)
        layout.addLayout(row2)

    def set_game_active(self, active: bool) -> None:
        """Enable/disable buttons based on game state."""
        self._btn_resign.setEnabled(active)
        self._btn_draw.setEnabled(active)
        self._btn_undo.setEnabled(active)
