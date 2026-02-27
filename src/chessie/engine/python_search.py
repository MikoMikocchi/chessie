"""Pure-Python chess engine search (negamax + alpha-beta)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter, sleep

from chessie.core.enums import Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.position import Position
from chessie.core.rules import Rules
from chessie.core.types import Square, file_of, rank_of
from chessie.engine.search import CancelCheck, IEngine, SearchLimits, SearchResult

_INF_SCORE = 1_000_000
_MATE_SCORE = 100_000
_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_MAX_KILLER_PLY = 128
_KILLER_PRIMARY_BONUS = 9_000
_KILLER_SECONDARY_BONUS = 8_000
_HISTORY_BONUS_FACTOR = 32
_HISTORY_MAX_SCORE = 8_000
_NULL_MOVE_MIN_DEPTH = 3
_NULL_MOVE_REDUCTION = 2
_LMR_MIN_DEPTH = 4
_LMR_MIN_MOVE_INDEX = 3
_QUIESCENCE_MAX_DEPTH = 16

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


@dataclass(slots=True)
class _TTEntry:
    depth: int
    score: int
    bound: int
    best_move: Move | None


@dataclass(slots=True)
class _NullMoveState:
    side_to_move: Color
    en_passant: Square | None
    halfmove_clock: int
    fullmove_number: int


class PythonSearchEngine(IEngine):
    """Classical chess searcher with iterative deepening and quiescence."""

    __slots__ = (
        "_cancel_check",
        "_deadline",
        "_nodes",
        "_last_yield_nodes",
        "_tt",
        "_tt_max_entries",
        "_killer_moves",
        "_history_scores",
    )

    def __init__(self) -> None:
        self._nodes = 0
        self._last_yield_nodes = 0
        self._deadline: float | None = None
        self._cancel_check: CancelCheck = _never_cancelled
        self._tt: dict[int, _TTEntry] = {}
        self._tt_max_entries = 200_000
        self._killer_moves: list[list[Move | None]] = [
            [None, None] for _ in range(_MAX_KILLER_PLY)
        ]
        self._history_scores: list[list[list[int]]] = [
            [[0 for _ in range(64)] for _ in range(64)] for _ in range(2)
        ]

    def search(
        self,
        position: Position,
        limits: SearchLimits,
        is_cancelled: CancelCheck | None = None,
    ) -> SearchResult:
        if limits.max_depth <= 0:
            raise ValueError("Search depth must be >= 1")

        self._nodes = 0
        self._last_yield_nodes = 0
        self._tt.clear()
        self._reset_move_order_heuristics()
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

        ordered_root = self._order_moves(position, root_moves, ply=0)
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
        allow_null: bool = True,
    ) -> int:
        if self._should_stop():
            return self._static_eval(position)

        self._nodes += 1
        alpha_orig = alpha
        beta_orig = beta
        tt_key = position._key_stack[-1]
        tt_entry = self._tt.get(tt_key)
        tt_move = tt_entry.best_move if tt_entry is not None else None

        if tt_entry is not None and tt_entry.depth >= depth:
            if tt_entry.bound == _TT_EXACT:
                return tt_entry.score
            if tt_entry.bound == _TT_LOWER:
                alpha = max(alpha, tt_entry.score)
            else:
                beta = min(beta, tt_entry.score)
            if alpha >= beta:
                return tt_entry.score

        if self._is_draw(position):
            return 0

        if depth <= 0:
            return self._quiescence(position, alpha, beta, ply)

        gen = MoveGenerator(position)
        in_check = gen.is_in_check(position.side_to_move)

        if self._can_apply_null_move(position, depth, in_check, allow_null):
            null_state = self._make_null_move(position)
            try:
                reduction = _NULL_MOVE_REDUCTION + (depth // 4)
                null_depth = max(0, depth - 1 - reduction)
                null_score = -self._negamax(
                    position,
                    null_depth,
                    -beta,
                    -beta + 1,
                    ply + 1,
                    allow_null=False,
                )
            finally:
                self._unmake_null_move(position, null_state)

            if self._should_stop():
                return self._static_eval(position)
            if null_score >= beta:
                return beta

        legal = gen.generate_legal_moves()
        if not legal:
            if in_check:
                return -_MATE_SCORE + ply
            return 0

        ordered = self._order_moves(position, legal, tt_move=tt_move, ply=ply)
        best_score = -_INF_SCORE
        best_move: Move | None = None
        side_to_move = position.side_to_move

        for move_index, move in enumerate(ordered):
            is_quiet = self._is_quiet_move(position, move)
            can_try_lmr = self._can_try_lmr(
                depth=depth,
                move_index=move_index,
                in_check=in_check,
                is_quiet=is_quiet,
                move=move,
                tt_move=tt_move,
            )

            position.make_move(move)
            if can_try_lmr and not MoveGenerator(position).is_in_check(
                position.side_to_move
            ):
                reduction = self._lmr_reduction(depth, move_index)
                reduced_depth = max(0, depth - 1 - reduction)
                score = -self._negamax(
                    position,
                    reduced_depth,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )
                if score > alpha:
                    score = -self._negamax(position, depth - 1, -beta, -alpha, ply + 1)
            else:
                score = -self._negamax(position, depth - 1, -beta, -alpha, ply + 1)
            position.unmake_move(move)

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score
            if alpha >= beta:
                if is_quiet:
                    self._record_killer(move, ply)
                    self._update_history(side_to_move, move, depth)
                break
            if self._should_stop():
                break

        if best_score == -_INF_SCORE:
            return self._static_eval(position)

        bound = _TT_EXACT
        if best_score <= alpha_orig:
            bound = _TT_UPPER
        elif best_score >= beta_orig:
            bound = _TT_LOWER
        self._store_tt(tt_key, depth, best_score, bound, best_move=best_move)
        return best_score

    def _quiescence(
        self,
        position: Position,
        alpha: int,
        beta: int,
        ply: int,
        q_depth: int = 0,
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

        # Hard cap to avoid unbounded recursive capture/check sequences.
        if q_depth >= _QUIESCENCE_MAX_DEPTH:
            if in_check:
                return self._static_eval(position)
            stand_pat = self._static_eval(position)
            if stand_pat >= beta:
                return beta
            return max(alpha, stand_pat)

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

        for move in self._order_moves(position, candidates, ply=ply):
            position.make_move(move)
            score = -self._quiescence(position, -beta, -alpha, ply + 1, q_depth + 1)
            position.unmake_move(move)

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
            if self._should_stop():
                break

        return alpha

    def _is_draw(self, position: Position) -> bool:
        return Rules.is_automatic_draw(position)

    def _should_stop(self) -> bool:
        if self._nodes - self._last_yield_nodes >= 4096:
            self._last_yield_nodes = self._nodes
            sleep(0.001)
        if self._cancel_check():
            return True
        return self._deadline is not None and perf_counter() >= self._deadline

    def _order_moves(
        self,
        position: Position,
        moves: list[Move],
        tt_move: Move | None = None,
        ply: int = 0,
    ) -> list[Move]:
        return sorted(
            moves,
            key=lambda move: self._move_order_score(position, move, tt_move, ply),
            reverse=True,
        )

    def _move_order_score(
        self,
        position: Position,
        move: Move,
        tt_move: Move | None = None,
        ply: int = 0,
    ) -> int:
        moving_piece = position.board[move.from_sq]
        if moving_piece is None:
            return -_INF_SCORE

        is_quiet = self._is_quiet_move(position, move)
        score = 0
        if tt_move is not None and move == tt_move:
            score += 100_000

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
        elif is_quiet:
            score += self._killer_score(move, ply)
            score += self._history_score(position.side_to_move, move)

        if move.flag in (MoveFlag.CASTLE_KINGSIDE, MoveFlag.CASTLE_QUEENSIDE):
            score += 120

        score += self._piece_square_delta(
            moving_piece.piece_type,
            moving_piece.color,
            move.from_sq,
            move.to_sq,
        )
        return score

    def _store_tt(
        self,
        key: int,
        depth: int,
        score: int,
        bound: int,
        best_move: Move | None,
    ) -> None:
        existing = self._tt.get(key)
        if existing is not None and existing.depth > depth:
            return
        if len(self._tt) >= self._tt_max_entries and key not in self._tt:
            self._tt.clear()
        self._tt[key] = _TTEntry(
            depth=depth, score=score, bound=bound, best_move=best_move
        )

    def _is_noisy_move(self, position: Position, move: Move) -> bool:
        if move.flag in (MoveFlag.EN_PASSANT, MoveFlag.PROMOTION):
            return True
        return position.board[move.to_sq] is not None

    def _can_try_lmr(
        self,
        depth: int,
        move_index: int,
        in_check: bool,
        is_quiet: bool,
        move: Move,
        tt_move: Move | None,
    ) -> bool:
        if in_check:
            return False
        if depth < _LMR_MIN_DEPTH:
            return False
        if move_index < _LMR_MIN_MOVE_INDEX:
            return False
        if not is_quiet:
            return False
        return tt_move is None or move != tt_move

    def _lmr_reduction(self, depth: int, move_index: int) -> int:
        reduction = 1
        if depth >= 8 and move_index >= 8:
            reduction += 1
        return reduction

    def _can_apply_null_move(
        self,
        position: Position,
        depth: int,
        in_check: bool,
        allow_null: bool,
    ) -> bool:
        if not allow_null or in_check:
            return False
        if depth < _NULL_MOVE_MIN_DEPTH:
            return False
        return self._has_non_pawn_material(position, position.side_to_move)

    def _has_non_pawn_material(self, position: Position, side: Color) -> bool:
        for sq in position.board.all_pieces(side):
            piece = position.board[sq]
            if piece is None:
                continue
            if piece.piece_type not in (PieceType.KING, PieceType.PAWN):
                return True
        return False

    def _make_null_move(self, position: Position) -> _NullMoveState:
        state = _NullMoveState(
            side_to_move=position.side_to_move,
            en_passant=position.en_passant,
            halfmove_clock=position.halfmove_clock,
            fullmove_number=position.fullmove_number,
        )
        position._set_en_passant(None)
        position.halfmove_clock += 1
        if position.side_to_move == Color.BLACK:
            position.fullmove_number += 1
        position.side_to_move = position.side_to_move.opposite
        position._toggle_side_hash()

        key = position._position_key()
        position._key_stack.append(key)
        position._key_counts[key] = position._key_counts.get(key, 0) + 1
        return state

    def _unmake_null_move(self, position: Position, state: _NullMoveState) -> None:
        key = position._key_stack.pop()
        key_count = position._key_counts[key] - 1
        if key_count:
            position._key_counts[key] = key_count
        else:
            del position._key_counts[key]

        position.side_to_move = state.side_to_move
        position.en_passant = state.en_passant
        position.halfmove_clock = state.halfmove_clock
        position.fullmove_number = state.fullmove_number
        position._zobrist_hash = position._key_stack[-1]

    def _is_quiet_move(self, position: Position, move: Move) -> bool:
        if move.flag in (MoveFlag.PROMOTION, MoveFlag.EN_PASSANT):
            return False
        return position.board[move.to_sq] is None

    def _reset_move_order_heuristics(self) -> None:
        self._killer_moves = [[None, None] for _ in range(_MAX_KILLER_PLY)]
        self._history_scores = [
            [[0 for _ in range(64)] for _ in range(64)] for _ in range(2)
        ]

    def _record_killer(self, move: Move, ply: int) -> None:
        if ply < 0 or ply >= len(self._killer_moves):
            return
        killers = self._killer_moves[ply]
        if killers[0] == move:
            return
        killers[1] = killers[0]
        killers[0] = move

    def _killer_score(self, move: Move, ply: int) -> int:
        if ply < 0 or ply >= len(self._killer_moves):
            return 0
        killers = self._killer_moves[ply]
        if killers[0] == move:
            return _KILLER_PRIMARY_BONUS
        if killers[1] == move:
            return _KILLER_SECONDARY_BONUS
        return 0

    def _history_score(self, side: Color, move: Move) -> int:
        return self._history_scores[int(side)][move.from_sq][move.to_sq]

    def _update_history(self, side: Color, move: Move, depth: int) -> None:
        bonus = max(depth, 1) * max(depth, 1) * _HISTORY_BONUS_FACTOR
        side_scores = self._history_scores[int(side)]
        current = side_scores[move.from_sq][move.to_sq]
        side_scores[move.from_sq][move.to_sq] = min(_HISTORY_MAX_SCORE, current + bonus)

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
