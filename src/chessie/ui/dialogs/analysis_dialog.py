"""Dialog for presenting game analysis results."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chessie.analysis import GameAnalysisReport
from chessie.ui.i18n import t


class AnalysisDialog(QDialog):
    """Displays a completed move-by-move game analysis report."""

    def __init__(
        self,
        report: GameAnalysisReport,
        *,
        on_jump_to_ply: Callable[[int], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._report = report
        self._on_jump_to_ply = on_jump_to_ply
        self._setup_ui()
        self.retranslate_ui()
        self._populate()

    def _setup_ui(self) -> None:
        self.setModal(False)
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self._summary = QLabel()
        self._summary.setWordWrap(True)
        self._summary.setFont(QFont("Adwaita Sans", 10))
        layout.addWidget(self._summary)

        self._table = QTableWidget(0, 5, self)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        vertical_header = self._table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        horizontal_header = self._table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setStretchLastSection(True)
        layout.addWidget(self._table, stretch=1)

        hints = QHBoxLayout()
        self._hint = QLabel()
        self._hint.setStyleSheet("color: #9a9a9a;")
        hints.addWidget(self._hint)
        hints.addStretch()
        layout.addLayout(hints)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._buttons.rejected.connect(self.reject)
        self._buttons.accepted.connect(self.accept)
        layout.addWidget(self._buttons)

    def retranslate_ui(self) -> None:
        s = t()
        self.setWindowTitle(s.analysis_title)
        self._table.setHorizontalHeaderLabels(
            [
                s.analysis_col_move,
                s.analysis_col_played,
                s.analysis_col_best,
                s.analysis_col_cp_loss,
                s.analysis_col_verdict,
            ]
        )
        self._hint.setText(s.analysis_hint_jump)

    def _populate(self) -> None:
        report = self._report
        self._table.setRowCount(len(report.moves))
        for row, move in enumerate(report.moves):
            move_no = f"{(move.ply // 2) + 1}{'.' if move.ply % 2 == 0 else '...'}"
            best = move.best_san if move.best_san is not None else "-"
            items = [
                QTableWidgetItem(move_no),
                QTableWidgetItem(move.played_san),
                QTableWidgetItem(best),
                QTableWidgetItem(str(move.cp_loss)),
                QTableWidgetItem(move.judgment.value),
            ]
            for col, item in enumerate(items):
                align = (
                    Qt.AlignmentFlag.AlignCenter
                    if col in (0, 3)
                    else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                item.setTextAlignment(int(align))
                self._table.setItem(row, col, item)

        self._table.resizeColumnsToContents()

        s = t()
        self._summary.setText(
            s.analysis_summary.format(
                white_avg=f"{report.white.avg_cp_loss:.1f}",
                black_avg=f"{report.black.avg_cp_loss:.1f}",
                white_blunders=report.white.blunders,
                black_blunders=report.black.blunders,
            )
        )

    def _on_cell_double_clicked(self, row: int, _col: int) -> None:
        if self._on_jump_to_ply is None:
            return
        if row < 0 or row >= len(self._report.moves):
            return
        self._on_jump_to_ply(self._report.moves[row].ply)
