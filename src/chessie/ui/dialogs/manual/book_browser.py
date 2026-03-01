"""QTextBrowser subclass with FEN diagram support and manual link navigation.

Image sources matching ``fen:<PLACEMENT>`` or ``fen:<PLACEMENT>|sq1,sq2``
are automatically rendered to board diagrams before the HTML is displayed.

Anchor links of the form ``manual:<chapter_id>#<anchor>`` are emitted via
the ``manual_link_clicked`` signal so the parent dialog can navigate across
chapters.
"""

from __future__ import annotations

import re
from typing import Any

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QTextBrowser

from chessie.ui.dialogs.manual.fen_renderer import render_fen_board

_FEN_RE = re.compile(r'src="fen:([^"]+)"')


class BookBrowser(QTextBrowser):
    """Rich-text browser that renders inline FEN board diagrams.

    Signals
    -------
    manual_link_clicked(chapter_id, anchor)
        Emitted when a ``manual:`` cross-chapter link is clicked.
    """

    manual_link_clicked = pyqtSignal(str, str)

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._on_anchor_clicked)

    # ── public ───────────────────────────────────────────────────────

    def set_page_html(self, html: str) -> None:
        """Set page content, pre-rendering any ``fen:`` image references."""
        self._register_fen_images(html)
        self.setHtml(html)

    # ── internals ────────────────────────────────────────────────────

    def _register_fen_images(self, html: str) -> None:
        """Scan *html* for ``fen:`` image sources and add pixmap resources."""
        doc = self.document()
        assert doc is not None
        for match in _FEN_RE.finditer(html):
            raw = match.group(1)
            try:
                fen, highlights = _parse_fen_src(raw)
                pixmap = render_fen_board(
                    fen,
                    board_size=220,
                    highlights=highlights,
                )
            except ValueError:
                # Keep page rendering even if a single diagram is malformed.
                continue
            url = QUrl(f"fen:{raw}")
            doc.addResource(
                QTextDocument.ResourceType.ImageResource.value,
                url,
                pixmap,
            )

    def _on_anchor_clicked(self, url: QUrl) -> None:
        scheme = url.scheme()
        if scheme == "manual":
            chapter_id = url.host() or url.path().lstrip("/")
            anchor = url.fragment() or ""
            self.manual_link_clicked.emit(chapter_id, anchor)
        elif scheme == "" or scheme == "about":
            # Internal anchor within same page
            frag = url.fragment()
            if frag:
                self.scrollToAnchor(frag)
        # ignore http/https (no external browser)


def _parse_fen_src(raw: str) -> tuple[str, tuple[str, ...]]:
    """Split ``'FEN|sq1,sq2'`` into ``(fen, highlights)``."""
    if "|" in raw:
        fen, hl = raw.split("|", 1)
        return fen, tuple(s.strip() for s in hl.split(",") if s.strip())
    return raw, ()
