"""Regression tests for AnalysisSession wiring."""

from __future__ import annotations

import weakref

from chessie.ui.analysis_session import AnalysisSession


def test_setup_connects_slots_without_weakref_error(qapp: object) -> None:
    del qapp
    session = AnalysisSession(
        on_progress=lambda _done, _total: None,
        on_finished=lambda _report: None,
        on_failed=lambda _message: None,
        on_cancelled=lambda: None,
    )
    assert weakref.ref(session)() is session

    session.setup()
    session.shutdown()
