"""Core domain layer — pure chess logic with zero external dependencies.

Quick start::

    from chessie.core import Position, MoveGenerator, position_from_fen, STARTING_FEN

    pos = position_from_fen(STARTING_FEN)
    gen = MoveGenerator(pos)
    for move in gen.generate_legal_moves():
        print(move)
"""

from chessie.core.board import Board
from chessie.core.enums import CastlingRights, Color, GameResult, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.notation import (
    STARTING_FEN,
    move_to_san,
    parse_san,
    position_from_fen,
    position_to_fen,
)
from chessie.core.piece import Piece
from chessie.core.position import Position
from chessie.core.rules import Rules
from chessie.core.types import (
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
