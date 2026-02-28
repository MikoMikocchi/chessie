/// @file test_types.cpp
/// Tests for types.hpp: Square helpers, Color, PieceType, CastlingRights, MoveFlag.

#include <chessie/types.hpp>

#include <gtest/gtest.h>

namespace chessie {

// ── Square helpers ──────────────────────────────────────────────────────────

TEST(Types, FileOfRankOf) {
    EXPECT_EQ(file_of(A1), 0);
    EXPECT_EQ(rank_of(A1), 0);
    EXPECT_EQ(file_of(H8), 7);
    EXPECT_EQ(rank_of(H8), 7);
    EXPECT_EQ(file_of(E4), 4);
    EXPECT_EQ(rank_of(E4), 3);
}

TEST(Types, MakeSquare) {
    EXPECT_EQ(make_square(0, 0), A1);
    EXPECT_EQ(make_square(7, 7), H8);
    EXPECT_EQ(make_square(4, 3), E4);
}

TEST(Types, IsValidSquare) {
    EXPECT_TRUE(is_valid_square(0));
    EXPECT_TRUE(is_valid_square(63));
    EXPECT_FALSE(is_valid_square(-1));
    EXPECT_FALSE(is_valid_square(64));
}

TEST(Types, SquareName) {
    EXPECT_EQ(square_name(A1), "a1");
    EXPECT_EQ(square_name(H8), "h8");
    EXPECT_EQ(square_name(E4), "e4");
    EXPECT_EQ(square_name(D7), "d7");
}

TEST(Types, ParseSquare) {
    EXPECT_EQ(parse_square("a1"), A1);
    EXPECT_EQ(parse_square("h8"), H8);
    EXPECT_EQ(parse_square("e4"), E4);
    EXPECT_EQ(parse_square(""), kNoSquare);
    EXPECT_EQ(parse_square("z9"), kNoSquare);
    EXPECT_EQ(parse_square("abc"), kNoSquare);
}

TEST(Types, NamedSquareConstants) {
    EXPECT_EQ(A1, 0);
    EXPECT_EQ(B1, 1);
    EXPECT_EQ(H1, 7);
    EXPECT_EQ(A2, 8);
    EXPECT_EQ(H8, 63);
}

// ── Color ───────────────────────────────────────────────────────────────────

TEST(Types, ColorOpposite) {
    EXPECT_EQ(opposite(Color::White), Color::Black);
    EXPECT_EQ(opposite(Color::Black), Color::White);
}

TEST(Types, ColorIndex) {
    EXPECT_EQ(color_index(Color::White), 0);
    EXPECT_EQ(color_index(Color::Black), 1);
}

// ── PieceType ───────────────────────────────────────────────────────────────

TEST(Types, PieceIndex) {
    EXPECT_EQ(piece_index(PieceType::Pawn), 0);
    EXPECT_EQ(piece_index(PieceType::King), 5);
    EXPECT_EQ(piece_index(PieceType::Queen), 4);
}

// ── CastlingRights ──────────────────────────────────────────────────────────

TEST(Types, CastlingRightsBitOps) {
    auto cr = kWhiteKingside | kBlackQueenside;
    EXPECT_EQ(cr & kWhiteKingside, kWhiteKingside);
    EXPECT_EQ(cr & kWhiteQueenside, kCastlingNone);
    EXPECT_EQ(cr & kBlackQueenside, kBlackQueenside);
}

TEST(Types, CastlingRightsAll) {
    EXPECT_EQ(kCastlingAll, kWhiteKingside | kWhiteQueenside | kBlackKingside | kBlackQueenside);
}

TEST(Types, CastlingRightsComplement) {
    auto removed = kCastlingAll & ~kWhiteKingside;
    EXPECT_EQ(removed & kWhiteKingside, kCastlingNone);
    EXPECT_NE(removed & kWhiteQueenside, kCastlingNone);
    EXPECT_NE(removed & kBlackKingside, kCastlingNone);
}

TEST(Types, CastlingRightsAssignOps) {
    CastlingRights cr = kCastlingNone;
    cr |= kWhiteKingside;
    EXPECT_EQ(cr, kWhiteKingside);
    cr |= kBlackBoth;
    EXPECT_EQ(cr & kBlackKingside, kBlackKingside);
    cr &= ~kBlackKingside;
    EXPECT_EQ(cr & kBlackKingside, kCastlingNone);
}

}  // namespace chessie
