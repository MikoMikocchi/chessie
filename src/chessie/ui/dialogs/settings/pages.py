"""Settings dialog page widgets."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QWidget,
)

from chessie.ui.dialogs.settings.models import AppSettings
from chessie.ui.dialogs.settings.previews import (
    _BoardThemePreviewWidget,
    _MoveNotationPreviewWidget,
)
from chessie.ui.i18n import LANGUAGES, t


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
        self._theme_combo.addItems(["Classic", "Blue", "Green", "Walnut", "Slate"])
        self._theme_combo.setCurrentText(settings.board_theme)
        self._preview = _BoardThemePreviewWidget(settings.board_theme)
        self._theme_combo.currentTextChanged.connect(self._preview.set_theme_name)

        theme_row = QWidget()
        theme_layout = QHBoxLayout(theme_row)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(12)
        self._theme_combo.setMinimumWidth(220)
        theme_layout.addWidget(self._theme_combo)
        theme_layout.addWidget(self._preview)
        theme_layout.addStretch()
        self._form.addRow(self._theme_label, theme_row)

        self._coords_label = QLabel()
        self._coords_check = QCheckBox()
        self._coords_check.setChecked(settings.show_coordinates)
        self._form.addRow(self._coords_label, self._coords_check)

        self._legal_label = QLabel()
        self._legal_check = QCheckBox()
        self._legal_check.setChecked(settings.show_legal_moves)
        self._form.addRow(self._legal_label, self._legal_check)

        self._anim_label = QLabel()
        self._anim_check = QCheckBox()
        self._anim_check.setChecked(settings.animate_moves)
        self._form.addRow(self._anim_label, self._anim_check)

        self._notation_label = QLabel()
        self._notation_combo = QComboBox()
        self._notation_combo.addItem("", True)
        self._notation_combo.addItem("", False)
        self._set_notation_combo_texts()
        self._notation_combo.setCurrentIndex(0 if settings.use_figurine_notation else 1)

        self._notation_preview = _MoveNotationPreviewWidget()
        self._notation_preview.set_use_figurine_notation(settings.use_figurine_notation)
        self._notation_combo.currentIndexChanged.connect(self._on_notation_changed)

        notation_row = QWidget()
        notation_layout = QHBoxLayout(notation_row)
        notation_layout.setContentsMargins(0, 0, 0, 0)
        notation_layout.setSpacing(12)
        self._notation_combo.setMinimumWidth(220)
        notation_layout.addWidget(self._notation_combo)
        notation_layout.addWidget(self._notation_preview)
        notation_layout.addStretch()
        self._form.addRow(self._notation_label, notation_row)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._title.setText(s.settings_board)
        self._theme_label.setText(s.settings_board_theme)
        self._coords_label.setText(s.settings_show_coords)
        self._legal_label.setText(s.settings_show_legal)
        self._anim_label.setText(s.settings_animate_moves)
        self._notation_label.setText(s.settings_move_notation)
        self._set_notation_combo_texts()

    def _set_notation_combo_texts(self) -> None:
        s = t()
        self._notation_combo.setItemText(0, s.settings_move_notation_icons)
        self._notation_combo.setItemText(1, s.settings_move_notation_letters)

    def _on_notation_changed(self) -> None:
        enabled = bool(self._notation_combo.currentData())
        self._notation_preview.set_use_figurine_notation(enabled)

    def apply(self, settings: AppSettings) -> None:
        settings.board_theme = self._theme_combo.currentText()
        settings.show_coordinates = self._coords_check.isChecked()
        settings.show_legal_moves = self._legal_check.isChecked()
        settings.animate_moves = self._anim_check.isChecked()
        settings.use_figurine_notation = bool(self._notation_combo.currentData())


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

        self._analysis_depth_label = QLabel()
        self._analysis_depth_spin = QSpinBox()
        self._analysis_depth_spin.setRange(1, 10)
        self._analysis_depth_spin.setValue(settings.analysis_depth)
        self._form.addRow(self._analysis_depth_label, self._analysis_depth_spin)

        self._analysis_time_label = QLabel()
        self._analysis_time_spin = QSpinBox()
        self._analysis_time_spin.setRange(50, 10_000)
        self._analysis_time_spin.setSingleStep(50)
        self._analysis_time_spin.setValue(settings.analysis_time_ms)
        self._form.addRow(self._analysis_time_label, self._analysis_time_spin)

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
        self._analysis_depth_label.setText(s.settings_analysis_depth)
        self._analysis_depth_spin.setSuffix(s.settings_engine_depth_suffix)
        self._analysis_time_label.setText(s.settings_analysis_time)
        self._analysis_time_spin.setSuffix(s.settings_engine_time_suffix)
        self._note.setText(s.settings_engine_note)

    def apply(self, settings: AppSettings) -> None:
        settings.engine_depth = self._depth_spin.value()
        settings.engine_time_ms = self._time_spin.value()
        settings.analysis_depth = self._analysis_depth_spin.value()
        settings.analysis_time_ms = self._analysis_time_spin.value()


type SettingsPage = _GeneralPage | _BoardPage | _SoundPage | _EnginePage

PAGE_FACTORIES: list[tuple[str, type[SettingsPage]]] = [
    ("settings_language", _GeneralPage),
    ("settings_board", _BoardPage),
    ("settings_sound", _SoundPage),
    ("settings_engine", _EnginePage),
]
