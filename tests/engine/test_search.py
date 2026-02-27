"""Tests for the built-in Python chess engine."""

from chessie.core.enums import Color
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.notation import STARTING_FEN, position_from_fen
from chessie.core.rules import Rules
from chessie.core.types import parse_square
from chessie.engine import PythonSearchEngine, SearchLimits


class _NullTrackingEngine(PythonSearchEngine):
    def __init__(self) -> None:
        super().__init__()
        self.null_move_calls = 0

    def _make_null_move(self, position):
        self.null_move_calls += 1
        return super()._make_null_move(position)


class TestPythonSearchEngine:
    def test_returns_legal_move_from_start(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        engine = PythonSearchEngine()

        result = engine.search(pos, SearchLimits(max_depth=2, time_limit_ms=None))
        legal = MoveGenerator(pos).generate_legal_moves()

        assert result.best_move in legal
        assert result.depth >= 1
        assert result.nodes > 0

    def test_finds_mate_in_one(self) -> None:
        pos = position_from_fen("6k1/7Q/6K1/8/8/8/8/8 w - - 0 1")
        engine = PythonSearchEngine()

        result = engine.search(pos, SearchLimits(max_depth=3, time_limit_ms=None))
        assert result.best_move is not None

        pos.make_move(result.best_move)
        assert Rules.is_checkmate(pos)

    def test_returns_none_for_checkmated_side(self) -> None:
        # Fool's mate position: white to move is already checkmated.
        pos = position_from_fen(
            "rnbqkbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        )
        engine = PythonSearchEngine()

        result = engine.search(pos, SearchLimits(max_depth=3, time_limit_ms=None))
        assert result.best_move is None
        assert result.score_cp <= -90_000

    def test_honors_cancel_callback(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        engine = PythonSearchEngine()

        result = engine.search(
            pos,
            SearchLimits(max_depth=6, time_limit_ms=None),
            is_cancelled=lambda: True,
        )

        legal = MoveGenerator(pos).generate_legal_moves()
        assert result.best_move in legal
        assert result.depth == 0

    def test_populates_transposition_table(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        engine = PythonSearchEngine()

        _ = engine.search(pos, SearchLimits(max_depth=3, time_limit_ms=None))

        assert len(engine._tt) > 0

    def test_killer_move_is_prioritized_among_quiet_moves(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        engine = PythonSearchEngine()
        killer = Move(parse_square("g1"), parse_square("f3"))
        other = Move(parse_square("b1"), parse_square("c3"))

        engine._record_killer(killer, ply=2)
        ordered = engine._order_moves(pos, [other, killer], ply=2)

        assert ordered[0] == killer

    def test_history_heuristic_prioritizes_quiet_move(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        engine = PythonSearchEngine()
        favored = Move(parse_square("d2"), parse_square("d4"))
        other = Move(parse_square("e2"), parse_square("e4"))

        for _ in range(3):
            engine._update_history(pos.side_to_move, favored, depth=6)
        ordered = engine._order_moves(pos, [other, favored], ply=1)

        assert ordered[0] == favored

    def test_uses_null_move_pruning_in_normal_position(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        engine = _NullTrackingEngine()

        _ = engine.search(pos, SearchLimits(max_depth=4, time_limit_ms=None))

        assert engine.null_move_calls > 0

    def test_skips_null_move_pruning_in_pawn_only_endgame(self) -> None:
        pos = position_from_fen("8/3k4/8/8/8/4K3/3P4/8 w - - 0 1")
        engine = _NullTrackingEngine()

        _ = engine.search(pos, SearchLimits(max_depth=5, time_limit_ms=None))

        assert engine.null_move_calls == 0

    def test_null_move_round_trip_restores_position_state(self) -> None:
        pos = position_from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        engine = PythonSearchEngine()

        initial_key_stack = pos._key_stack.copy()
        initial_key_counts = pos._key_counts.copy()
        initial_side = pos.side_to_move
        initial_en_passant = pos.en_passant
        initial_halfmove = pos.halfmove_clock
        initial_fullmove = pos.fullmove_number

        state = engine._make_null_move(pos)
        assert pos.side_to_move == Color.WHITE
        assert pos.en_passant is None

        engine._unmake_null_move(pos, state)

        assert pos.side_to_move == initial_side
        assert pos.en_passant == initial_en_passant
        assert pos.halfmove_clock == initial_halfmove
        assert pos.fullmove_number == initial_fullmove
        assert pos._key_stack == initial_key_stack
        assert pos._key_counts == initial_key_counts
