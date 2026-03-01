"""Settings dialog container widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from chessie.ui.dialogs.settings.models import AppSettings
from chessie.ui.dialogs.settings.pages import PAGE_FACTORIES, SettingsPage
from chessie.ui.i18n import t


class SettingsDialog(QDialog):
    """Modal settings dialog with a left category list and stacked pages."""

    def __init__(
        self,
        settings: AppSettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(720, 460)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._settings = settings
        self._pages: list[SettingsPage] = []
        self._page_attr_names: list[str] = []

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(150)
        self._sidebar.setStyleSheet(
            "QListWidget { background: #1e1e1e; border: none;"
            "  border-right: 1px solid #3c3c3c; }"
            "QListWidget::item { padding: 10px 14px; color: #c0c0c0; font-size: 13px; }"
            "QListWidget::item:selected { background: #264f78; color: #ffffff; }"
        )

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #2b2b2b;")

        for attr, page_class in PAGE_FACTORIES:
            self._page_attr_names.append(attr)
            item = QListWidgetItem()
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self._sidebar.addItem(item)

            page = page_class(self._settings)
            self._pages.append(page)
            self._stack.addWidget(page)

        self._sidebar.setCurrentRow(0)
        self._sidebar.currentRowChanged.connect(self._stack.setCurrentIndex)

        root.addWidget(self._sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._stack)

        self._btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._btn_box.setContentsMargins(12, 8, 12, 8)
        self._btn_box.accepted.connect(self._on_accept)
        self._btn_box.rejected.connect(self.reject)
        right.addWidget(self._btn_box)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget)

    def retranslate_ui(self) -> None:
        s = t()
        self.setWindowTitle(s.settings_title)
        for i, attr in enumerate(self._page_attr_names):
            item = self._sidebar.item(i)
            if item is not None:
                item.setText(getattr(s, attr))
        for page in self._pages:
            page.retranslate_ui()

    def _on_accept(self) -> None:
        for page in self._pages:
            page.apply(self._settings)
        self.accept()
