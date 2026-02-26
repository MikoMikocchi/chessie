"""Tests for MainWindow menu behavior across locale switches."""

from __future__ import annotations

import pytest
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication

from chessie.ui.i18n import set_language
from chessie.ui.main_window import MainWindow


class TestMainWindowMenu:
    def test_settings_action_stays_in_settings_menu_after_locale_switch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        set_language("English")
        monkeypatch.setattr(
            "chessie.ui.main_window.EngineSession.setup", lambda _s: None
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.EngineSession.shutdown", lambda _s: None
        )

        app = QApplication.instance() or QApplication([])
        window = MainWindow()

        assert window._act_settings.menuRole() == QAction.MenuRole.NoRole
        assert window._act_settings in window._menu_settings.actions()

        window._settings.language = "Russian"
        window._apply_settings()

        assert window._menu_settings.title() == "&Настройки"
        assert window._act_settings.text() == "&Настройки..."
        assert window._act_settings in window._menu_settings.actions()
        assert window._act_settings.isVisible()

        window.close()
        app.processEvents()
        set_language("English")
