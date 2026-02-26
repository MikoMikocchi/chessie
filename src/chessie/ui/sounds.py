"""Chess sound effects player using Qt multimedia."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect

from chessie.game.interfaces import GameEndReason
from chessie.game.state import GameState, MoveRecord

_SOUNDS_DIR = Path(__file__).resolve().parents[3] / "assets" / "sounds"


class SoundPlayer:
    """Plays chess sound effects (WAV via QSoundEffect).

    Each sound uses a dedicated QSoundEffect that is pre-loaded at startup,
    so playback is immediate and zero-latency.  A new event always interrupts
    the previous one.  Priority (lowest → highest): move < capture < check < checkmate.
    """

    _NAMES: dict[str, str] = {
        "move": "move.wav",
        "capture": "capture.wav",
        "check": "check.wav",
        "checkmate": "chekmate.wav",
    }

    def __init__(self) -> None:
        self._enabled = True
        self._volume = 0.8
        self._effects: dict[str, QSoundEffect] = {}
        self._current: QSoundEffect | None = None

        for name, filename in self._NAMES.items():
            path = _SOUNDS_DIR / filename
            if not path.exists():
                continue
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.setVolume(self._volume)
            self._effects[name] = effect

    # ── Public API ────────────────────────────────────────────────────────

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_volume(self, volume: int) -> None:
        """Set volume in range 0–100."""
        self._volume = max(0, min(100, volume)) / 100.0
        for effect in self._effects.values():
            effect.setVolume(self._volume)

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
        effect = self._effects.get(name)
        if effect is None:
            return
        if self._current is not None and self._current.isPlaying():
            self._current.stop()
        self._current = effect
        effect.play()
