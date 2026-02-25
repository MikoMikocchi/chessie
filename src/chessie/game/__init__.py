"""Game management layer — controller, players, clock, state machine.

Quick start::

    from chessie.game import GameController, HumanPlayer, TimeControl

    ctrl = GameController()
    ctrl.new_game(
        white=HumanPlayer(Color.WHITE, "Alice"),
        black=HumanPlayer(Color.BLACK, "Bob"),
        time_control=TimeControl.blitz_5m(),
    )
"""

from chessie.game.clock import Clock
from chessie.game.controller import GameController, GameEvents
from chessie.game.interfaces import (
    DrawOffer,
    GamePhase,
    IClock,
    IGameController,
    IPlayer,
    TimeControl,
)
from chessie.game.player import AIPlayer, HumanPlayer
from chessie.game.state import GameState, MoveRecord

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
