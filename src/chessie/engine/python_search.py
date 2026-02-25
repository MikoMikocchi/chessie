"""Pure-Python chess engine search (negamax + alpha-beta)."""

from __future__ import annotations

from time import perf_counter

from chessie.core.enums import Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.position import Position
from chessie.core.rules import Rules
from chessie.core.types import Square, file_of, rank_of
from chessie.engine.search import CancelCheck, IEngine, SearchLimits, SearchResult

_INF_SCORE = 1_000_000
_MATE_SCORE = 100_000

_PIECE_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 0,
}


def _never_cancelled() -> bool:
    return False


class PythonSearchEngine(IEngine):
    """Classical chess searcher with iterative deepening and quiescence."""

    __slots__ = ("_cancel_check", "_deadline", "_nodes")

    def __init__(self) -> None:
        self._nodes = 0
        self._deadline: float | None = None
        self._cancel_check: CancelCheck = _never_cancelled

    def search(
        self,
        position: Position,
        limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
    ) -> SearchResult:
        if limits.max_depth <= 0:
            raise ValueError("Search depth must be >= 1")

        self._nodes = 0
        self._cancel_check = is_cancelled or _never_cancelled
        self._deadline = None
        if limits.time_limit_ms is not None:
            ms = max(limits.time_limit_ms, 1)
            self._deadline = perf_counter() + (ms / 1000.0)

        root_gen = MoveGenerator(position)
        root_moves = root_gen.generate_legal_moves()
        if not root_moves:
            if root_gen.is_in_check(position.side_to_move):
                return SearchResult(None, -_MATE_SCORE, 0, self._nodes)
            return SearchResult(None, 0, 0, self._nodes)

        ordered_root = self._order_moves(position, root_moves)
        best_move = ordered_root[0]
        best_score = self._static_eval(position)
        completed_depth = 0

        for depth in range(1, limits.max_depth + 1):
            if self._should_stop():
                break

            score, move = self._search_root(position, ordered_root, depth)
            if self._should_stop():
                break
            if move is None:
                break

            best_move = move
            best_score = score
            completed_depth = depth

            # Principal variation move first in the next iteration.
            ordered_root = [move] + [m for m in ordered_root if m != move]

        return SearchResult(best_move, best_score, completed_depth, self._nodes)

    def _search_root(
        self,
        position: Position,
        root_moves: list[Move],
        depth: int,
    ) -> tuple[int, Move | None]:
        best_score = -_INF_SCORE
        best_move: Move | None = None
        alpha = -_INF_SCORE
        beta = _INF_SCORE

        for move in root_moves:
            if self._should_stop():
                break

            position.make_move(move)
            score = -self._negamax(
                position,
                depth - 1,
                -beta,
                -alpha,
                ply=1,
            )
            position.unmake_move(move)

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score

        return best_score, best_move

    def _negamax(
        self,
        position: Position,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> int:
        if self._should_stop():
            return self._static_eval(position)

        self._nodes += 1

        if self._is_draw(position):
            return 0

        if depth <= 0:
            return self._quiescence(position, alpha, beta, ply)

        gen = MoveGenerator(position)
        legal = gen.generate_legal_moves()
        if not legal:
            if gen.is_in_check(position.side_to_move):
                return -_MATE_SCORE + ply
            return 0

        ordered = self._order_moves(position, legal)
        best_score = -_INF_SCORE

        for move in ordered:
            position.make_move(move)
            score = -self._negamax(position, depth - 1, -beta, -alpha, ply + 1)
            position.unmake_move(move)

            if score > best_score:
                best_score = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
            if self._should_stop():
                break

        if best_score == -_INF_SCORE:
            return self._static_eval(position)
        return best_score

    def _quiescence(
        self,
        position: Position,
        alpha: int,
        beta: int,
        ply: int,
    ) -> int:
        if self._should_stop():
            return self._static_eval(position)

        self._nodes += 1

        if self._is_draw(position):
            return 0

        gen = MoveGenerator(position)
        in_check = gen.is_in_check(position.side_to_move)
        legal = gen.generate_legal_moves()

        if not legal:
            if in_check:
                return -_MATE_SCORE + ply
            return 0

        if not in_check:
            stand_pat = self._static_eval(position)
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat
            candidates = [m for m in legal if self._is_noisy_move(position, m)]
        else:
            candidates = legal

        if not candidates:
            return alpha

        for move in self._order_moves(position, candidates):
            position.make_move(move)
            score = -self._quiescence(position, -beta, -alpha, ply + 1)
            position.unmake_move(move)

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
            if self._should_stop():
                break

        return alpha

    def _is_draw(self, position: Position) -> bool:
        return Rules.is_fifty_move_rule(position) or Rules.is_insufficient_material(
            position
        )

    def _should_stop(self) -> bool:
        if self._cancel_check():
            return True
        return self._deadline is not None and perf_counter() >= self._deadline

    def _order_moves(self, position: Position, moves: list[Move]) -> list[Move]:
        return sorted(
            moves,
            key=lambda move: self._move_order_score(position, move),
            reverse=True,
        )

    def _move_order_score(self, position: Position, move: Move) -> int:
        moving_piece = position.board[move.from_sq]
        if moving_piece is None:
            return -_INF_SCORE

        score = 0
        if move.flag == MoveFlag.PROMOTION and move.promotion is not None:
            score += 20_000 + _PIECE_VALUES[move.promotion]

        target_piece = position.board[move.to_sq]
        if target_piece is not None:
            score += 10_000
            score += 10 * _PIECE_VALUES[target_piece.piece_type]
            score -= _PIECE_VALUES[moving_piece.piece_type]
        elif move.flag == MoveFlag.EN_PASSANT:
            score += 10_000
            score += 10 * _PIECE_VALUES[PieceType.PAWN]
            score -= _PIECE_VALUES[moving_piece.piece_type]
        elif move.flag in (MoveFlag.CASTLE_KINGSIDE, MoveFlag.CASTLE_QUEENSIDE):
            score += 120

        score += self._piece_square_delta(
            moving_piece.piece_type,
            moving_piece.color,
            move.from_sq,
            move.to_sq,
        )
        return score

    def _is_noisy_move(self, position: Position, move: Move) -> bool:
        if move.flag in (MoveFlag.EN_PASSANT, MoveFlag.PROMOTION):
            return True
        return position.board[move.to_sq] is not None

    def _static_eval(self, position: Position) -> int:
        white_score = 0
        black_score = 0

        for sq in range(64):
            piece = position.board[sq]
            if piece is None:
                continue

            val = _PIECE_VALUES[piece.piece_type]
            val += self._piece_square_bonus(piece.piece_type, piece.color, sq)
            if piece.color == Color.WHITE:
                white_score += val
            else:
                black_score += val

        score = white_score - black_score
        if position.side_to_move == Color.WHITE:
            return score
        return -score

    def _piece_square_delta(
        self,
        piece_type: PieceType,
        color: Color,
        from_sq: Square,
        to_sq: Square,
    ) -> int:
        return self._piece_square_bonus(piece_type, color, to_sq) - (
            self._piece_square_bonus(piece_type, color, from_sq)
        )

    def _piece_square_bonus(
        self,
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

        # King: favor safety in opening/middlegame.
        if rank_idx <= 1:
            return 18 - abs(file_idx - 4) * 2
        return -rank_idx * 8
