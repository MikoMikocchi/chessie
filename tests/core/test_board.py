"""Tests for Board."""

import pytest

from chessy.core.board import Board
from chessy.core.enums import Color, PieceType
from chessy.core.piece import Piece
from chessy.core.types import (
    A1, B1, C1, D1, E1, F1, G1, H1,
    E2,
    A8, B8, C8, D8, E8, F8, G8, H8,
    E4,
)


class TestBoardInitial:
    def test_white_king_position(self) -> None:
        board = Board.initial()
        assert board[E1] == Piece(Color.WHITE, PieceType.KING)

    def test_black_king_position(self) -> None:
        board = Board.initial()
        assert board[E8] == Piece(Color.BLACK, PieceType.KING)

    def test_white_back_rank(self) -> None:
        board = Board.initial()
        expected = [
            (A1, PieceType.ROOK), (B1, PieceType.KNIGHT), (C1, PieceType.BISHOP),
            (D1, PieceType.QUEEN), (E1, PieceType.KING), (F1, PieceType.BISHOP),
            (G1, PieceType.KNIGHT), (H1, PieceType.ROOK),
        ]
        for sq, pt in expected:
            assert board[sq] == Piece(Color.WHITE, pt), f"Mismatch at square {sq}"

    def test_black_back_rank(self) -> None:
        board = Board.initial()
        expected = [
            (A8, PieceType.ROOK), (B8, PieceType.KNIGHT), (C8, PieceType.BISHOP),
            (D8, PieceType.QUEEN), (E8, PieceType.KING), (F8, PieceType.BISHOP),
            (G8, PieceType.KNIGHT), (H8, PieceType.ROOK),
        ]
        for sq, pt in expected:
            assert board[sq] == Piece(Color.BLACK, pt), f"Mismatch at square {sq}"

    def test_white_pawns(self) -> None:
        board = Board.initial()
        pawns = board.pieces(Color.WHITE, PieceType.PAWN)
        assert len(pawns) == 8
        assert all(8 <= sq < 16 for sq in pawns)  # rank 2

    def test_black_pawns(self) -> None:
        board = Board.initial()
        pawns = board.pieces(Color.BLACK, PieceType.PAWN)
        assert len(pawns) == 8
        assert all(48 <= sq < 56 for sq in pawns)  # rank 7

    def test_empty_middle(self) -> None:
        board = Board.initial()
        for sq in range(16, 48):
            assert board[sq] is None


class TestBoardOperations:
    def test_set_and_get(self) -> None:
        board = Board()
        piece = Piece(Color.WHITE, PieceType.PAWN)
        board[E4] = piece
        assert board[E4] == piece
        assert board.is_empty(E2)

    def test_copy_independence(self) -> None:
        board = Board.initial()
        copy = board.copy()
        assert board == copy
        copy[E1] = None
        assert board != copy
        assert board[E1] == Piece(Color.WHITE, PieceType.KING)

    def test_king_square(self) -> None:
        board = Board.initial()
        assert board.king_square(Color.WHITE) == E1
        assert board.king_square(Color.BLACK) == E8

    def test_king_square_missing_raises(self) -> None:
        board = Board()
        with pytest.raises(ValueError, match="No WHITE king"):
            board.king_square(Color.WHITE)

    def test_all_pieces_count(self) -> None:
        board = Board.initial()
        assert len(board.all_pieces(Color.WHITE)) == 16
        assert len(board.all_pieces(Color.BLACK)) == 16

    def test_clear(self) -> None:
        board = Board.initial()
        board.clear()
        assert all(board[sq] is None for sq in range(64))

    def test_repr_not_empty(self) -> None:
        board = Board.initial()
        text = repr(board)
        assert "K" in text
        assert "a b c d e f g h" in text
