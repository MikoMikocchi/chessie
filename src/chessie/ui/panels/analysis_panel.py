"""AnalysisPanel — integrated analysis result display.

Shows accuracy summary, move details, and best-move suggestions
within the main window (not a dialog).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from chessie.analysis.models import (
    GameAnalysisReport,
    MoveJudgment,
    SideAnalysisSummary,
)
from chessie.ui.i18n import t

# ── Small reusable sub-widgets ──────────────────────────────────────────


class _AccuracyBar(QWidget):
    """Horizontal accuracy indicator with percentage label."""

    def __init__(
        self,
        label: str,
        color: QColor,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._label = QLabel(label)
        self._label.setFont(QFont("Adwaita Sans", 10, QFont.Weight.Bold))
        self._label.setFixedWidth(60)
        self._label.setStyleSheet("color: #c0c0c0;")
        layout.addWidget(self._label)

        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(14)
        bar_hex = color.name()
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: #333;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {bar_hex};
                border-radius: 4px;
            }}
            """
        )
        layout.addWidget(self._bar, stretch=1)

        self._pct = QLabel("—")
        self._pct.setFont(QFont("Adwaita Sans", 10, QFont.Weight.Bold))
        self._pct.setFixedWidth(46)
        self._pct.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._pct.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._pct)

    def set_label(self, text: str) -> None:
        self._label.setText(text)

    def set_accuracy(self, pct: float) -> None:
        self._bar.setValue(int(pct * 10))
        self._pct.setText(f"{pct:.1f}%")


class _JudgmentRow(QWidget):
    """Single row showing a judgment icon, count, and label."""

    def __init__(
        self,
        judgment: MoveJudgment,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)

        nag = judgment.nag or "★"
        color = judgment.color_hex

        self._icon = QLabel(nag)
        self._icon.setFont(QFont("Adwaita Sans", 11, QFont.Weight.Bold))
        self._icon.setFixedWidth(22)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet(f"color: {color};")
        layout.addWidget(self._icon)

        self._name = QLabel(judgment.value)
        self._name.setFont(QFont("Adwaita Sans", 9))
        self._name.setStyleSheet("color: #b0b0b0;")
        layout.addWidget(self._name, stretch=1)

        self._count = QLabel("0")
        self._count.setFont(QFont("Adwaita Sans", 10, QFont.Weight.Bold))
        self._count.setFixedWidth(24)
        self._count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count.setStyleSheet(f"color: {color};")
        layout.addWidget(self._count)

    def set_count(self, n: int) -> None:
        self._count.setText(str(n))


# ── Main panel ──────────────────────────────────────────────────────────


