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
from chessie.ui.i18n import t


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

    # Keys are internal identifiers; display text is set via retranslate_ui
    PRESETS: dict[str, TimeControl] = {
        "Bullet 1+0": TimeControl.bullet_1m(),
        "Blitz 3+2": TimeControl.blitz_3m2s(),
        "Rapid 10+0": TimeControl.rapid_10m(),
        "Rapid 15+10": TimeControl.rapid_15m10s(),
        "Classical 30+0": TimeControl.classical_30m(),
        "unlimited": TimeControl.unlimited(),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(340)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._settings: _NewGameSettings | None = None
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        self._form = QFormLayout()
        self._form.setSpacing(10)

        self._combo_opponent = QComboBox()
        self._combo_opponent.setCurrentIndex(1)
        self._form.addRow("", self._combo_opponent)

        color_row = QHBoxLayout()
        self._grp_color = QButtonGroup(self)
        self._rb_white = QRadioButton()
        self._rb_black = QRadioButton()
        self._rb_white.setChecked(True)
        self._rb_white.setFont(QFont("Adwaita Sans", 11))
        self._rb_black.setFont(QFont("Adwaita Sans", 11))
        self._grp_color.addButton(self._rb_white, 0)
        self._grp_color.addButton(self._rb_black, 1)
        color_row.addWidget(self._rb_white)
        color_row.addWidget(self._rb_black)
        self._form.addRow("", color_row)

        self._combo_time = QComboBox()
        self._combo_time.setCurrentIndex(2)  # Rapid 10+0
        self._form.addRow("", self._combo_time)

        main.addLayout(self._form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        main.addWidget(self._buttons)

    def retranslate_ui(self) -> None:
        s = t()
        self.setWindowTitle(s.new_game_title)

        # Re-populate opponent combo preserving selection
        cur_opp = self._combo_opponent.currentIndex()
        self._combo_opponent.clear()
        self._combo_opponent.addItems([s.new_game_human, s.new_game_ai])
        self._combo_opponent.setCurrentIndex(max(0, cur_opp))

        self._rb_white.setText(s.new_game_white)
        self._rb_black.setText(s.new_game_black)

        # Re-populate time combo preserving selection
        cur_time = self._combo_time.currentIndex()
        self._combo_time.clear()
        preset_labels = list(self.PRESETS.keys())
        preset_labels[-1] = s.new_game_unlimited  # last entry is "Unlimited"
        self._combo_time.addItems(preset_labels)
        self._combo_time.setCurrentIndex(max(0, cur_time))

        # Update form row labels
        for row, label_text in enumerate(
            [s.new_game_opponent, s.new_game_play_as, s.new_game_time_control]
        ):
            label_item = self._form.itemAt(row, QFormLayout.ItemRole.LabelRole)
            if label_item is not None and label_item.widget() is not None:
                label_item.widget().setText(label_text)  # type: ignore[union-attr]
            else:
                self._form.setItem(
                    row,
                    QFormLayout.ItemRole.LabelRole,
                    self._form.itemAt(row, QFormLayout.ItemRole.LabelRole),
                )

    def _on_accept(self) -> None:
        time_idx = self._combo_time.currentIndex()
        tc = list(self.PRESETS.values())[time_idx]

        color = Color.WHITE if self._rb_white.isChecked() else Color.BLACK
        opp_idx = self._combo_opponent.currentIndex()
        opponent = "human" if opp_idx == 0 else "ai"

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
