"""Tests for settings dialog widgets and apply pipeline."""

from __future__ import annotations

from typing import cast

from chessie.ui.dialogs.settings_dialog import (
    AppSettings,
    SettingsDialog,
    _BoardPage,
    _BoardThemePreviewWidget,
    _EnginePage,
    _GeneralPage,
    _MoveNotationPreviewWidget,
    _SoundPage,
)


def test_dialog_accept_applies_changes_to_settings() -> None:
    settings = AppSettings()
    dialog = SettingsDialog(settings)

    board_page = next(page for page in dialog._pages if isinstance(page, _BoardPage))
    board_page._theme_combo.setCurrentText("Blue")
    board_page._coords_check.setChecked(False)
    board_page._legal_check.setChecked(False)
    board_page._anim_check.setChecked(False)
    board_page._notation_combo.setCurrentIndex(1)

    dialog._on_accept()

    assert settings.board_theme == "Blue"
    assert settings.show_coordinates is False
    assert settings.show_legal_moves is False
    assert settings.animate_moves is False
    assert settings.use_figurine_notation is False


def test_board_page_notation_preview_updates_on_combo_change() -> None:
    page = _BoardPage(AppSettings(use_figurine_notation=True))
    assert page._notation_preview._use_figurine_notation is True

    page._notation_combo.setCurrentIndex(1)
    assert page._notation_preview._use_figurine_notation is False

    page._notation_combo.setCurrentIndex(0)
    assert page._notation_preview._use_figurine_notation is True


def test_dialog_retranslate_keeps_sidebar_items_populated() -> None:
    dialog = SettingsDialog(AppSettings())
    dialog.retranslate_ui()
    assert dialog._sidebar.count() == len(dialog._pages)
    for i in range(dialog._sidebar.count()):
        item = dialog._sidebar.item(i)
        assert item is not None
        assert item.text()


def test_dialog_accept_applies_general_sound_engine_pages() -> None:
    settings = AppSettings()
    dialog = SettingsDialog(settings)

    general_page = cast(_GeneralPage, dialog._pages[0])
    sound_page = cast(_SoundPage, dialog._pages[2])
    engine_page = cast(_EnginePage, dialog._pages[3])

    general_page._lang_combo.setCurrentText("Russian")
    sound_page._enabled_check.setChecked(False)
    sound_page._volume_slider.setValue(25)
    engine_page._depth_spin.setValue(7)
    engine_page._time_spin.setValue(1500)

    dialog._on_accept()

    assert settings.language == "Russian"
    assert settings.sound_enabled is False
    assert settings.sound_volume == 25
    assert settings.engine_depth == 7
    assert settings.engine_time_ms == 1500


def test_board_theme_preview_setter_and_paint_event() -> None:
    preview = _BoardThemePreviewWidget("Classic")
    preview.set_theme_name("Classic")
    assert preview._theme_name == "Classic"

    preview.set_theme_name("Unknown")
    assert preview._theme_name == "Unknown"
    preview.paintEvent(None)


def test_move_notation_preview_setter_and_paint_event() -> None:
    preview = _MoveNotationPreviewWidget()
    preview.set_use_figurine_notation(True)
    assert preview._use_figurine_notation is True

    preview.set_use_figurine_notation(False)
    assert preview._use_figurine_notation is False
    preview.paintEvent(None)
