"""Settings dialog package."""

from chessie.ui.dialogs.settings.dialog import SettingsDialog
from chessie.ui.dialogs.settings.models import AppSettings
from chessie.ui.dialogs.settings.pages import (
    _BoardPage,
    _EnginePage,
    _GeneralPage,
    _SoundPage,
)
from chessie.ui.dialogs.settings.previews import (
    _BoardThemePreviewWidget,
    _MoveNotationPreviewWidget,
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
