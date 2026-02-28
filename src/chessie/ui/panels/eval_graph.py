"""EvalGraph — interactive evaluation chart showing advantage over time."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QResizeEvent,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget


class EvalGraph(QWidget):
    """Horizontal evaluation graph with clickable move markers.

    Positive values = white advantage (drawn above centre).
    Negative values = black advantage (drawn below centre).
    """

    ply_clicked = pyqtSignal(int)

    _BG = QColor(38, 38, 38)
    _GRID_LINE = QColor(60, 60, 60)
    _CENTER_LINE = QColor(90, 90, 90)
    _WHITE_FILL_TOP = QColor(245, 245, 245, 120)
    _WHITE_FILL_BOT = QColor(200, 200, 200, 40)
    _BLACK_FILL_TOP = QColor(50, 50, 50, 40)
    _BLACK_FILL_BOT = QColor(30, 30, 30, 120)
    _LINE_COLOR = QColor(180, 200, 220)
    _CURSOR_COLOR = QColor(100, 160, 255, 160)
    _MARGIN_LEFT = 28
    _MARGIN_RIGHT = 6
    _MARGIN_TOP = 6
    _MARGIN_BOTTOM = 14
    _MAX_EVAL = 600.0  # centipawns clamp

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._evals: list[float] = []  # white-relative centipawns per ply
        self._marker_colors: list[QColor | None] = []
        self._active_ply: int | None = None
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── Public API ───────────────────────────────────────────────────────

    def set_data(
        self,
        evals: list[float],
        marker_colors: list[QColor | None] | None = None,
    ) -> None:
        """Set evaluation data. *evals* is per-ply white-relative centipawns."""
        self._evals = list(evals)
        self._marker_colors = list(marker_colors) if marker_colors else []
        self.update()

    def set_active_ply(self, ply: int | None) -> None:
        self._active_ply = ply
        self.update()

    def clear(self) -> None:
        self._evals.clear()
        self._marker_colors.clear()
        self._active_ply = None
        self.update()

    # ── Coordinate helpers ───────────────────────────────────────────────

    def _chart_rect(self) -> QRectF:
        return QRectF(
            self._MARGIN_LEFT,
            self._MARGIN_TOP,
            self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT,
            self.height() - self._MARGIN_TOP - self._MARGIN_BOTTOM,
        )

    def _ply_to_x(self, ply: int, rect: QRectF) -> float:
        n = max(1, len(self._evals) - 1)
        return rect.left() + (ply / n) * rect.width()

    def _eval_to_y(self, ev: float, rect: QRectF) -> float:
        clamped = max(-self._MAX_EVAL, min(self._MAX_EVAL, ev))
        ratio = 0.5 - clamped / (2.0 * self._MAX_EVAL)
        return rect.top() + ratio * rect.height()

    # ── Painting ─────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent | None) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, self._BG)

        rect = self._chart_rect()
        if len(self._evals) < 2:
            self._draw_empty(p, rect)
            p.end()
            return

        # Centre line
        cy = self._eval_to_y(0, rect)
        p.setPen(QPen(self._CENTER_LINE, 1, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(rect.left(), cy), QPointF(rect.right(), cy))

        # Grid lines at ±100, ±300 cp
        p.setPen(QPen(self._GRID_LINE, 0.5, Qt.PenStyle.DotLine))
        for grid_val in (-300, -100, 100, 300):
            gy = self._eval_to_y(grid_val, rect)
            if rect.top() <= gy <= rect.bottom():
                p.drawLine(QPointF(rect.left(), gy), QPointF(rect.right(), gy))

        # Build curve points
        points = [
            QPointF(self._ply_to_x(i, rect), self._eval_to_y(ev, rect))
            for i, ev in enumerate(self._evals)
        ]

        # Filled area: white above centre, black below
        white_path = QPainterPath()
        white_path.moveTo(QPointF(points[0].x(), cy))
        for pt in points:
            y = min(pt.y(), cy)
            white_path.lineTo(QPointF(pt.x(), y))
        white_path.lineTo(QPointF(points[-1].x(), cy))
        white_path.closeSubpath()

        white_grad = QLinearGradient(0, rect.top(), 0, cy)
        white_grad.setColorAt(0, self._WHITE_FILL_TOP)
        white_grad.setColorAt(1, self._WHITE_FILL_BOT)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(white_grad))
        p.drawPath(white_path)

        black_path = QPainterPath()
        black_path.moveTo(QPointF(points[0].x(), cy))
        for pt in points:
            y = max(pt.y(), cy)
            black_path.lineTo(QPointF(pt.x(), y))
        black_path.lineTo(QPointF(points[-1].x(), cy))
        black_path.closeSubpath()

        black_grad = QLinearGradient(0, cy, 0, rect.bottom())
        black_grad.setColorAt(0, self._BLACK_FILL_TOP)
        black_grad.setColorAt(1, self._BLACK_FILL_BOT)
        p.setBrush(QBrush(black_grad))
        p.drawPath(black_path)

        # Main evaluation line
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)
        p.setPen(QPen(self._LINE_COLOR, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(line_path)

        # Colored markers for judgments
        for i, color in enumerate(self._marker_colors):
            if color is None or i >= len(points):
                continue
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(points[i], 3.5, 3.5)

        # Active ply cursor
        if self._active_ply is not None and 0 <= self._active_ply < len(points):
            ax = points[self._active_ply].x()
            p.setPen(QPen(self._CURSOR_COLOR, 1.5))
            p.drawLine(QPointF(ax, rect.top()), QPointF(ax, rect.bottom()))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(self._CURSOR_COLOR))
            p.drawEllipse(points[self._active_ply], 4.0, 4.0)

        # Y-axis labels
        font = QFont("Adwaita Sans", 7)
        p.setFont(font)
        p.setPen(QColor(140, 140, 140))
        for label_val in (-3, -1, 0, 1, 3):
            ly = self._eval_to_y(label_val * 100, rect)
            text = f"{label_val:+d}" if label_val != 0 else "0"
            p.drawText(
                QRectF(0, ly - 6, self._MARGIN_LEFT - 4, 12),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

        # X-axis move numbers (every 5 moves)
        total_plies = len(self._evals)
        for ply in range(0, total_plies, 10):
            move_no = ply // 2 + 1
            mx = self._ply_to_x(ply, rect)
            p.drawText(
                QRectF(mx - 10, rect.bottom() + 1, 20, 12),
                Qt.AlignmentFlag.AlignCenter,
                str(move_no),
            )

        p.end()

    def _draw_empty(self, p: QPainter, rect: QRectF) -> None:
        p.setPen(QColor(100, 100, 100))
        font = QFont("Adwaita Sans", 9)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "—")

    # ── Mouse interaction ────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None or not self._evals:
            return
        rect = self._chart_rect()
        x = event.position().x()
        n = len(self._evals)
        if n < 2 or rect.width() <= 0:
            return
        ratio = (x - rect.left()) / rect.width()
        ply = max(0, min(n - 1, round(ratio * (n - 1))))
        self._active_ply = ply
        self.update()
        self.ply_clicked.emit(ply)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self.update()
