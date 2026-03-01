"""Tests for manual chapter content and FEN diagram rendering safety."""

from __future__ import annotations

import re
from pathlib import Path

from chessie.core.notation import position_from_fen
from chessie.core.rules import Rules
from chessie.ui.dialogs.manual.chapters._base import fen_diagram
from chessie.ui.dialogs.manual.chapters.ch02_pieces import PiecesChapter
from chessie.ui.dialogs.manual.chapters.ch05_tactics import TacticsChapter
from chessie.ui.dialogs.manual.chapters.ch06_openings import OpeningsChapter
from chessie.ui.dialogs.manual.chapters.ch07_endgame import EndgameChapter
from chessie.ui.dialogs.manual.fen_renderer import (
    _parse_placement,
    _parse_square,
    render_fen_board,
)


def _extract_first_fen(html: str) -> str:
    m = re.search(r'src="fen:([^"]+)"', html)
    assert m is not None
    return m.group(1).split("|", 1)[0]


def _extract_first_fen_raw(html: str) -> str:
    m = re.search(r'src="fen:([^"]+)"', html)
    assert m is not None
    return m.group(1)


def _extract_fen_raw_list(html: str) -> list[str]:
    return re.findall(r'src="fen:([^"]+)"', html)


def test_endgame_mate_examples_are_actual_checkmates() -> None:
    chapter = EndgameChapter().build("English")

    kq_page = next(page for page in chapter.pages if page.anchor == "kq_vs_k")
    kr_page = next(page for page in chapter.pages if page.anchor == "kr_vs_k")

    kq_fen = _extract_first_fen(kq_page.html)
    kr_fen = _extract_first_fen(kr_page.html)

    assert Rules.is_checkmate(position_from_fen(f"{kq_fen} b - - 0 1"))
    assert Rules.is_checkmate(position_from_fen(f"{kr_fen} b - - 0 1"))


def test_pieces_king_diagram_highlights_match_king_moves() -> None:
    expected = {"c6", "d6", "e6", "c5", "e5", "c4", "d4", "e4"}

    for lang in ("English", "Russian"):
        chapter = PiecesChapter().build(lang)
        page = next(page for page in chapter.pages if page.anchor == "king")
        raw = _extract_first_fen_raw(page.html)
        _fen, highlights = raw.split("|", 1)
        assert set(highlights.split(",")) == expected


def test_pieces_sliding_piece_diagrams_have_move_highlights() -> None:
    queen_expected = {
        "a5",
        "b5",
        "c5",
        "e5",
        "f5",
        "g5",
        "h5",
        "d1",
        "d2",
        "d3",
        "d4",
        "d6",
        "d7",
        "d8",
        "c6",
        "b7",
        "a8",
        "e6",
        "f7",
        "g8",
        "c4",
        "b3",
        "a2",
        "e4",
        "f3",
        "g2",
        "h1",
    }
    rook_expected = {
        "a5",
        "b5",
        "c5",
        "e5",
        "f5",
        "g5",
        "h5",
        "d1",
        "d2",
        "d3",
        "d4",
        "d6",
        "d7",
        "d8",
    }
    bishop_expected = {
        "c6",
        "b7",
        "a8",
        "e6",
        "f7",
        "g8",
        "c4",
        "b3",
        "a2",
        "e4",
        "f3",
        "g2",
        "h1",
    }

    for lang in ("English", "Russian"):
        chapter = PiecesChapter().build(lang)
        by_anchor = {page.anchor: page for page in chapter.pages}

        _, queen_hl = _extract_first_fen_raw(by_anchor["queen"].html).split("|", 1)
        _, rook_hl = _extract_first_fen_raw(by_anchor["rook"].html).split("|", 1)
        _, bishop_hl = _extract_first_fen_raw(by_anchor["bishop"].html).split("|", 1)

        assert set(queen_hl.split(",")) == queen_expected
        assert set(rook_hl.split(",")) == rook_expected
        assert set(bishop_hl.split(",")) == bishop_expected


def test_render_fen_board_is_resilient_to_invalid_input(qapp: object) -> None:
    _ = qapp  # Ensure QApplication exists before creating QPixmap resources.
    pixmap = render_fen_board(
        "invalid-fen",
        highlights=("a1", "z9", "x0", "h8"),
    )
    assert pixmap.width() > 0
    assert pixmap.height() > 0


