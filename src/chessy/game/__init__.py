"""Game management layer — controller, players, clock, state machine.

Quick start::

    from chessy.game import GameController, HumanPlayer, TimeControl

    ctrl = GameController()
    ctrl.new_game(
        white=HumanPlayer(Color.WHITE, "Alice"),
        black=HumanPlayer(Color.BLACK, "Bob"),
        time_control=TimeControl.blitz_5m(),
    )
"""

from chessy.game.clock import Clock
from chessy.game.controller import GameController, GameEvents
from chessy.game.interfaces import (
    DrawOffer,
    GamePhase,
    IClock,
    IGameController,
    IPlayer,
    TimeControl,
)
from chessy.game.player import AIPlayer, HumanPlayer
from chessy.game.state import GameState, MoveRecord

__all__ = [
    # Interfaces
    "DrawOffer",
    "GamePhase",
    "IClock",
    "IGameController",
    "IPlayer",
    "TimeControl",
    # Concrete
    "AIPlayer",
    "Clock",
    "GameController",
    "GameEvents",
    "GameState",
    "HumanPlayer",
    "MoveRecord",
]
