/// @file test_piece.cpp
/// Tests for piece.hpp: Piece creation, FEN character conversion.

#include <chessie/piece.hpp>

#include <gtest/gtest.h>

namespace chessie {

TEST(Piece, FenChar) {
    EXPECT_EQ((Piece{Color::White, PieceType::Pawn}.fen_char()), 'P');
    EXPECT_EQ((Piece{Color::White, PieceType::Knight}.fen_char()), 'N');
    EXPECT_EQ((Piece{Color::White, PieceType::Bishop}.fen_char()), 'B');
    EXPECT_EQ((Piece{Color::White, PieceType::Rook}.fen_char()), 'R');
    EXPECT_EQ((Piece{Color::White, PieceType::Queen}.fen_char()), 'Q');
    EXPECT_EQ((Piece{Color::White, PieceType::King}.fen_char()), 'K');
    EXPECT_EQ((Piece{Color::Black, PieceType::Pawn}.fen_char()), 'p');
    EXPECT_EQ((Piece{Color::Black, PieceType::King}.fen_char()), 'k');
}

TEST(Piece, FromFenChar) {
    EXPECT_EQ(Piece::from_fen_char('P'), (Piece{Color::White, PieceType::Pawn}));
    EXPECT_EQ(Piece::from_fen_char('k'), (Piece{Color::Black, PieceType::King}));
    EXPECT_EQ(Piece::from_fen_char('Q'), (Piece{Color::White, PieceType::Queen}));
    EXPECT_EQ(Piece::from_fen_char('n'), (Piece{Color::Black, PieceType::Knight}));
}

TEST(Piece, FromFenCharInvalid) {
    Piece p = Piece::from_fen_char('x');
    EXPECT_EQ(p.type, PieceType::None);
}

TEST(Piece, RoundTrip) {
    // Every valid FEN char should round-trip through from_fen_char → fen_char
    const char chars[] = {'P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k'};
    for (char c : chars) {
        Piece p = Piece::from_fen_char(c);
        EXPECT_EQ(p.fen_char(), c) << "Round-trip failed for '" << c << "'";
    }
}

TEST(Piece, Equality) {
    Piece wp{Color::White, PieceType::Pawn};
    Piece bp{Color::Black, PieceType::Pawn};
    Piece wp2{Color::White, PieceType::Pawn};
    EXPECT_EQ(wp, wp2);
    EXPECT_NE(wp, bp);
}

TEST(Piece, NoPieceSentinel) {
    EXPECT_EQ(kNoPiece.type, PieceType::None);
}

}  // namespace chessie
