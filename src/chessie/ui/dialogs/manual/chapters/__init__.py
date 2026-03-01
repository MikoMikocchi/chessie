"""Chapter registry — collects all built-in chapter providers.

To add a new chapter:
1. Create a module with a ``ChapterProvider`` subclass.
2. Import it here and append an instance to ``ALL_CHAPTERS``.
"""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters.ch01_introduction import IntroductionChapter
from chessie.ui.dialogs.manual.chapters.ch02_pieces import PiecesChapter
from chessie.ui.dialogs.manual.chapters.ch03_special_moves import SpecialMovesChapter
from chessie.ui.dialogs.manual.chapters.ch04_notation import NotationChapter
from chessie.ui.dialogs.manual.chapters.ch05_tactics import TacticsChapter
from chessie.ui.dialogs.manual.chapters.ch06_openings import OpeningsChapter
from chessie.ui.dialogs.manual.chapters.ch07_endgame import EndgameChapter
from chessie.ui.dialogs.manual.models import ChapterProvider

ALL_CHAPTERS: list[ChapterProvider] = sorted(
    [
        IntroductionChapter(),
        PiecesChapter(),
        SpecialMovesChapter(),
        NotationChapter(),
        TacticsChapter(),
        OpeningsChapter(),
        EndgameChapter(),
    ],
    key=lambda ch: ch.order,
)

__all__ = ["ALL_CHAPTERS"]
