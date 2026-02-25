"""Chess clock with Fischer increment support."""

from __future__ import annotations

import time

from chessie.core.enums import Color
from chessie.game.interfaces import IClock, TimeControl


class Clock(IClock):
    """Dual chess clock tracking remaining time for both players.

    Uses monotonic time for accuracy. Supports Fischer increment.
    """

    __slots__ = (
        "_time_control",
        "_remaining",
        "_active_color",
        "_last_tick",
        "_running",
    )

    def __init__(self, time_control: TimeControl) -> None:
        self._time_control = time_control
        self._remaining: dict[Color, float] = {
            Color.WHITE: time_control.initial_seconds,
            Color.BLACK: time_control.initial_seconds,
        }
        self._active_color: Color | None = None
        self._last_tick: float = 0.0
        self._running: bool = False

    # ── IClock implementation ────────────────────────────────────────────

    def start(self, color: Color) -> None:
        self._active_color = color
        self._last_tick = time.monotonic()
        self._running = True

    def stop(self) -> None:
        if self._running:
            self._consume_elapsed()
            self._running = False

    def switch(self) -> None:
        """Stop current player's clock, start the other player's."""
        if self._active_color is None:
            return
        self._consume_elapsed()
        self._active_color = self._active_color.opposite
        self._last_tick = time.monotonic()

    def remaining(self, color: Color) -> float:
        if self._running and self._active_color == color:
            elapsed = time.monotonic() - self._last_tick
            return max(0.0, self._remaining[color] - elapsed)
        return max(0.0, self._remaining[color])

    def is_flag_fallen(self, color: Color) -> bool:
        return self.remaining(color) <= 0.0

    def add_increment(self, color: Color) -> None:
        self._remaining[color] += self._time_control.increment_seconds

    # ── Extra helpers ────────────────────────────────────────────────────

    @property
    def is_unlimited(self) -> bool:
        return self._time_control.initial_seconds == float("inf")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_color(self) -> Color | None:
        return self._active_color

    def set_remaining(self, color: Color, seconds: float) -> None:
        """Manually override remaining time (for testing / UI override)."""
        self._remaining[color] = seconds

    # ── Internal ─────────────────────────────────────────────────────────

    def _consume_elapsed(self) -> None:
        if self._active_color is None:
            return
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._remaining[self._active_color] = max(
            0.0, self._remaining[self._active_color] - elapsed
        )
        self._last_tick = now
