"""Evaluation helpers for :class:`PythonSearchEngine`."""

from __future__ import annotations

from chessie.core.enums import Color, PieceType
from chessie.core.position import Position
from chessie.core.types import Square, file_of, rank_of

PIECE_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 0,
}


def _piece_square_bonus_formula(
    piece_type: PieceType,
    color: Color,
    sq: Square,
) -> int:
    file_idx = file_of(sq)
    rank_idx = rank_of(sq)
    if color == Color.BLACK:
        rank_idx = 7 - rank_idx

    center_dist = abs(file_idx - 3) + abs(rank_idx - 3)

    if piece_type == PieceType.PAWN:
        return rank_idx * 12 - abs(file_idx - 3) * 2
    if piece_type == PieceType.KNIGHT:
        return 28 - center_dist * 8
    if piece_type == PieceType.BISHOP:
        return 22 - center_dist * 5 + rank_idx * 2
    if piece_type == PieceType.ROOK:
        return 10 + rank_idx * 3 - abs(file_idx - 3)
    if piece_type == PieceType.QUEEN:
        return 6 - center_dist * 2

    if rank_idx <= 1:
        return 18 - abs(file_idx - 4) * 2
    return -rank_idx * 8


def _build_piece_square_tables() -> list[list[list[int]]]:
    tables = [[[0 for _ in range(64)] for _ in range(2)] for _ in range(7)]
    for piece_type in PieceType:
        pt_idx = int(piece_type)
        for color in Color:
            color_idx = int(color)
            for sq in range(64):
                tables[pt_idx][color_idx][sq] = _piece_square_bonus_formula(
                    piece_type,
                    color,
                    sq,
                )
    return tables


PIECE_SQUARE_TABLES = _build_piece_square_tables()


def static_eval(position: Position) -> int:
    """Evaluate position from side-to-move perspective."""
    board = position.board
    pst = PIECE_SQUARE_TABLES
    white_idx = int(Color.WHITE)
    black_idx = int(Color.BLACK)

    white_score = 0
    black_score = 0

    for piece_type, material in PIECE_VALUES.items():
        pt_idx = int(piece_type)
        white_table = pst[pt_idx][white_idx]
        black_table = pst[pt_idx][black_idx]

        white_bb = board.pieces_bitboard(Color.WHITE, piece_type)
        while white_bb:
            lsb = white_bb & -white_bb
            sq = lsb.bit_length() - 1
            white_score += material + white_table[sq]
            white_bb ^= lsb

        black_bb = board.pieces_bitboard(Color.BLACK, piece_type)
        while black_bb:
            lsb = black_bb & -black_bb
            sq = lsb.bit_length() - 1
            black_score += material + black_table[sq]
            black_bb ^= lsb

    score = white_score - black_score
    if position.side_to_move == Color.WHITE:
        return score
    return -score


def piece_square_delta(
    piece_type: PieceType,
    color: Color,
    from_sq: Square,
    to_sq: Square,
) -> int:
    table = PIECE_SQUARE_TABLES[int(piece_type)][int(color)]
    return table[to_sq] - table[from_sq]


def piece_square_bonus(
    piece_type: PieceType,
    color: Color,
    sq: Square,
) -> int:
    return PIECE_SQUARE_TABLES[int(piece_type)][int(color)][sq]