def test_manual_uses_qtextbrowser_compatible_diagram_markup() -> None:
    html = fen_diagram("8/8/8/8/8/8/8/8", "Caption", "e4")
    assert '<table class="board-wrap"' in html
    assert '<div class="board-diagram">' in html
    assert "<figure" not in html
    assert "<figcaption" not in html


def test_openings_principles_keeps_list_before_diagram() -> None:
    chapter = OpeningsChapter().build("English")
    page = next(page for page in chapter.pages if page.anchor == "principles")
    html = page.html
    assert html.find("</ol>") < html.find('<table class="board-wrap"')


def test_tactics_fork_diagrams_match_declared_targets() -> None:
    for lang in ("English", "Russian"):
        chapter = TacticsChapter().build(lang)
        forks_page = next(page for page in chapter.pages if page.anchor == "forks")
        fen_raw = _extract_fen_raw_list(forks_page.html)
        assert len(fen_raw) >= 2

        first_fen, first_hl = fen_raw[0].split("|", 1)
        second_fen, second_hl = fen_raw[1].split("|", 1)

        assert first_fen == "8/2r1k3/8/3N4/8/8/8/4K3"
        assert set(first_hl.split(",")) == {"d5", "e7", "c7"}

        assert second_fen == "8/8/8/8/2r1b3/3P4/8/3K4"
        assert set(second_hl.split(",")) == {"d3", "c4", "e4"}


def test_tactics_relative_pin_and_discovered_attack_are_consistent() -> None:
    for lang in ("English", "Russian"):
        chapter = TacticsChapter().build(lang)
        pins_page = next(page for page in chapter.pages if page.anchor == "pins")
        discovered_page = next(
            page for page in chapter.pages if page.anchor == "discovered"
        )

        pin_raw = _extract_fen_raw_list(pins_page.html)[1]
        discovered_raw = _extract_fen_raw_list(discovered_page.html)[0]

        pin_fen, pin_hl = pin_raw.split("|", 1)
        disc_fen, disc_hl = discovered_raw.split("|", 1)

        assert pin_fen == "3kq3/8/4b3/8/8/8/8/4R2K"
        assert set(pin_hl.split(",")) == {"e1", "e6", "e8"}

        assert disc_fen == "4k3/4p3/8/8/4N3/8/8/4R2K"
        assert set(disc_hl.split(",")) == {"e4", "e1", "e7"}


def test_openings_principles_shows_symmetric_center_control() -> None:
    """The Opening Principles diagram must show both sides fighting for the
    centre (1.e4 e5 2.Nf3 Nc6). The buggy version had 1.e4 Nf6 2.Nf3 Nc6
    where Black had no centre pawn, contradicting the lesson content."""
    for lang in ("English", "Russian"):
        chapter = OpeningsChapter().build(lang)
        page = next(page for page in chapter.pages if page.anchor == "principles")
        fen = _extract_first_fen(page.html)
        # Black must have a centre pawn (e5) and only ONE knight developed (Nc6),
        # not BOTH knights developed without any pawn:
        placement = fen.split()[0] if " " in fen else fen
        ranks = placement.split("/")
        # rank 5 (index 3 from top) must contain 'p' (Black's e5 pawn)
        assert "p" in ranks[3], (
            f"[{lang}] Opening Principles FEN has no Black centre pawn on rank 5: {fen!r}"
        )
        # rank 7 (index 1 from top) must contain an empty e7 square ('1' in 4th
        # field position), meaning the e-pawn has advanced
        assert ranks[1] != "pppppppp", (
            f"[{lang}] Opening Principles FEN shows all Black pawns on rank 7 "
            f"(no pawn has advanced): {fen!r}"
        )


def test_all_manual_diagrams_have_valid_fen_and_highlights() -> None:
    chapter_dir = (
        Path(__file__).resolve().parents[2] / "src/chessie/ui/dialogs/manual/chapters"
    )
    call_re = re.compile(r"fen_diagram\((.*?)\)", re.S)
    str_re = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')

    count = 0
    for chapter_file in sorted(chapter_dir.glob("ch*.py")):
        text = chapter_file.read_text(encoding="utf-8")
        for call in call_re.finditer(text):
            args = call.group(1)
            parts = [
                s.encode("utf-8").decode("unicode_escape") for s in str_re.findall(args)
            ]
            if not parts:
                continue
            count += 1

            fen = parts[0]
            _parse_placement(fen)

            if len(parts) < 3:
                continue
            highlights = [s.strip() for s in parts[2].split(",") if s.strip()]
            for sq in highlights:
                _parse_square(sq)

    assert count > 0
