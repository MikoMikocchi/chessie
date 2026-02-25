"""Tests for Clock."""

import time

from chessie.core.enums import Color
from chessie.game.clock import Clock
from chessie.game.interfaces import TimeControl


class TestClockBasics:
    def test_initial_remaining(self) -> None:
        clock = Clock(TimeControl(300, 0))
        assert clock.remaining(Color.WHITE) == 300.0
        assert clock.remaining(Color.BLACK) == 300.0

    def test_not_running_initially(self) -> None:
        clock = Clock(TimeControl(300, 0))
        assert not clock.is_running

    def test_start_sets_running(self) -> None:
        clock = Clock(TimeControl(300, 0))
        clock.start(Color.WHITE)
        assert clock.is_running
        assert clock.active_color == Color.WHITE

    def test_stop_pauses(self) -> None:
        clock = Clock(TimeControl(300, 0))
        clock.start(Color.WHITE)
        clock.stop()
        assert not clock.is_running

    def test_time_decreases(self) -> None:
        clock = Clock(TimeControl(300, 0))
        clock.start(Color.WHITE)
        time.sleep(0.05)
        remaining = clock.remaining(Color.WHITE)
        assert remaining < 300.0
        assert clock.remaining(Color.BLACK) == 300.0  # opponent not ticking

    def test_switch(self) -> None:
        clock = Clock(TimeControl(300, 0))
        clock.start(Color.WHITE)
        time.sleep(0.02)
        clock.switch()
        assert clock.active_color == Color.BLACK
        white_left = clock.remaining(Color.WHITE)
        assert white_left < 300.0
        # Black should start ticking now
        time.sleep(0.02)
        black_left = clock.remaining(Color.BLACK)
        assert black_left < 300.0


class TestClockIncrement:
    def test_fischer_increment(self) -> None:
        clock = Clock(TimeControl(300, 5))
        clock.start(Color.WHITE)
        clock.stop()
        clock.add_increment(Color.WHITE)
        assert clock.remaining(Color.WHITE) > 300.0 - 1  # at most ~1ms elapsed

    def test_increment_adds_up(self) -> None:
        clock = Clock(TimeControl(10, 2))
        clock.add_increment(Color.WHITE)
        clock.add_increment(Color.WHITE)
        assert clock.remaining(Color.WHITE) == 14.0


class TestClockFlagFall:
    def test_flag_not_fallen_initially(self) -> None:
        clock = Clock(TimeControl(300, 0))
        assert not clock.is_flag_fallen(Color.WHITE)

    def test_flag_falls_at_zero(self) -> None:
        clock = Clock(TimeControl(0.01, 0))
        clock.start(Color.WHITE)
        time.sleep(0.03)
        assert clock.is_flag_fallen(Color.WHITE)
        assert not clock.is_flag_fallen(Color.BLACK)


class TestClockUnlimited:
    def test_unlimited_is_infinite(self) -> None:
        clock = Clock(TimeControl.unlimited())
        assert clock.is_unlimited
        assert clock.remaining(Color.WHITE) == float("inf")

    def test_unlimited_no_flag(self) -> None:
        clock = Clock(TimeControl.unlimited())
        clock.start(Color.WHITE)
        assert not clock.is_flag_fallen(Color.WHITE)