class AnalysisPanel(QWidget):
    """Complete analysis view shown inside the main window right panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._report: GameAnalysisReport | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ── Title ──
        self._title = QLabel()
        self._title.setFont(QFont("Adwaita Sans", 12, QFont.Weight.Bold))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("color: #e0e0e0;")
        root.addWidget(self._title)

        # ── Accuracy bars ──
        self._white_bar = _AccuracyBar("♔", QColor(240, 240, 240))
        self._black_bar = _AccuracyBar("♚", QColor(100, 100, 100))
        root.addWidget(self._white_bar)
        root.addWidget(self._black_bar)

        # ── Judgment stats (two columns: white | black) ──
        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            """
            QFrame {
                background: #2a2a2a;
                border-radius: 6px;
                padding: 4px;
            }
            """
        )
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(4, 4, 4, 4)
        stats_layout.setSpacing(10)

        # White column
        w_col = QVBoxLayout()
        w_col.setSpacing(1)
        self._white_rows: dict[MoveJudgment, _JudgmentRow] = {}
        for j in (
            MoveJudgment.BRILLIANT,
            MoveJudgment.GREAT,
            MoveJudgment.BEST,
            MoveJudgment.INACCURACY,
            MoveJudgment.MISTAKE,
            MoveJudgment.BLUNDER,
        ):
            row = _JudgmentRow(j)
            self._white_rows[j] = row
            w_col.addWidget(row)
        stats_layout.addLayout(w_col, stretch=1)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #444;")
        stats_layout.addWidget(sep)

        # Black column
        b_col = QVBoxLayout()
        b_col.setSpacing(1)
        self._black_rows: dict[MoveJudgment, _JudgmentRow] = {}
        for j in (
            MoveJudgment.BRILLIANT,
            MoveJudgment.GREAT,
            MoveJudgment.BEST,
            MoveJudgment.INACCURACY,
            MoveJudgment.MISTAKE,
            MoveJudgment.BLUNDER,
        ):
            row = _JudgmentRow(j)
            self._black_rows[j] = row
            b_col.addWidget(row)
        stats_layout.addLayout(b_col, stretch=1)

        root.addWidget(stats_frame)

        # ── Move info (selected move details) ──
        self._move_info_frame = QFrame()
        self._move_info_frame.setStyleSheet(
            """
            QFrame {
                background: #2a2a2a;
                border-radius: 6px;
                padding: 6px;
            }
            """
        )
        mi_layout = QVBoxLayout(self._move_info_frame)
        mi_layout.setContentsMargins(8, 6, 8, 6)
        mi_layout.setSpacing(4)

        self._move_info_title = QLabel()
        self._move_info_title.setFont(QFont("Adwaita Sans", 10, QFont.Weight.Bold))
        self._move_info_title.setStyleSheet("color: #d0d0d0;")
        mi_layout.addWidget(self._move_info_title)

        self._move_played_label = QLabel()
        self._move_played_label.setFont(QFont("Adwaita Sans", 10))
        self._move_played_label.setStyleSheet("color: #b0b0b0;")
        self._move_played_label.setWordWrap(True)
        mi_layout.addWidget(self._move_played_label)

        self._move_best_label = QLabel()
        self._move_best_label.setFont(QFont("Adwaita Sans", 10))
        self._move_best_label.setStyleSheet("color: #9bc700;")
        self._move_best_label.setWordWrap(True)
        mi_layout.addWidget(self._move_best_label)

        self._move_eval_label = QLabel()
        self._move_eval_label.setFont(QFont("Adwaita Sans", 9))
        self._move_eval_label.setStyleSheet("color: #888;")
        mi_layout.addWidget(self._move_eval_label)

        root.addWidget(self._move_info_frame)
        self._move_info_frame.hide()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self._title.setText(s.analysis_title)

    # ── Public API ───────────────────────────────────────────────────────

    def set_report(self, report: GameAnalysisReport) -> None:
        """Populate the panel from a completed analysis report."""
        self._report = report
        self._white_bar.set_accuracy(report.white.accuracy)
        self._black_bar.set_accuracy(report.black.accuracy)
        self._populate_side(self._white_rows, report.white)
        self._populate_side(self._black_rows, report.black)
        self._move_info_frame.hide()

    def show_move_info(self, ply: int) -> None:
        """Display best-move suggestion for the given ply."""
        if self._report is None or ply < 0 or ply >= len(self._report.moves):
            self._move_info_frame.hide()
            return

        ma = self._report.moves[ply]
        s = t()
        move_num = f"{(ply // 2) + 1}{'.' if ply % 2 == 0 else '...'}"
        nag = ma.judgment.nag
        color_hex = ma.judgment.color_hex
        nag_display = f' <span style="color:{color_hex};">{nag}</span>' if nag else ""

        self._move_info_title.setText(
            f"{s.analysis_move_title}: {move_num} {ma.played_san}{nag_display}"
        )
        self._move_info_title.setTextFormat(Qt.TextFormat.RichText)

        self._move_played_label.setText(
            f"{s.analysis_col_played}: {ma.played_san}"
            f' <span style="color:{color_hex};">({ma.judgment.value},'
            f" CPL {ma.cp_loss})</span>"
        )
        self._move_played_label.setTextFormat(Qt.TextFormat.RichText)

        if ma.best_san and ma.best_san != ma.played_san:
            self._move_best_label.setText(f"{s.analysis_col_best}: {ma.best_san}")
            self._move_best_label.show()
        else:
            self._move_best_label.hide()

        before_pawn = ma.eval_before_white_cp / 100.0
        after_pawn = ma.eval_after_white_cp / 100.0
        self._move_eval_label.setText(f"Eval: {before_pawn:+.2f} → {after_pawn:+.2f}")

        self._move_info_frame.show()

    def clear(self) -> None:
        """Reset the panel."""
        self._report = None
        self._white_bar.set_accuracy(0.0)
        self._black_bar.set_accuracy(0.0)
        for row in self._white_rows.values():
            row.set_count(0)
        for row in self._black_rows.values():
            row.set_count(0)
        self._move_info_frame.hide()

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _populate_side(
        rows: dict[MoveJudgment, _JudgmentRow],
        summary: SideAnalysisSummary,
    ) -> None:
        counts = {
            MoveJudgment.BRILLIANT: summary.brilliant,
            MoveJudgment.GREAT: summary.great,
            MoveJudgment.BEST: summary.best,
            MoveJudgment.INACCURACY: summary.inaccuracies,
            MoveJudgment.MISTAKE: summary.mistakes,
            MoveJudgment.BLUNDER: summary.blunders,
        }
        for j, row in rows.items():
            row.set_count(counts.get(j, 0))
