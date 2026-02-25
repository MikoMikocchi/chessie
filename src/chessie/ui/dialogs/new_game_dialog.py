"""NewGameDialog — game setup before starting a new game."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from chessie.core.enums import Color
from chessie.game.interfaces import TimeControl


class _NewGameSettings:
    """Plain data returned by NewGameDialog."""

    __slots__ = ("opponent", "player_color", "time_control")

    def __init__(
        self,
        opponent: str,
        player_color: Color,
        time_control: TimeControl,
    ) -> None:
        self.opponent = opponent
        self.player_color = player_color
        self.time_control = time_control


class NewGameDialog(QDialog):
    """Modal dialog to configure a new game."""

    PRESETS: dict[str, TimeControl] = {
        "Bullet 1+0": TimeControl.bullet_1m(),
        "Blitz 3+2": TimeControl.blitz_3m2s(),
        "Rapid 10+0": TimeControl.rapid_10m(),
        "Rapid 15+10": TimeControl.rapid_15m10s(),
        "Classical 30+0": TimeControl.classical_30m(),
        "Unlimited": TimeControl.unlimited(),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Game")
        self.setModal(True)
        self.setMinimumWidth(340)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._settings: _NewGameSettings | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        # Opponent
        self._combo_opponent = QComboBox()
        self._combo_opponent.addItems(["Human", "AI"])
        self._combo_opponent.setCurrentIndex(1)
        form.addRow("Opponent:", self._combo_opponent)

        # Player color
        color_row = QHBoxLayout()
        self._grp_color = QButtonGroup(self)
        self._rb_white = QRadioButton("♔ White")
        self._rb_black = QRadioButton("♚ Black")
        self._rb_white.setChecked(True)
        self._rb_white.setFont(QFont("Adwaita Sans", 11))
        self._rb_black.setFont(QFont("Adwaita Sans", 11))
        self._grp_color.addButton(self._rb_white, 0)
        self._grp_color.addButton(self._rb_black, 1)
        color_row.addWidget(self._rb_white)
        color_row.addWidget(self._rb_black)
        form.addRow("Play as:", color_row)

        # Time control preset
        self._combo_time = QComboBox()
        self._combo_time.addItems(list(self.PRESETS.keys()))
        self._combo_time.setCurrentIndex(2)  # Rapid 10+0
        form.addRow("Time control:", self._combo_time)

        main.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        main.addWidget(buttons)

    def _on_accept(self) -> None:
        preset_name = self._combo_time.currentText()
        tc = self.PRESETS[preset_name]

        color = Color.WHITE if self._rb_white.isChecked() else Color.BLACK
        opponent = self._combo_opponent.currentText().lower()

        self._settings = _NewGameSettings(
            opponent=opponent,
            player_color=color,
            time_control=tc,
        )
        self.accept()

    @property
    def settings(self) -> _NewGameSettings | None:
        return self._settings

    @staticmethod
    def ask(parent: QWidget | None = None) -> _NewGameSettings | None:
        dlg = NewGameDialog(parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.settings
        return None
