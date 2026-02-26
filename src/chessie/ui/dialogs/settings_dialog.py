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


# ── Settings data class ──────────────────────────────────────────────────────


@dataclass
class AppSettings:
    """All user-configurable settings."""

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


class _BoardPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Доска")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addRow(title)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Classic", "Blue"])
        self._theme_combo.setCurrentText(settings.board_theme)
        layout.addRow("Тема доски:", self._theme_combo)

        self._coords_check = QCheckBox()
        self._coords_check.setChecked(settings.show_coordinates)
        layout.addRow("Показывать координаты:", self._coords_check)

        self._legal_check = QCheckBox()
        self._legal_check.setChecked(settings.show_legal_moves)
        layout.addRow("Показывать возможные ходы:", self._legal_check)

    def apply(self, settings: AppSettings) -> None:
        settings.board_theme = self._theme_combo.currentText()
        settings.show_coordinates = self._coords_check.isChecked()
        settings.show_legal_moves = self._legal_check.isChecked()


class _SoundPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Звук")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addRow(title)

        self._enabled_check = QCheckBox()
        self._enabled_check.setChecked(settings.sound_enabled)
        layout.addRow("Включить звуки:", self._enabled_check)

        # Volume row: slider + value label
        vol_row = QWidget()
        vol_layout = QHBoxLayout(vol_row)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(8)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(settings.sound_volume)
        self._volume_slider.setFixedWidth(160)

        self._volume_label = QLabel(f"{settings.sound_volume}%")
        self._volume_label.setFixedWidth(36)
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_label.setText(f"{v}%")
        )

        vol_layout.addWidget(self._volume_slider)
        vol_layout.addWidget(self._volume_label)
        vol_layout.addStretch()

        layout.addRow("Громкость:", vol_row)

    def apply(self, settings: AppSettings) -> None:
        settings.sound_enabled = self._enabled_check.isChecked()
        settings.sound_volume = self._volume_slider.value()


class _EnginePage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Движок")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addRow(title)

        self._depth_spin = QSpinBox()
        self._depth_spin.setRange(1, 10)
        self._depth_spin.setValue(settings.engine_depth)
        self._depth_spin.setSuffix(" пл.")
        layout.addRow("Глубина поиска:", self._depth_spin)

        self._time_spin = QSpinBox()
        self._time_spin.setRange(100, 10_000)
        self._time_spin.setSingleStep(100)
        self._time_spin.setValue(settings.engine_time_ms)
        self._time_spin.setSuffix(" мс")
        layout.addRow("Лимит времени на ход:", self._time_spin)

        note = QLabel("Изменения вступят в силу с начала следующей игры.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(note)

    def apply(self, settings: AppSettings) -> None:
        settings.engine_depth = self._depth_spin.value()
        settings.engine_time_ms = self._time_spin.value()


# ── Main dialog ──────────────────────────────────────────────────────────────


_PAGES = [
    ("Доска", _BoardPage),
    ("Звук", _SoundPage),
    ("Движок", _EnginePage),
]


class SettingsDialog(QDialog):
    """Modal settings dialog with a left category list and stacked pages."""

    def __init__(
        self,
        settings: AppSettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.setMinimumSize(560, 340)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._settings = settings
        self._pages: list[_BoardPage | _SoundPage | _EnginePage] = []

        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left sidebar ─────────────────────────────────────────────────
        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(150)
        self._sidebar.setStyleSheet(
            "QListWidget { background: #1e1e1e; border: none; border-right: 1px solid #3c3c3c; }"
            "QListWidget::item { padding: 10px 14px; color: #c0c0c0; font-size: 13px; }"
            "QListWidget::item:selected { background: #264f78; color: #ffffff; }"
        )

        # ── Right stacked pages ──────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #2b2b2b;")

        for label, PageClass in _PAGES:
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._sidebar.addItem(item)

            page = PageClass(self._settings)
            self._pages.append(page)
            self._stack.addWidget(page)

        self._sidebar.setCurrentRow(0)
        self._sidebar.currentRowChanged.connect(self._stack.setCurrentIndex)

        root.addWidget(self._sidebar)

        # Right side: pages + button box
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._stack)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.setContentsMargins(12, 8, 12, 8)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        right.addWidget(btn_box)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget)

    def _on_accept(self) -> None:
        for page in self._pages:
            page.apply(self._settings)
        self.accept()
