"""Chess engine package: search implementation and Qt worker bridge."""

from chessie.engine._default import DefaultEngine
from chessie.engine.cpp_search import CppSearchEngine, is_available
from chessie.engine.python_search import PythonSearchEngine
from chessie.engine.qt_bridge import EngineWorker
from chessie.engine.search import IEngine, SearchLimits, SearchResult

__all__ = [
    "CppSearchEngine",
    "DefaultEngine",
    "EngineWorker",
    "IEngine",
    "PythonSearchEngine",
    "SearchLimits",
    "SearchResult",
    "is_available",
]
