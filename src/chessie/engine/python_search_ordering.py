"""Move ordering helpers for :class:`PythonSearchEngine`."""

from __future__ import annotations

from collections.abc import Callable

from chessie.core.enums import Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.position import Position

KILLER_PRIMARY_BONUS = 9_000
KILLER_SECONDARY_BONUS = 8_000
HISTORY_BONUS_FACTOR = 32
HISTORY_MAX_SCORE = 8_000
MAX_KILLER_PLY = 128


def new_killer_moves() -> list[list[Move | None]]:
    return [[None, None] for _ in range(MAX_KILLER_PLY)]


def new_history_scores() -> list[list[list[int]]]:
    return [[[0 for _ in range(64)] for _ in range(64)] for _ in range(2)]


def reset_heuristics() -> tuple[list[list[Move | None]], list[list[list[int]]]]:
    return new_killer_moves(), new_history_scores()


def record_killer(killer_moves: list[list[Move | None]], move: Move, ply: int) -> None:
    if ply < 0 or ply >= len(killer_moves):
        return
    killers = killer_moves[ply]
    if killers[0] == move:
        return
    killers[1] = killers[0]
    killers[0] = move


def killer_score(killer_moves: list[list[Move | None]], move: Move, ply: int) -> int:
    if ply < 0 or ply >= len(killer_moves):
        return 0
    killers = killer_moves[ply]
    if killers[0] == move:
        return KILLER_PRIMARY_BONUS
    if killers[1] == move:
        return KILLER_SECONDARY_BONUS
    return 0


def history_score(
    history_scores: list[list[list[int]]],
    side: Color,
    move: Move,
) -> int:
    return history_scores[int(side)][move.from_sq][move.to_sq]


def update_history(
    history_scores: list[list[list[int]]],
    side: Color,
    move: Move,
    depth: int,
) -> None:
    bonus = max(depth, 1) * max(depth, 1) * HISTORY_BONUS_FACTOR
    side_scores = history_scores[int(side)]
    current = side_scores[move.from_sq][move.to_sq]
    side_scores[move.from_sq][move.to_sq] = min(HISTORY_MAX_SCORE, current + bonus)


def move_order_score(
    *,
    position: Position,
    move: Move,
    tt_move: Move | None,
    ply: int,
    killer_moves: list[list[Move | None]],
    history_scores: list[list[list[int]]],
    piece_values: dict[PieceType, int],
    is_quiet_move: Callable[[Position, Move], bool],
    piece_square_delta: Callable[[PieceType, Color, int, int], int],
    inf_score: int,
) -> int:
    moving_piece = position.board[move.from_sq]
    if moving_piece is None:
        return -inf_score

    is_quiet = is_quiet_move(position, move)
    score = 0
    if tt_move is not None and move == tt_move:
        score += 100_000

    if move.flag == MoveFlag.PROMOTION and move.promotion is not None:
        score += 20_000 + piece_values[move.promotion]

    target_piece = position.board[move.to_sq]
    if target_piece is not None:
        score += 10_000
        score += 10 * piece_values[target_piece.piece_type]
        score -= piece_values[moving_piece.piece_type]
    elif move.flag == MoveFlag.EN_PASSANT:
        score += 10_000
        score += 10 * piece_values[PieceType.PAWN]
        score -= piece_values[moving_piece.piece_type]
    elif is_quiet:
        score += killer_score(killer_moves, move, ply)
        score += history_score(history_scores, position.side_to_move, move)

    if move.flag in (MoveFlag.CASTLE_KINGSIDE, MoveFlag.CASTLE_QUEENSIDE):
        score += 120

    score += piece_square_delta(
        moving_piece.piece_type,
        moving_piece.color,
        move.from_sq,
        move.to_sq,
    )
    return score
