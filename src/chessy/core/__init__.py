"""Core domain layer — pure chess logic with zero external dependencies.

Quick start::

    from chessy.core import Position, MoveGenerator, position_from_fen, STARTING_FEN

    pos = position_from_fen(STARTING_FEN)
    gen = MoveGenerator(pos)
    for move in gen.generate_legal_moves():
        print(move)
"""

from chessy.core.board import Board
from chessy.core.enums import CastlingRights, Color, GameResult, MoveFlag, PieceType
from chessy.core.move import Move
from chessy.core.move_generator import MoveGenerator
from chessy.core.notation import (
    STARTING_FEN,
    move_to_san,
    parse_san,
    position_from_fen,
    position_to_fen,
)
from chessy.core.piece import Piece
from chessy.core.position import Position
from chessy.core.rules import Rules
from chessy.core.types import (
    Square,
    file_of,
    make_square,
    parse_square,
    rank_of,
    square_name,
)

__all__ = [
    # Enums / flags
    "CastlingRights",
    "Color",
    "GameResult",
    "MoveFlag",
    "PieceType",
    # Types / helpers
    "Square",
    "file_of",
    "make_square",
    "parse_square",
    "rank_of",
    "square_name",
    # Domain objects
    "Board",
    "Move",
    "MoveGenerator",
    "Piece",
    "Position",
    "Rules",
    # Notation
    "STARTING_FEN",
    "move_to_san",
    "parse_san",
    "position_from_fen",
    "position_to_fen",
]
