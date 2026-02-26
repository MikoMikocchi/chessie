"""SettingsDialog — application-wide settings with a category sidebar."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from chessie.ui.i18n import LANGUAGES, t

# ── Settings data class ──────────────────────────────────────────────────────


@dataclass
class AppSettings:
    """All user-configurable settings."""

    # General
    language: str = "English"

    # Board
    board_theme: str = "Classic"
    show_coordinates: bool = True
    show_legal_moves: bool = True

    # Sound
    sound_enabled: bool = True
    sound_volume: int = 80  # 0–100

    # Engine
    engine_depth: int = 4
    engine_time_ms: int = 900


# ── Individual settings pages ────────────────────────────────────────────────


class _GeneralPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._form = QFormLayout(self)
        self._form.setSpacing(12)
        self._form.setContentsMargins(16, 16, 16, 16)

        self._title = QLabel()
        self._title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        self._form.addRow(self._title)

        self._lang_label = QLabel()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(LANGUAGES)
        idx = self._lang_combo.findText(settings.language)
        self._lang_combo.setCurrentIndex(max(0, idx))
        self._form.addRow(self._lang_label, self._lang_combo)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._title.setText(s.settings_language)
        self._lang_label.setText(s.settings_language)

    def apply(self, settings: AppSettings) -> None:
        settings.language = self._lang_combo.currentText()


class _BoardPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._form = QFormLayout(self)
        self._form.setSpacing(12)
        self._form.setContentsMargins(16, 16, 16, 16)

        self._title = QLabel()
        self._title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        self._form.addRow(self._title)

        self._theme_label = QLabel()
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Classic", "Blue"])
        self._theme_combo.setCurrentText(settings.board_theme)
        self._form.addRow(self._theme_label, self._theme_combo)

        self._coords_label = QLabel()
        self._coords_check = QCheckBox()
        self._coords_check.setChecked(settings.show_coordinates)
        self._form.addRow(self._coords_label, self._coords_check)

        self._legal_label = QLabel()
        self._legal_check = QCheckBox()
        self._legal_check.setChecked(settings.show_legal_moves)
        self._form.addRow(self._legal_label, self._legal_check)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._title.setText(s.settings_board)
        self._theme_label.setText(s.settings_board_theme)
        self._coords_label.setText(s.settings_show_coords)
        self._legal_label.setText(s.settings_show_legal)

    def apply(self, settings: AppSettings) -> None:
        settings.board_theme = self._theme_combo.currentText()
        settings.show_coordinates = self._coords_check.isChecked()
        settings.show_legal_moves = self._legal_check.isChecked()


class _SoundPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._form = QFormLayout(self)
        self._form.setSpacing(12)
        self._form.setContentsMargins(16, 16, 16, 16)

        self._title = QLabel()
        self._title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        self._form.addRow(self._title)

        self._enabled_label = QLabel()
        self._enabled_check = QCheckBox()
        self._enabled_check.setChecked(settings.sound_enabled)
        self._form.addRow(self._enabled_label, self._enabled_check)

        vol_row = QWidget()
        vol_layout = QHBoxLayout(vol_row)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(8)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(settings.sound_volume)
        self._volume_slider.setFixedWidth(160)

        self._volume_val_label = QLabel(f"{settings.sound_volume}%")
        self._volume_val_label.setFixedWidth(36)
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_val_label.setText(f"{v}%")
        )

        vol_layout.addWidget(self._volume_slider)
        vol_layout.addWidget(self._volume_val_label)
        vol_layout.addStretch()

        self._vol_label = QLabel()
        self._form.addRow(self._vol_label, vol_row)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._title.setText(s.settings_sound)
        self._enabled_label.setText(s.settings_sound_enable)
        self._vol_label.setText(s.settings_sound_volume)

    def apply(self, settings: AppSettings) -> None:
        settings.sound_enabled = self._enabled_check.isChecked()
        settings.sound_volume = self._volume_slider.value()


class _EnginePage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._form = QFormLayout(self)
        self._form.setSpacing(12)
        self._form.setContentsMargins(16, 16, 16, 16)

        self._title = QLabel()
        self._title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        self._form.addRow(self._title)

        self._depth_label = QLabel()
        self._depth_spin = QSpinBox()
        self._depth_spin.setRange(1, 10)
        self._depth_spin.setValue(settings.engine_depth)
        self._form.addRow(self._depth_label, self._depth_spin)

        self._time_label = QLabel()
        self._time_spin = QSpinBox()
        self._time_spin.setRange(100, 10_000)
        self._time_spin.setSingleStep(100)
        self._time_spin.setValue(settings.engine_time_ms)
        self._form.addRow(self._time_label, self._time_spin)

        self._note = QLabel()
        self._note.setWordWrap(True)
        self._note.setStyleSheet("color: #888; font-size: 11px;")
        self._form.addRow(self._note)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._title.setText(s.settings_engine)
        self._depth_label.setText(s.settings_engine_depth)
        self._depth_spin.setSuffix(s.settings_engine_depth_suffix)
        self._time_label.setText(s.settings_engine_time)
        self._time_spin.setSuffix(s.settings_engine_time_suffix)
        self._note.setText(s.settings_engine_note)

    def apply(self, settings: AppSettings) -> None:
        settings.engine_depth = self._depth_spin.value()
        settings.engine_time_ms = self._time_spin.value()


# ── Main dialog ──────────────────────────────────────────────────────────────

_PAGE_FACTORIES: list[
    tuple[str, type[_GeneralPage | _BoardPage | _SoundPage | _EnginePage]]
] = [
    ("settings_language", _GeneralPage),
    ("settings_board", _BoardPage),
    ("settings_sound", _SoundPage),
    ("settings_engine", _EnginePage),
]


class SettingsDialog(QDialog):
    """Modal settings dialog with a left category list and stacked pages."""

    def __init__(
        self,
        settings: AppSettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(560, 340)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._settings = settings
        self._pages: list[_GeneralPage | _BoardPage | _SoundPage | _EnginePage] = []
        self._page_attr_names: list[str] = []

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(150)
        self._sidebar.setStyleSheet(
            "QListWidget { background: #1e1e1e; border: none;"
            "  border-right: 1px solid #3c3c3c; }"
            "QListWidget::item { padding: 10px 14px; color: #c0c0c0; font-size: 13px; }"
            "QListWidget::item:selected { background: #264f78; color: #ffffff; }"
        )

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #2b2b2b;")

        for attr, PageClass in _PAGE_FACTORIES:
            self._page_attr_names.append(attr)
            item = QListWidgetItem()
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self._sidebar.addItem(item)

            page = PageClass(self._settings)
            self._pages.append(page)
            self._stack.addWidget(page)

        self._sidebar.setCurrentRow(0)
        self._sidebar.currentRowChanged.connect(self._stack.setCurrentIndex)

        root.addWidget(self._sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._stack)

        self._btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._btn_box.setContentsMargins(12, 8, 12, 8)
        self._btn_box.accepted.connect(self._on_accept)
        self._btn_box.rejected.connect(self.reject)
        right.addWidget(self._btn_box)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget)

    def retranslate_ui(self) -> None:
        s = t()
        self.setWindowTitle(s.settings_title)
        for i, attr in enumerate(self._page_attr_names):
            item = self._sidebar.item(i)
            if item is not None:
                item.setText(getattr(s, attr))
        for page in self._pages:
            page.retranslate_ui()

    def _on_accept(self) -> None:
        for page in self._pages:
            page.apply(self._settings)
        self.accept()
