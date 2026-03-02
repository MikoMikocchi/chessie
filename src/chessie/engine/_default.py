"""Resolves the default engine class without causing circular imports.

Both ``chessie.engine.__init__`` and ``chessie.engine.qt_bridge`` import from
here instead of from each other, breaking the import cycle.
"""

from __future__ import annotations

from chessie.engine.cpp_search import CppSearchEngine
from chessie.engine.search import IEngine

DefaultEngine: type[IEngine] = CppSearchEngine

__all__ = ["DefaultEngine"]
