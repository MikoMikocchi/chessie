"""Concrete player implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from chessie.core.enums import Color
from chessie.game.interfaces import IPlayer

if TYPE_CHECKING:
    from chessie.core.position import Position


class HumanPlayer(IPlayer):
    """A human participant — moves come from the UI.

    ``request_move`` is a no-op because humans select moves interactively.
    """

    __slots__ = ("_color", "_name")

    def __init__(self, color: Color, name: str = "") -> None:
        self._color = color
        self._name = name or f"Player ({color})"

    @property
    def color(self) -> Color:
        return self._color

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_human(self) -> bool:
        return True

    def request_move(self, position: Position) -> None:
        pass  # Human moves arrive via controller.submit_move()

    def cancel(self) -> None:
        pass


class AIPlayer(IPlayer):
    """An AI participant that delegates computation to a callback.

    The actual engine search is decoupled — ``AIPlayer`` only stores
    a reference to a *bridge* callable that will be invoked on
    ``request_move``.  In production this callable will dispatch work
    to an ``EngineWorker`` running in a ``QThread``.

    Args:
        color: Side the AI plays.
        name: Display name.
        on_request_move: ``(Position) -> None`` — called when the game
            controller asks the AI to start thinking.
        on_cancel: ``() -> None`` — called to abort a running search.
    """

    __slots__ = ("_color", "_name", "_on_request_move", "_on_cancel")

    def __init__(
        self,
        color: Color,
        name: str = "Engine",
        on_request_move: Callable[[Position], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self._color = color
        self._name = name
        self._on_request_move = on_request_move
        self._on_cancel = on_cancel

    @property
    def color(self) -> Color:
        return self._color

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_human(self) -> bool:
        return False

    def request_move(self, position: Position) -> None:
        if self._on_request_move is not None:
            self._on_request_move(position)

    def cancel(self) -> None:
        if self._on_cancel is not None:
            self._on_cancel()
