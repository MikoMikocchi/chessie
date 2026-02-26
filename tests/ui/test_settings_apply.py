"""Tests for applying app settings to UI components."""

from __future__ import annotations

from types import SimpleNamespace

from chessie.ui.dialogs.settings_dialog import AppSettings
from chessie.ui.main_window_parts import settings as settings_part


class _StubScene:
    def set_theme(self, _theme: object) -> None:
        return

    def set_show_coordinates(self, _visible: bool) -> None:
        return

    def set_show_legal_moves(self, _visible: bool) -> None:
        return

    def set_animate_moves(self, _enabled: bool) -> None:
        return


class _StubMovePanel:
    def __init__(self) -> None:
        self.values: list[bool] = []

    def set_use_figurine_notation(self, enabled: bool) -> None:
        self.values.append(enabled)


class _StubSound:
    def set_enabled(self, _enabled: bool) -> None:
        return

    def set_volume(self, _volume: int) -> None:
        return


class _StubEngine:
    def set_limits(self, _depth: int, _time_ms: int) -> None:
        return


def test_apply_settings_updates_move_notation_mode() -> None:
    settings = AppSettings(use_figurine_notation=False)
    move_panel = _StubMovePanel()
    host = SimpleNamespace(
        _settings=settings,
        _board_view=SimpleNamespace(board_scene=_StubScene()),
        _move_panel=move_panel,
        _sound_player=_StubSound(),
        _engine_session=_StubEngine(),
        retranslate_ui=lambda: None,
    )

    settings_part.apply_settings(host)

    assert move_panel.values == [False]
