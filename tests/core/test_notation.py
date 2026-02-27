"""Tests for FEN and SAN notation."""

import pytest

from chessie.core.enums import CastlingRights, Color, GameResult, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.notation import (
    STARTING_FEN,
    ParsedPgn,
    build_pgn,
    game_result_from_pgn,
    move_to_san,
    parse_pgn,
    parse_pgn_game,
    parse_san,
    pgn_result_token,
    position_from_fen,
    position_to_fen,
)
from chessie.core.piece import Piece
from chessie.core.types import E1, E2, E3, E4, E8, parse_square


class TestFenParsing:
    def test_starting_side(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert pos.side_to_move == Color.WHITE

    def test_starting_castling(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert pos.castling == CastlingRights.ALL

    def test_starting_en_passant(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert pos.en_passant is None

    def test_starting_clocks(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert pos.halfmove_clock == 0
        assert pos.fullmove_number == 1

    def test_starting_kings(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert pos.board[E1] == Piece(Color.WHITE, PieceType.KING)
        assert pos.board[E8] == Piece(Color.BLACK, PieceType.KING)

    def test_en_passant_square(self) -> None:
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        pos = position_from_fen(fen)
        assert pos.en_passant == E3

    def test_no_castling(self) -> None:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
        pos = position_from_fen(fen)
        assert pos.castling == CastlingRights.NONE

    def test_partial_castling(self) -> None:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w Kq - 0 1"
        pos = position_from_fen(fen)
        assert pos.castling == (
            CastlingRights.WHITE_KINGSIDE | CastlingRights.BLACK_QUEENSIDE
        )

    def test_invalid_fen_raises(self) -> None:
        with pytest.raises(ValueError):
            position_from_fen("invalid")

    def test_invalid_side_to_move_raises(self) -> None:
        with pytest.raises(ValueError, match="side-to-move"):
            position_from_fen("8/8/8/8/8/8/8/8 x - - 0 1")

    def test_invalid_board_rank_count_raises(self) -> None:
        with pytest.raises(ValueError, match="8 ranks"):
            position_from_fen("8/8/8/8/8/8/8 w - - 0 1")

    def test_invalid_board_rank_width_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid FEN"):
            position_from_fen("9/8/8/8/8/8/8/8 w - - 0 1")

    def test_invalid_castling_field_raises(self) -> None:
        with pytest.raises(ValueError, match="castling"):
            position_from_fen("8/8/8/8/8/8/8/8 w Kx - 0 1")

    def test_invalid_en_passant_for_side_raises(self) -> None:
        with pytest.raises(ValueError, match="en-passant"):
            position_from_fen("8/8/8/8/8/8/8/8 w - e3 0 1")


class TestFenSerialisation:
    def test_roundtrip_starting(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        assert position_to_fen(pos) == STARTING_FEN

    def test_roundtrip_after_e4(self) -> None:
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        pos = position_from_fen(fen)
        assert position_to_fen(pos) == fen

    def test_roundtrip_custom(self) -> None:
        fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        pos = position_from_fen(fen)
        assert position_to_fen(pos) == fen

    def test_roundtrip_endgame(self) -> None:
        fen = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
        pos = position_from_fen(fen)
        assert position_to_fen(pos) == fen


class TestSAN:
    def test_pawn_push(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        move = Move(E2, E4, MoveFlag.DOUBLE_PAWN)
        assert move_to_san(pos, move) == "e4"

    def test_knight_move(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        nf3 = Move(parse_square("g1"), parse_square("f3"))
        san = move_to_san(pos, nf3)
        assert san == "Nf3"

    def test_parse_san_e4(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        move = parse_san(pos, "e4")
        assert move.to_sq == E4
        assert move.flag == MoveFlag.DOUBLE_PAWN

    def test_parse_san_nf3(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        move = parse_san(pos, "Nf3")
        assert move.to_sq == parse_square("f3")
        assert move.from_sq == parse_square("g1")

    def test_parse_san_illegal_raises(self) -> None:
        pos = position_from_fen(STARTING_FEN)
        with pytest.raises(ValueError, match="Illegal"):
            parse_san(pos, "Ke5")

    def test_san_roundtrip(self) -> None:
        """parse_san(move_to_san(m)) should return the same move."""
        pos = position_from_fen(STARTING_FEN)
        from chessie.core.move_generator import MoveGenerator

        gen = MoveGenerator(pos)
        for move in gen.generate_legal_moves():
            san = move_to_san(pos, move)
            parsed = parse_san(pos, san)
            assert parsed == move, f"Roundtrip failed for {san}: {move} ≠ {parsed}"

    def test_parse_san_zero_castling_notation(self) -> None:
        pos = position_from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        move = parse_san(pos, "0-0")
        assert move.flag == MoveFlag.CASTLE_KINGSIDE

    def test_move_to_san_knight_disambiguation_file(self) -> None:
        pos = position_from_fen("7k/8/8/8/8/8/8/K1N3N1 w - - 0 1")
        move = Move(parse_square("c1"), parse_square("e2"))
        assert move_to_san(pos, move) == "Nce2"

    def test_parse_san_ambiguous_knight_raises(self) -> None:
        pos = position_from_fen("7k/8/8/8/8/8/8/K1N3N1 w - - 0 1")
        with pytest.raises(ValueError, match="Ambiguous"):
            parse_san(pos, "Ne2")

    def test_parse_san_promotion_with_check_suffix(self) -> None:
        pos = position_from_fen("7k/6P1/8/8/8/8/8/4K3 w - - 0 1")
        move = parse_san(pos, "g8=Q+")
        assert move.to_sq == parse_square("g8")
        assert move.flag == MoveFlag.PROMOTION
        assert move.promotion == PieceType.QUEEN

    def test_move_to_san_castling_both_sides(self) -> None:
        pos = position_from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        king_side = Move(parse_square("e1"), parse_square("g1"), MoveFlag.CASTLE_KINGSIDE)
        queen_side = Move(parse_square("e1"), parse_square("c1"), MoveFlag.CASTLE_QUEENSIDE)
        assert move_to_san(pos, king_side) == "O-O"
        assert move_to_san(pos, queen_side) == "O-O-O"

    def test_move_to_san_pawn_capture_and_promotion(self) -> None:
        pos_capture = position_from_fen("7k/8/8/4p3/3P4/8/8/4K3 w - - 0 1")
        capture = Move(parse_square("d4"), parse_square("e5"))
        assert move_to_san(pos_capture, capture) == "dxe5"

        pos_promo = position_from_fen("7k/6P1/8/8/8/8/8/4K3 w - - 0 1")
        promo = Move(parse_square("g7"), parse_square("g8"), MoveFlag.PROMOTION, PieceType.QUEEN)
        assert move_to_san(pos_promo, promo) == "g8=Q+"

    def test_parse_san_file_and_rank_disambiguation(self) -> None:
        pos = position_from_fen("7k/8/8/8/8/8/8/K1N3N1 w - - 0 1")
        move = parse_san(pos, "Nce2")
        assert move.from_sq == parse_square("c1")
        assert move.to_sq == parse_square("e2")

        pos_rank = position_from_fen("7k/8/8/8/8/8/R7/4R2K w - - 0 1")
        move_rank = parse_san(pos_rank, "R1e2")
        assert move_rank.from_sq == parse_square("e1")
        assert move_rank.to_sq == parse_square("e2")


class TestPGN:
    def test_build_and_parse_roundtrip(self) -> None:
        headers = {
            "Event": "Test",
            "Site": "Local",
            "Date": "2026.02.26",
            "Round": "-",
            "White": "Alice",
            "Black": "Bob",
            "Result": "1-0",
        }
        pgn_text = build_pgn(headers, ["e4", "e5", "Nf3"], "1-0")
        parsed_headers, sans, result_token = parse_pgn(pgn_text)

        assert parsed_headers == headers
        assert sans == ["e4", "e5", "Nf3"]
        assert result_token == "1-0"

    def test_parse_pgn_ignores_comments_and_variations(self) -> None:
        pgn_text = """
[Event "Annotated"]
[Result "1/2-1/2"]

1. e4 {central push} e5 (1... c5) 2. Nf3 Nc6 1/2-1/2
"""
        _headers, sans, result_token = parse_pgn(pgn_text)
        assert sans == ["e4", "e5", "Nf3", "Nc6"]
        assert result_token == "1/2-1/2"

    def test_parse_pgn_game_keeps_mainline_comments(self) -> None:
        pgn_text = """
[Event "Annotated"]
[Result "*"]

1. e4 {Best by test} e5 (1... c5 {Sicilian}) 2. Nf3 ;Developing move
*
"""
        parsed = parse_pgn_game(pgn_text)

        assert isinstance(parsed, ParsedPgn)
        assert [move.san for move in parsed.moves] == ["e4", "e5", "Nf3"]
        assert parsed.moves[0].comment == "Best by test"
        assert parsed.moves[1].comment == ""
        assert parsed.moves[2].comment == "Developing move"
        assert parsed.result_token == "*"

    def test_build_pgn_with_comments_roundtrip(self) -> None:
        headers = {"Event": "Commented", "Result": "*"}
        pgn_text = build_pgn(
            headers=headers,
            sans=["e4", "e5", "Nf3"],
            result_token="*",
            comments=["central push", None, "developing move"],
        )
        parsed = parse_pgn_game(pgn_text)

        assert [move.san for move in parsed.moves] == ["e4", "e5", "Nf3"]
        assert [move.comment for move in parsed.moves] == [
            "central push",
            "",
            "developing move",
        ]

    def test_parse_pgn_uses_header_result_when_movetext_omits_it(self) -> None:
        pgn_text = """
[Event "NoResultToken"]
[Result "0-1"]

1. d4 d5
"""
        headers, sans, result_token = parse_pgn(pgn_text)
        assert headers["Result"] == "0-1"
        assert sans == ["d4", "d5"]
        assert result_token == "0-1"

    def test_build_pgn_rejects_comment_count_mismatch(self) -> None:
        with pytest.raises(ValueError, match="comments length"):
            build_pgn(
                headers={"Event": "Mismatch", "Result": "*"},
                sans=["e4", "e5"],
                result_token="*",
                comments=["only one"],
            )

    def test_result_token_mapping(self) -> None:
        assert pgn_result_token(GameResult.WHITE_WINS) == "1-0"
        assert pgn_result_token(GameResult.BLACK_WINS) == "0-1"
        assert pgn_result_token(GameResult.DRAW) == "1/2-1/2"
        assert pgn_result_token(GameResult.IN_PROGRESS) == "*"

        assert game_result_from_pgn("1-0") == GameResult.WHITE_WINS
        assert game_result_from_pgn("0-1") == GameResult.BLACK_WINS
        assert game_result_from_pgn("1/2-1/2") == GameResult.DRAW
        assert game_result_from_pgn("*") == GameResult.IN_PROGRESS
