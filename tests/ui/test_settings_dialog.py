"""Tests for settings dialog widgets and apply pipeline."""

from __future__ import annotations

from chessie.ui.dialogs.settings_dialog import AppSettings, SettingsDialog, _BoardPage


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
