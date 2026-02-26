"""ClockWidget — dual chess clock display."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from chessie.core.enums import Color
from chessie.ui.i18n import t


class _SingleClock(QLabel):
    """Display for one player's time."""

    def __init__(self, color: Color, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self._active = False
        self._is_low_time = False

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Adwaita Sans", 22, QFont.Weight.Bold))
        self.setMinimumWidth(110)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._set_time_text(None)
        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def set_low_time(self) -> None:
        self._is_low_time = True
        self._apply_style()

    def _apply_style(self) -> None:
        if not self._active:
            self.setStyleSheet(
                "background-color: #2b2b2b; color: #aaa; "
                "padding: 6px 12px; border-radius: 4px;"
            )
            return

        if self._is_low_time:
            self.setStyleSheet(
                "background-color: #8b2020; color: white; "
                "padding: 6px 12px; border-radius: 4px;"
            )
            return

        self.setStyleSheet(
            "background-color: #3a7d44; color: white; "
            "padding: 6px 12px; border-radius: 4px;"
        )

    def _set_time_text(self, seconds: float | None) -> None:
        if seconds is None:
            self.setText("∞")
            return
        s = max(0.0, seconds)
        mins = int(s) // 60
        secs = int(s) % 60
        tenths = int((s * 10) % 10)
        if mins >= 10:
            self.setText(f"{mins}:{secs:02d}")
        else:
            self.setText(f"{mins}:{secs:02d}.{tenths}")

    def update_time(self, seconds: float | None) -> None:
        self._set_time_text(seconds)
        self._is_low_time = seconds is not None and seconds < 30.0
        self._apply_style()


class ClockWidget(QWidget):
    """Combined dual clock widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._white_clock = _SingleClock(Color.WHITE)
        self._black_clock = _SingleClock(Color.BLACK)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        w_box = QVBoxLayout()
        self._w_label = QLabel()
        self._w_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._w_label.setFont(QFont("Adwaita Sans", 9))
        w_box.addWidget(self._w_label)
        w_box.addWidget(self._white_clock)

        b_box = QVBoxLayout()
        self._b_label = QLabel()
        self._b_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._b_label.setFont(QFont("Adwaita Sans", 9))
        b_box.addWidget(self._b_label)
        b_box.addWidget(self._black_clock)

        layout.addLayout(w_box)
        layout.addLayout(b_box)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._get_remaining: Callable[[], tuple[float, float]] | None = None

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._w_label.setText(s.clock_white)
        self._b_label.setText(s.clock_black)

    def start(self, get_remaining: Callable[[], tuple[float, float]]) -> None:
        """Start updating. *get_remaining* returns (white_sec, black_sec)."""
        self._get_remaining = get_remaining
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_active(self, color: Color) -> None:
        self._white_clock.set_active(color == Color.WHITE)
        self._black_clock.set_active(color == Color.BLACK)

    def update_display(self, white_sec: float | None, black_sec: float | None) -> None:
        self._white_clock.update_time(white_sec)
        self._black_clock.update_time(black_sec)

    def reset(self, seconds: float | None) -> None:
        self.stop()
        self.update_display(seconds, seconds)
        self._white_clock.set_active(False)
        self._black_clock.set_active(False)

    def _tick(self) -> None:
        if self._get_remaining:
            w, b = self._get_remaining()
            self.update_display(w, b)
