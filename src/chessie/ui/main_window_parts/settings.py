"""MainWindow settings dialog and application helpers."""

from __future__ import annotations

from typing import Any

from chessie.ui.i18n import set_language
from chessie.ui.styles.theme import BoardTheme


def on_settings(host: Any, *, settings_dialog_cls: type[Any]) -> None:
    dlg = settings_dialog_cls(host._settings, host)
    if dlg.exec():
        host._apply_settings()


def apply_settings(host: Any) -> None:
    s = host._settings

    # Language must come first so all retranslate calls use the new locale
    set_language(s.language)
    host.retranslate_ui()

    scene = host._board_view.board_scene

    # Board
    theme_map = {
        "Classic": BoardTheme.default(),
        "Blue": BoardTheme.blue(),
        "Green": BoardTheme.green(),
        "Walnut": BoardTheme.walnut(),
        "Slate": BoardTheme.slate(),
    }
    scene.set_theme(theme_map.get(s.board_theme, BoardTheme.default()))
    scene.set_show_coordinates(s.show_coordinates)
    scene.set_show_legal_moves(s.show_legal_moves)
    scene.set_animate_moves(s.animate_moves)

    # Sound
    host._sound_player.set_enabled(s.sound_enabled)
    host._sound_player.set_volume(s.sound_volume)

    # Engine (applied to subsequent searches; doesn't interrupt current)
    host._engine_session.set_limits(s.engine_depth, s.engine_time_ms)
