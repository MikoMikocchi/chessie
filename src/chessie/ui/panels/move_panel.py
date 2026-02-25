"""MovePanel — scrollable list of moves in SAN notation."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chessie.core.enums import Color
from chessie.game.state import MoveRecord


class MovePanel(QWidget):
    """Displays the game's move history in standard notation."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[MoveRecord] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("Moves")
        header.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._list)

    def clear(self) -> None:
        self._records.clear()
        self._list.clear()

    def add_move(self, record: MoveRecord, move_number: int, color: Color) -> None:
        """Append a move to the panel."""
        self._records.append(record)

        if color == Color.WHITE:
            text = f"{move_number}. {record.san}"
        else:
            text = f"{move_number}. ... {record.san}"

        item = QListWidgetItem(text)
        item.setFont(QFont("JetBrains Mono", 12))
        self._list.addItem(item)
        self._list.scrollToBottom()

    def remove_last(self) -> None:
        """Remove the last move entry (for undo)."""
        if self._records:
            self._records.pop()
            self._list.takeItem(self._list.count() - 1)

    def set_history(self, records: list[MoveRecord]) -> None:
        """Rebuild the entire move list."""
        self.clear()
        for i, rec in enumerate(records):
            ply = i
            move_num = ply // 2 + 1
            color = Color.WHITE if ply % 2 == 0 else Color.BLACK
            self.add_move(rec, move_num, color)
