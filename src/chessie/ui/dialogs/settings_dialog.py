"""Backward-compatible exports for the settings dialog API."""

from chessie.ui.dialogs.settings import (
    AppSettings,
    SettingsDialog,
    _BoardPage,
    _BoardThemePreviewWidget,
    _EnginePage,
    _GeneralPage,
    _MoveNotationPreviewWidget,
    _SoundPage,
)

__all__ = [
    "AppSettings",
    "SettingsDialog",
    "_BoardPage",
    "_BoardThemePreviewWidget",
    "_EnginePage",
    "_GeneralPage",
    "_MoveNotationPreviewWidget",
    "_SoundPage",
]
