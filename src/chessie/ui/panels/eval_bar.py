"""EvalBar — vertical evaluation bar (future engine integration)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QSizePolicy, QWidget


class EvalBar(QWidget):
    """Vertical bar showing engine evaluation (-10 to +10 scale).

    White advantage → white fills from bottom.
    Black advantage → black fills from top.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._eval_cp: float = 0.0  # centipawns
        self._mate: int | None = None
        self.setFixedWidth(28)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(200)

    def set_eval(self, centipawns: float) -> None:
        """Set evaluation in centipawns (positive = white advantage)."""
        self._eval_cp = centipawns
        self._mate = None
        self.update()

    def set_mate(self, moves: int) -> None:
        """Set mate score (positive = white mates in N)."""
        self._mate = moves
        self._eval_cp = 1000.0 if moves > 0 else -1000.0
        self.update()

    def reset(self) -> None:
        self._eval_cp = 0.0
        self._mate = None
        self.update()

    def paintEvent(self, event) -> None:
        h = self.height()
        w = self.width()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background (black side)
        painter.fillRect(0, 0, w, h, QColor(50, 50, 50))

        # White portion: map eval (-1000..+1000cp) → (0..1)
        clamped = max(-1000.0, min(1000.0, self._eval_cp))
        ratio = (clamped + 1000.0) / 2000.0
        white_h = int(h * ratio)
        painter.fillRect(0, h - white_h, w, white_h, QColor(240, 240, 240))

        # Divider line
        painter.setPen(QColor(100, 100, 100))
        painter.drawLine(0, h - white_h, w, h - white_h)

        # Text label
        if self._mate is not None:
            text = f"M{abs(self._mate)}"
        else:
            pawns = self._eval_cp / 100.0
            text = f"{pawns:+.1f}"

        painter.setPen(QColor(120, 120, 120))
        font = QFont("Helvetica Neue", 8)
        painter.setFont(font)
        painter.drawText(0, 0, w, 18, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()
