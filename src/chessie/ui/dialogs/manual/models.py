"""Data models for the in-game chess manual.

This module defines the core abstractions:
- ``Page``           – a single rendered page of content
- ``Chapter``        – a titled, ordered sequence of pages
- ``ChapterProvider`` – abstract interface for pluggable chapter content
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Page:
    """A single page of manual content.

    Parameters
    ----------
    html:
        Complete HTML string (including ``<style>``).
    anchor:
        Optional anchor id.  Allows other pages to link here via
        ``manual:<chapter_id>#<anchor>``.
    """

    html: str
    anchor: str = ""


@dataclass(frozen=True)
class Chapter:
    """An ordered collection of pages forming a chapter."""

    chapter_id: str
    title: str
    pages: tuple[Page, ...] = field(default_factory=tuple)

    # ── helpers ──────────────────────────────────────────────────────
    def page_for_anchor(self, anchor: str) -> int | None:
        """Return the page index whose anchor matches, or *None*."""
        for idx, page in enumerate(self.pages):
            if page.anchor == anchor:
                return idx
        return None


class ChapterProvider(ABC):
    """Interface for pluggable chapter providers.

    To add a new chapter to the manual:
    1. Create a class implementing ``ChapterProvider``.
    2. Register an instance in ``chapters/__init__.py``.
    """

    @property
    @abstractmethod
    def chapter_id(self) -> str:
        """Unique string identifier (e.g. ``'ch01_intro'``)."""

    @property
    @abstractmethod
    def order(self) -> int:
        """Sort key – lower values appear first in the sidebar."""

    @abstractmethod
    def build(self, lang: str) -> Chapter:
        """Build the chapter for the given language (``'English'`` / ``'Russian'``)."""
