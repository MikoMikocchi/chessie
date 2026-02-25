"""Perft tests — the gold standard for move-generator correctness.

Reference values: https://www.chessprogramming.org/Perft_Results
"""

import pytest

from chessy.core.move_generator import MoveGenerator
from chessy.core.notation import position_from_fen, STARTING_FEN
from chessy.core.position import Position


def perft(position: Position, depth: int) -> int:
    """Count leaf nodes at *depth* using make/unmake."""
    if depth == 0:
        return 1
    gen = MoveGenerator(position)
    moves = gen.generate_legal_moves()
    nodes = 0
    for move in moves:
        position.make_move(move)
        nodes += perft(position, depth - 1)
        position.unmake_move(move)
    return nodes


# ── Starting position ────────────────────────────────────────────────────────


class TestPerftStarting:
    def test_depth_1(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert perft(pos, 1) == 20

    def test_depth_2(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert perft(pos, 2) == 400

    def test_depth_3(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert perft(pos, 3) == 8_902

    @pytest.mark.slow
    def test_depth_4(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert perft(pos, 4) == 197_281


# ── Kiwipete (rich in tactics: castling, ep, promotions) ─────────────────────

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


class TestPerftKiwipete:
    def test_depth_1(self) -> None:
        pos = position_from_fen(KIWIPETE)
        assert perft(pos, 1) == 48

    def test_depth_2(self) -> None:
        pos = position_from_fen(KIWIPETE)
        assert perft(pos, 2) == 2_039

    def test_depth_3(self) -> None:
        pos = position_from_fen(KIWIPETE)
        assert perft(pos, 3) == 97_862


# ── Position 3: en-passant + promotion edge cases ───────────────────────────

POS3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"


class TestPerftPos3:
    def test_depth_1(self) -> None:
        pos = position_from_fen(POS3)
        assert perft(pos, 1) == 14

    def test_depth_2(self) -> None:
        pos = position_from_fen(POS3)
        assert perft(pos, 2) == 191

    def test_depth_3(self) -> None:
        pos = position_from_fen(POS3)
        assert perft(pos, 3) == 2_812


# ── Position 4: mirrored, many promotions ────────────────────────────────────

POS4 = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"


class TestPerftPos4:
    def test_depth_1(self) -> None:
        pos = position_from_fen(POS4)
        assert perft(pos, 1) == 6

    def test_depth_2(self) -> None:
        pos = position_from_fen(POS4)
        assert perft(pos, 2) == 264

    def test_depth_3(self) -> None:
        pos = position_from_fen(POS4)
        assert perft(pos, 3) == 9_467


# ── Position 5 ───────────────────────────────────────────────────────────────

POS5 = "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8"


class TestPerftPos5:
    def test_depth_1(self) -> None:
        pos = position_from_fen(POS5)
        assert perft(pos, 1) == 44

    def test_depth_2(self) -> None:
        pos = position_from_fen(POS5)
        assert perft(pos, 2) == 1_486

    def test_depth_3(self) -> None:
        pos = position_from_fen(POS5)
        assert perft(pos, 3) == 62_379
