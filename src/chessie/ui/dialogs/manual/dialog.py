"""ManualDialog — the in-game chess manual window.

A non-modal dialog with:
* **sidebar** – chapter list with a Table-of-Contents entry at the top;
* **browser** – rich-text page view with FEN board diagrams;
* **nav bar** – previous / next page buttons and a page indicator.

Cross-chapter anchor links (``manual:<chapter_id>#<anchor>``) are handled
automatically by navigating to the target chapter and page.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chessie.ui.dialogs.manual.book_browser import BookBrowser
from chessie.ui.dialogs.manual.chapters import ALL_CHAPTERS
from chessie.ui.dialogs.manual.chapters._base import wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider
from chessie.ui.i18n import current_language, t

_TOC_ID = "__toc__"


class ManualDialog(QDialog):
    """In-game chess manual dialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self.setMinimumSize(820, 560)
        self.resize(960, 640)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._lang = current_language()
        self._providers: list[ChapterProvider] = list(ALL_CHAPTERS)
        self._chapters: list[Chapter] = [p.build(self._lang) for p in self._providers]
        self._chapter_idx = -1  # selected chapter (-1 = TOC)
        self._page_idx = 0

        self._setup_ui()
        self.retranslate_ui()

        # Start on TOC
        self._sidebar.setCurrentRow(0)

    # ── UI construction ──────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- sidebar ---
        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet(
            """
            QListWidget {
                background: #252526;
                border: none;
                border-right: 1px solid #3c3c3c;
                font-size: 13px;
                padding-top: 6px;
            }
            QListWidget::item {
                color: #cccccc;
                padding: 8px 12px;
            }
            QListWidget::item:selected {
                background: #37373d;
                color: #f0d9b5;
                border-left: 3px solid #b58863;
            }
            QListWidget::item:hover {
                background: #2a2d2e;
            }
            """
        )
        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        root.addWidget(self._sidebar)

        # --- main content area ---
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        self._browser = BookBrowser()
        self._browser.setStyleSheet(
            """
            QTextBrowser {
                background: #1e1e1e;
                border: none;
            }
            """
        )
        self._browser.manual_link_clicked.connect(self._on_manual_link)
        content.addWidget(self._browser, stretch=1)

        # --- navigation bar ---
        nav = QHBoxLayout()
        nav.setContentsMargins(12, 6, 12, 8)

        self._btn_prev = QPushButton("◁")
        self._btn_prev.setFixedSize(40, 32)
        self._btn_prev.setFont(QFont("Adwaita Sans", 14))
        self._btn_prev.clicked.connect(self._prev_page)

        self._btn_next = QPushButton("▷")
        self._btn_next.setFixedSize(40, 32)
        self._btn_next.setFont(QFont("Adwaita Sans", 14))
        self._btn_next.clicked.connect(self._next_page)

        self._page_label = QLabel()
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setStyleSheet("color: #888; font-size: 12px;")

        nav.addStretch()
        nav.addWidget(self._btn_prev)
        nav.addWidget(self._page_label)
        nav.addWidget(self._btn_next)
        nav.addStretch()

        content.addLayout(nav)
        root.addLayout(content, stretch=1)

    # ── i18n ─────────────────────────────────────────────────────────

    def retranslate_ui(self) -> None:
        s = t()
        self.setWindowTitle(s.manual_title)

        # Rebuild chapters for current language
        self._lang = current_language()
        self._chapters = [p.build(self._lang) for p in self._providers]

        # Rebuild sidebar preserving selection
        old_row = self._sidebar.currentRow()
        self._sidebar.blockSignals(True)
        self._sidebar.clear()

        toc_item = QListWidgetItem(f"📖  {s.manual_toc}")
        toc_item.setData(Qt.ItemDataRole.UserRole, _TOC_ID)
        self._sidebar.addItem(toc_item)

        for ch in self._chapters:
            item = QListWidgetItem(f"   {ch.title}")
            item.setData(Qt.ItemDataRole.UserRole, ch.chapter_id)
            self._sidebar.addItem(item)

        self._sidebar.blockSignals(False)
        self._sidebar.setCurrentRow(max(0, old_row))

        self._refresh_page()

    # ── navigation ───────────────────────────────────────────────────

    def _on_sidebar_changed(self, row: int) -> None:
        if row < 0:
            return
        if row == 0:
            self._chapter_idx = -1
        else:
            self._chapter_idx = row - 1
        self._page_idx = 0
        self._refresh_page()

    def _prev_page(self) -> None:
        if self._page_idx > 0:
            self._page_idx -= 1
            self._refresh_page()

    def _next_page(self) -> None:
        total = self._current_page_count()
        if self._page_idx < total - 1:
            self._page_idx += 1
            self._refresh_page()

    def _on_manual_link(self, chapter_id: str, anchor: str) -> None:
        """Navigate to a cross-chapter link."""
        for idx, ch in enumerate(self._chapters):
            if ch.chapter_id == chapter_id:
                self._chapter_idx = idx
                # If anchor specified, find the page
                page = ch.page_for_anchor(anchor) if anchor else 0
                self._page_idx = page if page is not None else 0

                self._sidebar.blockSignals(True)
                self._sidebar.setCurrentRow(idx + 1)  # +1 for TOC row
                self._sidebar.blockSignals(False)

                self._refresh_page()
                return

    # ── page rendering ───────────────────────────────────────────────

    def _refresh_page(self) -> None:
        if self._chapter_idx < 0:
            html = self._build_toc_html()
        else:
            ch = self._chapters[self._chapter_idx]
            if self._page_idx < len(ch.pages):
                html = ch.pages[self._page_idx].html
            else:
                html = wrap_page("<p>—</p>")

        self._browser.set_page_html(html)
        self._update_nav()

    def _update_nav(self) -> None:
        total = self._current_page_count()
        current = self._page_idx + 1

        self._btn_prev.setEnabled(self._page_idx > 0)
        self._btn_next.setEnabled(self._page_idx < total - 1)

        s = t()
        self._page_label.setText(s.manual_page_of.format(current=current, total=total))

    def _current_page_count(self) -> int:
        if self._chapter_idx < 0:
            return 1  # TOC is one page
        return max(1, len(self._chapters[self._chapter_idx].pages))

    # ── Table of Contents ────────────────────────────────────────────

    def _build_toc_html(self) -> str:
        s = t()
        body = f"<h1>{s.manual_toc}</h1>"
        for ch in self._chapters:
            body += f'<h2><a href="manual:{ch.chapter_id}">{ch.title}</a></h2><ul>'
            for page in ch.pages:
                label = self._extract_title(page.html)
                if page.anchor:
                    body += (
                        f'<li><a href="manual:{ch.chapter_id}#{page.anchor}">'
                        f"{label}</a></li>"
                    )
                else:
                    body += f"<li>{label}</li>"
            body += "</ul>"
        return wrap_page(body)

    @staticmethod
    def _extract_title(html: str) -> str:
        """Extract the first <h1> or <h2> text from an HTML string."""
        import re

        m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", html)
        if m:
            # Strip inner tags
            return re.sub(r"<[^>]+>", "", m.group(1))
        return "—"

    # ── static entry point ───────────────────────────────────────────

    @staticmethod
    def show_manual(parent: QWidget | None = None) -> ManualDialog:
        """Create and show the manual dialog (non-modal)."""
        dlg = ManualDialog(parent)
        dlg.show()
        return dlg
