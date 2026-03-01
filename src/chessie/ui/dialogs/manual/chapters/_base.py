"""Base utilities for manual chapters.

Every chapter module creates a :class:`ChapterProvider` subclass.  This
module supplies helper functions shared by all chapters:

* ``wrap_page``   – wraps a body HTML fragment in a full document with the
  manual stylesheet.
* ``fen_diagram`` – generates the ``<img>`` snippet for a FEN board.
* ``MANUAL_CSS``  – common stylesheet used across all pages.
"""

from __future__ import annotations

MANUAL_CSS = """\
body {
    background: #202122;
    color: #eaecf0;
    font-family: 'Adwaita Sans', sans-serif;
    font-size: 14px;
    line-height: 1.5;
    margin: 0;
    padding: 12px 16px 14px 16px;
}
h1 {
    color: #f8e2be;
    font-size: 22px;
    border-bottom: 1px solid #54595d;
    padding-bottom: 5px;
    margin: 4px 0 10px;
}
h2 {
    color: #f3d4a8;
    font-size: 18px;
    margin: 12px 0 6px;
}
h3 {
    color: #d9dde3;
    font-size: 15px;
    margin: 10px 0 4px;
}
p {
    margin: 5px 0 8px;
}
ul, ol {
    margin: 4px 0 8px;
    padding-left: 24px;
}
li {
    margin: 3px 0;
}
.board-diagram {
    display: inline-block;
    width: 228px;
    margin: 0;
    padding: 6px;
    background: #2a2d31;
    border: 1px solid #54595d;
    border-radius: 3px;
    text-align: center;
    vertical-align: top;
}
.board-diagram img {
    width: 220px;
    height: 220px;
    border: 1px solid #54595d;
}
table.board-wrap {
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 10px;
    border: none;
    background: transparent;
}
table.board-wrap td {
    text-align: right;
    border: none;
    background: transparent;
    padding: 0;
}
.board-caption {
    margin-top: 4px;
    color: #c8ccd1;
    font-size: 12px;
    font-style: italic;
    line-height: 1.35;
}
.highlight-box {
    background: #2b3036;
    border-left: 3px solid #c8a25c;
    padding: 9px 12px;
    margin: 9px 0;
    border-radius: 0 4px 4px 0;
}
.note {
    background: #243447;
    border-left: 3px solid #6aa8e8;
    padding: 9px 12px;
    margin: 9px 0;
    border-radius: 0 4px 4px 0;
    font-style: italic;
}
.move {
    font-family: 'Adwaita Mono Nerd Font', 'Consolas', monospace;
    background: #30363d;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
}
a {
    color: #8cbcf7;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
table {
    border-collapse: collapse;
    margin: 8px 0 10px;
    background: #2a2d31;
}
th, td {
    border: 1px solid #54595d;
    padding: 5px 10px;
    text-align: center;
}
th {
    background: #30353a;
    color: #f8e2be;
}
td {
    background: #26292d;
}
"""


def wrap_page(body: str, *, anchor: str = "") -> str:
    """Wrap a body HTML fragment in a complete page with the manual CSS."""
    anchor_tag = f'<a name="{anchor}"></a>' if anchor else ""
    return (
        "<!DOCTYPE html><html><head>"
        f"<style>{MANUAL_CSS}</style>"
        f"</head><body>{anchor_tag}{body}</body></html>"
    )


def fen_diagram(
    fen: str,
    caption: str = "",
    highlights: str = "",
) -> str:
    """Return an HTML ``<div>`` containing a FEN board image.

    Parameters
    ----------
    fen:
        FEN position string (at least the placement part).
    caption:
        Optional caption displayed below the diagram.
    highlights:
        Comma-separated algebraic squares to highlight, e.g. ``"e4,d5"``.
    """
    src = f"fen:{fen}"
    if highlights:
        src += f"|{highlights}"
    html = '<table class="board-wrap" cellspacing="0" cellpadding="0"><tr><td>'
    html += '<div class="board-diagram">'
    html += f'<img src="{src}" width="220" height="220">'
    if caption:
        html += f'<div class="board-caption">{caption}</div>'
    html += "</div></td></tr></table>"
    return html
