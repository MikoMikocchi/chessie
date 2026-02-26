"""Tests for clock widget styling behavior."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from chessie.core.enums import Color
from chessie.ui.panels.clock_widget import _SingleClock

_APP = QApplication.instance() or QApplication([])


class TestSingleClock:
    def test_low_time_style_is_cleared_after_time_increase(self) -> None:
        assert _APP is not None
        clock = _SingleClock(Color.WHITE)
        clock.set_active(True)

        clock.update_time(10.0)
        assert "#8b2020" in clock.styleSheet()

        clock.update_time(45.0)
        assert "#8b2020" not in clock.styleSheet()
        assert "#3a7d44" in clock.styleSheet()
