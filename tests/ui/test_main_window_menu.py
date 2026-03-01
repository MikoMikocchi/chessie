"""Tests for MainWindow menu behavior across locale switches."""

from __future__ import annotations

from typing import cast

import pytest
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication

from chessie.ui.dialogs.manual_dialog import ManualDialog
from chessie.ui.i18n import set_language
from chessie.ui.main_window import MainWindow


class _ManualDialogStub:
    def __init__(self) -> None:
        self.show_calls = 0
        self.raise_calls = 0
        self.activate_calls = 0
        self.retranslate_calls = 0

    def show(self) -> None:
        self.show_calls += 1

    def raise_(self) -> None:
        self.raise_calls += 1

    def activateWindow(self) -> None:
        self.activate_calls += 1

    def retranslate_ui(self) -> None:
        self.retranslate_calls += 1


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

    def test_manual_action_reuses_existing_dialog(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        set_language("English")
        monkeypatch.setattr(
            "chessie.ui.main_window.EngineSession.setup", lambda _s: None
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.EngineSession.shutdown", lambda _s: None
        )
        manual_dialog_stub = _ManualDialogStub()
        manual_dialog = cast(ManualDialog, manual_dialog_stub)
        monkeypatch.setattr(
            "chessie.ui.main_window.ManualDialog.show_manual",
            lambda _parent: manual_dialog,
        )

        app = QApplication.instance() or QApplication([])
        window = MainWindow()

        window._on_manual()
        assert window._manual_dialog is manual_dialog

        window._on_manual()
        assert manual_dialog_stub.show_calls == 1
        assert manual_dialog_stub.raise_calls == 1
        assert manual_dialog_stub.activate_calls == 1

        window.close()
        app.processEvents()
        set_language("English")

    def test_retranslate_updates_existing_manual_dialog(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        set_language("English")
        monkeypatch.setattr(
            "chessie.ui.main_window.EngineSession.setup", lambda _s: None
        )
        monkeypatch.setattr(
            "chessie.ui.main_window.EngineSession.shutdown", lambda _s: None
        )
        manual_dialog_stub = _ManualDialogStub()
        manual_dialog = cast(ManualDialog, manual_dialog_stub)

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window._manual_dialog = manual_dialog

        window.retranslate_ui()
        assert manual_dialog_stub.retranslate_calls == 1

        window.close()
        app.processEvents()
        set_language("English")
