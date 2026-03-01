"""Chess engine package: search implementation and Qt worker bridge."""

from chessie.engine.cpp_search import CppSearchEngine, is_available
from chessie.engine.python_search import PythonSearchEngine
from chessie.engine.qt_bridge import EngineWorker
from chessie.engine.search import IEngine, SearchLimits, SearchResult

# Use the native C++ engine when available, fall back to pure Python.
DefaultEngine: type[IEngine] = CppSearchEngine if is_available() else PythonSearchEngine

__all__ = [
    "CppSearchEngine",
    "DefaultEngine",
    "EngineWorker",
    "IEngine",
    "PythonSearchEngine",
    "SearchLimits",
    "SearchResult",
]
