"""MovePanel — scrollable list of moves in SAN notation."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from chessie.core.enums import Color
from chessie.game.state import MoveRecord
from chessie.ui.i18n import t

# Unicode figurine symbols: white = outline, black = filled
_FIGURINE: dict[Color, dict[str, str]] = {
    Color.WHITE: {"K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘"},
    Color.BLACK: {"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞"},
}


def _figurine_san(san: str, color: Color) -> str:
    """Replace piece letters in *san* with Unicode figurine symbols for *color*."""
    table = _FIGURINE[color]

    # Replace leading piece letter (Nf3, Qxd5, Ke2…)
    if san and san[0] in table:
        san = table[san[0]] + san[1:]

    # Replace promotion target (e8=Q → e8=♕)
    if "=" in san:
        prefix, _, promo = san.partition("=")
        san = prefix + "=" + table.get(promo[0], promo[0]) + promo[1:]

    return san


class MovePanel(QWidget):
    """Displays the game's move history in standard notation."""

    move_clicked = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._records: list[MoveRecord] = []
        self._move_buttons: dict[int, QToolButton] = {}
        self._active_ply: int | None = None
        self._use_figurine_notation = True
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._header = QLabel()
        self._header.setFont(QFont("Adwaita Sans", 12, QFont.Weight.Bold))
        self._header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._header)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setFont(QFont("AdwaitaMono Nerd Font", 12))
        layout.addWidget(self._list)

    def retranslate_ui(self) -> None:
        self._header.setText(t().moves_header)

    def clear(self) -> None:
        self._records.clear()
        self._move_buttons.clear()
        self._active_ply = None
        self._list.clear()

    def _create_move_button(self, text: str, ply: int) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setProperty("activeMove", False)
        btn.setStyleSheet(
            """
            QToolButton {
                background: transparent;
                color: #d4d4d4;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px 8px;
                text-align: left;
                font-family: "AdwaitaMono Nerd Font", "Adwaita Sans", monospace;
                font-size: 13px;
            }
            QToolButton:hover {
                background: #3c3c3c;
                border-color: #555;
            }
            QToolButton[activeMove="true"] {
                background: #264f78;
                border-color: #3b79b7;
                color: #f0f6ff;
            }
            """
        )
        btn.clicked.connect(
            lambda _checked=False, move_ply=ply: self._on_move_clicked(move_ply)
        )
        return btn

    def _set_active_ply(self, ply: int | None) -> None:
        self._active_ply = ply
        for move_ply, btn in self._move_buttons.items():
            btn.setProperty("activeMove", move_ply == ply)
            style = btn.style()
            if style is not None:
                style.unpolish(btn)
                style.polish(btn)
            btn.update()

    def _on_move_clicked(self, ply: int) -> None:
        self._set_active_ply(ply)
        self.move_clicked.emit(ply)

    def set_use_figurine_notation(self, enabled: bool) -> None:
        """Toggle move text style between figurines and standard SAN letters."""
        if self._use_figurine_notation == enabled:
            return
        self._use_figurine_notation = enabled
        self._rebuild_list()

    def _format_san(self, san: str, color: Color) -> str:
        if self._use_figurine_notation:
            return _figurine_san(san, color)
        return san

    def _rebuild_list(self) -> None:
        self._list.clear()
        self._move_buttons.clear()
        for move_idx in range(0, len(self._records), 2):
            move_num = move_idx // 2 + 1
            white_san = self._format_san(self._records[move_idx].san, Color.WHITE)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(6, 2, 6, 2)
            row_layout.setSpacing(8)

            num_label = QLabel(f"{move_num}.")
            num_label.setFont(QFont("Adwaita Sans", 12))
            num_label.setFixedWidth(28)
            num_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            row_layout.addWidget(num_label)

            white_btn = self._create_move_button(white_san, move_idx)
            row_layout.addWidget(white_btn, 1)
            self._move_buttons[move_idx] = white_btn

            if move_idx + 1 < len(self._records):
                black_san = self._format_san(
                    self._records[move_idx + 1].san,
                    Color.BLACK,
                )
                black_btn = self._create_move_button(black_san, move_idx + 1)
                row_layout.addWidget(black_btn, 1)
                self._move_buttons[move_idx + 1] = black_btn
            else:
                spacer = QWidget()
                spacer.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                row_layout.addWidget(spacer, 1)

            item = QListWidgetItem()
            item.setSizeHint(row_widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row_widget)

        if self._records:
            active = (
                self._active_ply
                if self._active_ply is not None
                else len(self._records) - 1
            )
            if active >= len(self._records):
                active = len(self._records) - 1
            self._set_active_ply(active)
        else:
            self._set_active_ply(None)
        self._list.scrollToBottom()

    def add_move(self, record: MoveRecord, move_number: int, color: Color) -> None:
        """Append a move to the panel."""
        self._records.append(record)
        self._active_ply = len(self._records) - 1
        self._rebuild_list()

    def remove_last(self) -> None:
        """Remove the last move entry (for undo)."""
        if self._records:
            self._records.pop()
            self._active_ply = len(self._records) - 1 if self._records else None
            self._rebuild_list()

    def set_history(self, records: list[MoveRecord]) -> None:
        """Rebuild the entire move list."""
        self._records = list(records)
        self._active_ply = len(self._records) - 1 if self._records else None
        self._rebuild_list()
