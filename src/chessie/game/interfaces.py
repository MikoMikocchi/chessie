"""Abstract interfaces for the game layer.

Follows Dependency Inversion: high-level GameController depends on
these ABCs, not on concrete Player/Clock implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum, auto
from typing import TYPE_CHECKING

from chessie.core.enums import Color

if TYPE_CHECKING:
    from chessie.core.move import Move
    from chessie.core.position import Position


# ── Game phase FSM states ────────────────────────────────────────────────────


class GamePhase(IntEnum):
    """Finite-state-machine states for a chess game."""

    NOT_STARTED = auto()
    AWAITING_MOVE = auto()
    THINKING = auto()  # AI is computing
    GAME_OVER = auto()


class DrawOffer(IntEnum):
    """Draw offer status between players."""

    NONE = 0
    OFFERED = auto()
    ACCEPTED = auto()
    DECLINED = auto()


# ── Time control presets ─────────────────────────────────────────────────────


class TimeControl:
    """Immutable time-control definition.

    Args:
        initial_seconds: Starting time per player.
        increment_seconds: Per-move increment (Fischer).
    """

    __slots__ = ("initial_seconds", "increment_seconds")

    def __init__(self, initial_seconds: float, increment_seconds: float = 0.0) -> None:
        self.initial_seconds = initial_seconds
        self.increment_seconds = increment_seconds

    # Common presets
    @classmethod
    def bullet_1m(cls) -> TimeControl:
        return cls(60, 0)

    @classmethod
    def bullet_2m1s(cls) -> TimeControl:
        return cls(120, 1)

    @classmethod
    def blitz_3m(cls) -> TimeControl:
        return cls(180, 0)

    @classmethod
    def blitz_3m2s(cls) -> TimeControl:
        return cls(180, 2)

    @classmethod
    def blitz_5m(cls) -> TimeControl:
        return cls(300, 0)

    @classmethod
    def blitz_5m3s(cls) -> TimeControl:
        return cls(300, 3)

    @classmethod
    def rapid_10m(cls) -> TimeControl:
        return cls(600, 0)

    @classmethod
    def rapid_15m10s(cls) -> TimeControl:
        return cls(900, 10)

    @classmethod
    def classical_30m(cls) -> TimeControl:
        return cls(1800, 0)

    @classmethod
    def unlimited(cls) -> TimeControl:
        """No time limit."""
        return cls(float("inf"), 0)

    def __repr__(self) -> str:
        mins = self.initial_seconds / 60
        if self.increment_seconds:
            return f"TimeControl({mins:.0f}m+{self.increment_seconds:.0f}s)"
        return f"TimeControl({mins:.0f}m)"


# ── Abstract interfaces ─────────────────────────────────────────────────────


class IPlayer(ABC):
    """Interface for a game participant (human or AI)."""

    @property
    @abstractmethod
    def color(self) -> Color: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def is_human(self) -> bool: ...

    @abstractmethod
    def request_move(self, position: Position) -> None:
        """Begin the move-selection process.

        For humans this is a no-op (they interact via UI).
        For AI this kicks off background search.
        """

    @abstractmethod
    def cancel(self) -> None:
        """Cancel an ongoing move computation (AI only, no-op for human)."""


class IClock(ABC):
    """Interface for a chess clock."""

    @abstractmethod
    def start(self, color: Color) -> None:
        """Start the clock for *color*."""

    @abstractmethod
    def stop(self) -> None:
        """Pause the running clock."""

    @abstractmethod
    def switch(self) -> None:
        """Switch to the other player's clock."""

    @abstractmethod
    def remaining(self, color: Color) -> float:
        """Seconds remaining for *color*."""

    @abstractmethod
    def is_flag_fallen(self, color: Color) -> bool:
        """Has *color* run out of time?"""

    @abstractmethod
    def add_increment(self, color: Color) -> None:
        """Add Fischer increment after a move."""


class IGameController(ABC):
    """Interface for the game orchestrator."""

    @abstractmethod
    def new_game(
        self,
        white: IPlayer,
        black: IPlayer,
        time_control: TimeControl | None = None,
        fen: str | None = None,
    ) -> None:
        """Set up a new game."""

    @abstractmethod
    def submit_move(self, move: Move) -> bool:
        """Submit a move. Returns True if legal and applied."""

    @abstractmethod
    def resign(self, color: Color) -> None:
        """Player of *color* resigns."""

    @abstractmethod
    def offer_draw(self, color: Color) -> None:
        """Player offers a draw."""

    @abstractmethod
    def accept_draw(self, color: Color) -> None:
        """Opponent accepts the draw offer."""

    @abstractmethod
    def undo_move(self) -> bool:
        """Undo the last move. Returns True on success."""
