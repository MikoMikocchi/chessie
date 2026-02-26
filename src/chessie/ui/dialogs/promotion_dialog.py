"""Promotion dialog — lets user pick the promotion piece."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chessie.core.enums import Color, PieceType
from chessie.core.piece import Piece
from chessie.ui.i18n import t
from chessie.ui.resources import piece_pixmap


class PromotionDialog(QDialog):
    """Modal dialog to select promotion piece type."""

    def __init__(self, color: Color, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setFixedSize(340, 130)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._selected: PieceType = PieceType.QUEEN

        layout = QVBoxLayout(self)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont("Adwaita Sans", 11))
        layout.addWidget(self._label)

        btn_row = QHBoxLayout()
        icon_size = 56
        for pt in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
            pixmap = piece_pixmap(Piece(color, pt), icon_size)
            btn = QPushButton()
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(pixmap.size())
            btn.setFixedSize(68, 68)
            btn.setToolTip(pt.name.capitalize())
            btn.clicked.connect(lambda checked, p=pt: self._choose(p))
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        s = t()
        self.setWindowTitle(s.promote_title)
        self._label.setText(s.promote_label)

    def _choose(self, piece_type: PieceType) -> None:
        self._selected = piece_type
        self.accept()

    @property
    def selected(self) -> PieceType:
        return self._selected

    @staticmethod
    def ask(color: Color, parent: QWidget | None = None) -> PieceType | None:
        """Show the dialog and return the chosen piece type, or ``None`` on cancel."""
        dlg = PromotionDialog(color, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.selected
        return None
