"""Chess sound effects player using Qt multimedia."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from chessie.game.interfaces import GameEndReason
from chessie.game.state import GameState, MoveRecord

_SOUNDS_DIR = Path(__file__).resolve().parents[3] / "assets" / "sounds"


class SoundPlayer:
    """Plays chess sound effects (OGG via FFmpeg).

    A single QMediaPlayer is shared across all sounds so that only one
    sound can ever be heard at a time.  A new event always interrupts the
    previous one.  Priority (lowest → highest): move < capture < check < checkmate.
    """

    _PATHS: dict[str, Path] = {
        "move": _SOUNDS_DIR / "move.ogg",
        "capture": _SOUNDS_DIR / "capture.ogg",
        "check": _SOUNDS_DIR / "check.ogg",
        "checkmate": _SOUNDS_DIR / "chekmate.ogg",
    }

    def __init__(self) -> None:
        self._enabled = True
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(0.8)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)

    # ── Public API ────────────────────────────────────────────────────────

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_volume(self, volume: int) -> None:
        """Set volume in range 0–100."""
        self._audio_output.setVolume(max(0, min(100, volume)) / 100.0)

    def play_move_sound(self, record: MoveRecord, state: GameState) -> None:
        """Choose and play the appropriate sound for the move just made."""
        if state.end_reason == GameEndReason.CHECKMATE:
            self._play("checkmate")
        elif record.was_check:
            self._play("check")
        elif record.was_capture:
            self._play("capture")
        else:
            self._play("move")

    # ── Internal helpers ──────────────────────────────────────────────────

    def _play(self, name: str) -> None:
        if not self._enabled:
            return
        path = self._PATHS.get(name)
        if path is None or not path.exists():
            return
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(str(path)))
        self._player.setPosition(0)
        self._player.play()
