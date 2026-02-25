"""ClockWidget — dual chess clock display."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from chessie.core.enums import Color


class _SingleClock(QLabel):
    """Display for one player's time."""

    def __init__(self, color: Color, parent=None) -> None:
        super().__init__(parent)
        self._color = color
        self._active = False

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("JetBrains Mono", 22, QFont.Weight.Bold))
        self.setMinimumWidth(110)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._set_time_text(0.0)
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self.setStyleSheet(
                "background-color: #3a7d44; color: white; "
                "padding: 6px 12px; border-radius: 4px;"
            )
        else:
            self.setStyleSheet(
                "background-color: #2b2b2b; color: #aaa; "
                "padding: 6px 12px; border-radius: 4px;"
            )

    def set_low_time(self) -> None:
        if self._active:
            self.setStyleSheet(
                "background-color: #8b2020; color: white; "
                "padding: 6px 12px; border-radius: 4px;"
            )

    def _set_time_text(self, seconds: float) -> None:
        s = max(0.0, seconds)
        mins = int(s) // 60
        secs = int(s) % 60
        tenths = int((s * 10) % 10)
        if mins >= 10:
            self.setText(f"{mins}:{secs:02d}")
        else:
            self.setText(f"{mins}:{secs:02d}.{tenths}")

    def update_time(self, seconds: float) -> None:
        self._set_time_text(seconds)
        if seconds < 30.0 and self._active:
            self.set_low_time()


class ClockWidget(QWidget):
    """Combined dual clock widget."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._white_clock = _SingleClock(Color.WHITE)
        self._black_clock = _SingleClock(Color.BLACK)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        w_box = QVBoxLayout()
        w_label = QLabel("White")
        w_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w_label.setFont(QFont("Helvetica Neue", 9))
        w_box.addWidget(w_label)
        w_box.addWidget(self._white_clock)

        b_box = QVBoxLayout()
        b_label = QLabel("Black")
        b_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_label.setFont(QFont("Helvetica Neue", 9))
        b_box.addWidget(b_label)
        b_box.addWidget(self._black_clock)

        layout.addLayout(w_box)
        layout.addLayout(b_box)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._get_remaining: callable | None = None

    def start(self, get_remaining: callable) -> None:
        """Start updating. *get_remaining* returns (white_sec, black_sec)."""
        self._get_remaining = get_remaining
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_active(self, color: Color) -> None:
        self._white_clock.set_active(color == Color.WHITE)
        self._black_clock.set_active(color == Color.BLACK)

    def update_display(self, white_sec: float, black_sec: float) -> None:
        self._white_clock.update_time(white_sec)
        self._black_clock.update_time(black_sec)

    def reset(self, seconds: float) -> None:
        self.stop()
        self.update_display(seconds, seconds)
        self._white_clock.set_active(False)
        self._black_clock.set_active(False)

    def _tick(self) -> None:
        if self._get_remaining:
            w, b = self._get_remaining()
            self.update_display(w, b)
