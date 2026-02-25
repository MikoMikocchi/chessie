"""Tests for Position make/unmake."""

from chessy.core.enums import CastlingRights, Color, MoveFlag, PieceType
from chessy.core.move import Move
from chessy.core.move_generator import MoveGenerator
from chessy.core.notation import STARTING_FEN, position_from_fen, position_to_fen
from chessy.core.piece import Piece
from chessy.core.types import (
    E1, E2, E4, D5, D7,
    parse_square,
)


class TestMakeUnmake:
    def test_side_switches(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        move = Move(E2, E4, MoveFlag.DOUBLE_PAWN)
        pos.make_move(move)
        assert pos.side_to_move == Color.BLACK

    def test_unmake_restores_side(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        move = Move(E2, E4, MoveFlag.DOUBLE_PAWN)
        pos.make_move(move)
        pos.unmake_move(move)
        assert pos.side_to_move == Color.WHITE

    def test_unmake_restores_fen(self) -> None:
        """After make+unmake of every legal move, FEN must match original."""
        pos = position_from_fen(STARTING_FEN)
        fen_before = position_to_fen(pos)
        gen = MoveGenerator(pos)
        for move in gen.generate_legal_moves():
            pos.make_move(move)
            pos.unmake_move(move)
            assert position_to_fen(pos) == fen_before, f"Failed for {move}"

    def test_en_passant_set(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        pos.make_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        assert pos.en_passant == parse_square("e3")

    def test_en_passant_cleared(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        pos.make_move(Move(E2, E4, MoveFlag.DOUBLE_PAWN))
        pos.make_move(Move(D7, D5, MoveFlag.DOUBLE_PAWN))
        assert pos.en_passant == parse_square("d6")  # new ep, old cleared

    def test_capture_restores_piece(self) -> None:
        # Simplified position: white pawn on e4, black pawn on d5
        fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"
        pos = position_from_fen(fen)
        fen_before = position_to_fen(pos)
        capture = Move(E4, D5)  # exd5
        pos.make_move(capture)
        assert pos.board[D5] == Piece(Color.WHITE, PieceType.PAWN)
        pos.unmake_move(capture)
        assert position_to_fen(pos) == fen_before


class TestCastlingRightsUpdate:
    def test_king_move_removes_rights(self) -> None:
        pos = position_from_fen(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
        )
        pos.make_move(Move(E1, E2))  # king moves
        assert not (pos.castling & CastlingRights.WHITE_BOTH)

    def test_rook_move_removes_one_right(self) -> None:
        pos = position_from_fen(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
        )
        pos.make_move(Move(parse_square("a1"), parse_square("a2")))
        assert not (pos.castling & CastlingRights.WHITE_QUEENSIDE)
        assert bool(pos.castling & CastlingRights.WHITE_KINGSIDE)

    def test_castling_kingside(self) -> None:
        pos = position_from_fen(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
        )
        move = Move(E1, parse_square("g1"), MoveFlag.CASTLE_KINGSIDE)
        pos.make_move(move)
        assert pos.board[parse_square("g1")] == Piece(Color.WHITE, PieceType.KING)
        assert pos.board[parse_square("f1")] == Piece(Color.WHITE, PieceType.ROOK)
        assert pos.board[parse_square("h1")] is None

    def test_castling_queenside(self) -> None:
        pos = position_from_fen(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
        )
        move = Move(E1, parse_square("c1"), MoveFlag.CASTLE_QUEENSIDE)
        pos.make_move(move)
        assert pos.board[parse_square("c1")] == Piece(Color.WHITE, PieceType.KING)
        assert pos.board[parse_square("d1")] == Piece(Color.WHITE, PieceType.ROOK)
        assert pos.board[parse_square("a1")] is None


class TestPromotion:
    def test_promote_to_queen(self) -> None:
        fen = "8/4P3/8/8/8/8/4k3/4K3 w - - 0 1"
        pos = position_from_fen(fen)
        move = Move(
            parse_square("e7"), parse_square("e8"),
            MoveFlag.PROMOTION, PieceType.QUEEN,
        )
        pos.make_move(move)
        assert pos.board[parse_square("e8")] == Piece(Color.WHITE, PieceType.QUEEN)

    def test_promote_unmake_restores_pawn(self) -> None:
        fen = "8/4P3/8/8/8/8/4k3/4K3 w - - 0 1"
        pos = position_from_fen(fen)
        fen_before = position_to_fen(pos)
        move = Move(
            parse_square("e7"), parse_square("e8"),
            MoveFlag.PROMOTION, PieceType.QUEEN,
        )
        pos.make_move(move)
        pos.unmake_move(move)
        assert position_to_fen(pos) == fen_before
