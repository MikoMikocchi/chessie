#include <chessie/bitboard.hpp>
#include <chessie/magic.hpp>

#include <gtest/gtest.h>

using namespace chessie;

class MagicTest : public ::testing::Test {
   protected:
    static void SetUpTestSuite() { magic::init(); }
};

// ── Bishop attacks ──────────────────────────────────────────────────────────

TEST_F(MagicTest, BishopE4EmptyBoard) {
    // Bishop on e4, empty board — should see 13 squares on diagonals
    Bitboard attacks = magic::bishop_attacks(E4, kEmptyBB);
    EXPECT_EQ(popcount(attacks), 13);

    // Should reach corners
    EXPECT_TRUE(test_bit(attacks, A8));  // NW diagonal
    EXPECT_TRUE(test_bit(attacks, H7));  // NE diagonal
    EXPECT_TRUE(test_bit(attacks, B1));  // SW diagonal
    EXPECT_TRUE(test_bit(attacks, H1));  // SE diagonal
}

TEST_F(MagicTest, BishopA1EmptyBoard) {
    Bitboard attacks = magic::bishop_attacks(A1, kEmptyBB);
    EXPECT_EQ(popcount(attacks), 7);  // only a1-h8 diagonal
    EXPECT_TRUE(test_bit(attacks, H8));
    EXPECT_FALSE(test_bit(attacks, A1));  // doesn't include own square
}

TEST_F(MagicTest, BishopBlockedByPiece) {
    // Bishop on e4 with a piece on f5 — should not see beyond f5
    Bitboard occ = square_bb(F5);
    Bitboard attacks = magic::bishop_attacks(E4, occ);

    EXPECT_TRUE(test_bit(attacks, F5));   // can capture the blocking piece
    EXPECT_FALSE(test_bit(attacks, G6));  // blocked
    EXPECT_FALSE(test_bit(attacks, H7));  // blocked
}

// ── Rook attacks ────────────────────────────────────────────────────────────

TEST_F(MagicTest, RookE4EmptyBoard) {
    Bitboard attacks = magic::rook_attacks(E4, kEmptyBB);
    // File e (7 squares) + rank 4 (7 squares) = 14
    EXPECT_EQ(popcount(attacks), 14);

    EXPECT_TRUE(test_bit(attacks, E1));
    EXPECT_TRUE(test_bit(attacks, E8));
    EXPECT_TRUE(test_bit(attacks, A4));
    EXPECT_TRUE(test_bit(attacks, H4));
    EXPECT_FALSE(test_bit(attacks, E4));  // not own square
}

TEST_F(MagicTest, RookA1EmptyBoard) {
    Bitboard attacks = magic::rook_attacks(A1, kEmptyBB);
    EXPECT_EQ(popcount(attacks), 14);  // 7 on rank + 7 on file
}

TEST_F(MagicTest, RookBlockedByPiece) {
    // Rook on e4 with pieces on e6 and c4
    Bitboard occ = square_bb(E6) | square_bb(C4);
    Bitboard attacks = magic::rook_attacks(E4, occ);

    EXPECT_TRUE(test_bit(attacks, E5));
    EXPECT_TRUE(test_bit(attacks, E6));   // capture the blocker
    EXPECT_FALSE(test_bit(attacks, E7));  // blocked
    EXPECT_TRUE(test_bit(attacks, D4));
    EXPECT_TRUE(test_bit(attacks, C4));   // capture
    EXPECT_FALSE(test_bit(attacks, B4));  // blocked
    EXPECT_TRUE(test_bit(attacks, H4));   // unblocked direction
}

// ── Queen attacks ───────────────────────────────────────────────────────────

TEST_F(MagicTest, QueenE4EmptyBoard) {
    Bitboard attacks = magic::queen_attacks(E4, kEmptyBB);
    // Bishop (13) + Rook (14) = 27 for e4
    EXPECT_EQ(popcount(attacks), 27);
}

TEST_F(MagicTest, QueenCornerA1) {
    Bitboard attacks = magic::queen_attacks(A1, kEmptyBB);
    // Rook 14 + Bishop 7 = 21
    EXPECT_EQ(popcount(attacks), 21);
}

// ── Symmetry / consistency ──────────────────────────────────────────────────

TEST_F(MagicTest, RookAttacksSymmetric) {
    // Rook attacks from a1 on empty board should include a8 and h1
    Bitboard attacks = magic::rook_attacks(A1, kEmptyBB);
    EXPECT_TRUE(test_bit(attacks, A8));
    EXPECT_TRUE(test_bit(attacks, H1));

    // And rook from h8 should include h1 and a8
    attacks = magic::rook_attacks(H8, kEmptyBB);
    EXPECT_TRUE(test_bit(attacks, H1));
    EXPECT_TRUE(test_bit(attacks, A8));
}

TEST_F(MagicTest, BishopAttacksDontOverlapOwnSquare) {
    for (int sq = 0; sq < 64; ++sq) {
        Bitboard attacks = magic::bishop_attacks(static_cast<Square>(sq), kEmptyBB);
        EXPECT_FALSE(test_bit(attacks, static_cast<Square>(sq)));
    }
}

TEST_F(MagicTest, RookAttacksDontOverlapOwnSquare) {
    for (int sq = 0; sq < 64; ++sq) {
        Bitboard attacks = magic::rook_attacks(static_cast<Square>(sq), kEmptyBB);
        EXPECT_FALSE(test_bit(attacks, static_cast<Square>(sq)));
    }
}
