/// @file test_bitboard.cpp
/// Tests for bitboard.hpp: bit ops, shifts, attack tables.

#include <chessie/bitboard.hpp>

#include <gtest/gtest.h>

namespace chessie {

// ── Basic bit operations ────────────────────────────────────────────────────

TEST(Bitboard, SquareBB) {
    EXPECT_EQ(square_bb(A1), 1ULL);
    EXPECT_EQ(square_bb(H8), 1ULL << 63);
    EXPECT_EQ(square_bb(E4), 1ULL << 28);
}

TEST(Bitboard, Popcount) {
    EXPECT_EQ(popcount(kEmptyBB), 0);
    EXPECT_EQ(popcount(kFullBB), 64);
    EXPECT_EQ(popcount(square_bb(E4)), 1);
    EXPECT_EQ(popcount(kRank1), 8);
    EXPECT_EQ(popcount(kFileA), 8);
}

TEST(Bitboard, LsbMsb) {
    EXPECT_EQ(lsb(kRank1), A1);
    EXPECT_EQ(msb(kRank1), H1);
    EXPECT_EQ(lsb(square_bb(E4)), E4);
    EXPECT_EQ(msb(square_bb(E4)), E4);
    EXPECT_EQ(lsb(kRank8), A8);
    EXPECT_EQ(msb(kRank8), H8);
}

TEST(Bitboard, PopLsb) {
    Bitboard bb = square_bb(A1) | square_bb(C3) | square_bb(H8);
    Square s1 = pop_lsb(bb);
    EXPECT_EQ(s1, A1);
    EXPECT_EQ(popcount(bb), 2);
    Square s2 = pop_lsb(bb);
    EXPECT_EQ(s2, C3);
    EXPECT_EQ(popcount(bb), 1);
    Square s3 = pop_lsb(bb);
    EXPECT_EQ(s3, H8);
    EXPECT_EQ(bb, kEmptyBB);
}

TEST(Bitboard, TestSetClearBit) {
    Bitboard bb = kEmptyBB;
    EXPECT_FALSE(test_bit(bb, E4));
    set_bit(bb, E4);
    EXPECT_TRUE(test_bit(bb, E4));
    clear_bit(bb, E4);
    EXPECT_FALSE(test_bit(bb, E4));
}

TEST(Bitboard, MoreThanOne) {
    EXPECT_FALSE(more_than_one(kEmptyBB));
    EXPECT_FALSE(more_than_one(square_bb(E4)));
    EXPECT_TRUE(more_than_one(square_bb(E4) | square_bb(D5)));
    EXPECT_TRUE(more_than_one(kRank1));
}

// ── Rank / File masks ───────────────────────────────────────────────────────

TEST(Bitboard, FileMasks) {
    EXPECT_EQ(popcount(kFileA), 8);
    EXPECT_EQ(popcount(kFileH), 8);
    EXPECT_TRUE(test_bit(kFileA, A1));
    EXPECT_TRUE(test_bit(kFileA, A8));
    EXPECT_FALSE(test_bit(kFileA, B1));
    EXPECT_EQ(file_bb(0), kFileA);
    EXPECT_EQ(file_bb(7), kFileH);
}

TEST(Bitboard, RankMasks) {
    EXPECT_EQ(popcount(kRank1), 8);
    EXPECT_TRUE(test_bit(kRank1, A1));
    EXPECT_TRUE(test_bit(kRank1, H1));
    EXPECT_FALSE(test_bit(kRank1, A2));
    EXPECT_EQ(rank_bb(0), kRank1);
    EXPECT_EQ(rank_bb(7), kRank8);
}

// ── Shift operations ────────────────────────────────────────────────────────

TEST(Bitboard, ShiftNorthSouth) {
    Bitboard e4 = square_bb(E4);
    EXPECT_EQ(shift_north(e4), square_bb(E5));
    EXPECT_EQ(shift_south(e4), square_bb(E3));
    // North from rank 8 → off board
    EXPECT_EQ(shift_north(square_bb(E8)), kEmptyBB);
    // South from rank 1 → off board
    EXPECT_EQ(shift_south(square_bb(E1)), kEmptyBB);
}

TEST(Bitboard, ShiftEastWest) {
    Bitboard e4 = square_bb(E4);
    EXPECT_EQ(shift_east(e4), square_bb(F4));
    EXPECT_EQ(shift_west(e4), square_bb(D4));
    // East from H file → off board
    EXPECT_EQ(shift_east(square_bb(H4)), kEmptyBB);
    // West from A file → off board
    EXPECT_EQ(shift_west(square_bb(A4)), kEmptyBB);
}

TEST(Bitboard, ShiftDiagonals) {
    Bitboard e4 = square_bb(E4);
    EXPECT_EQ(shift_ne(e4), square_bb(F5));
    EXPECT_EQ(shift_nw(e4), square_bb(D5));
    EXPECT_EQ(shift_se(e4), square_bb(F3));
    EXPECT_EQ(shift_sw(e4), square_bb(D3));
}

TEST(Bitboard, ShiftEdgeCases) {
    // No wrap-around: a-file pieces shouldn't go to h-file when shifting west
    EXPECT_EQ(shift_west(square_bb(A4)), kEmptyBB);
    EXPECT_EQ(shift_nw(square_bb(A4)), kEmptyBB);
    EXPECT_EQ(shift_sw(square_bb(A4)), kEmptyBB);
    // No wrap-around: h-file pieces shouldn't go to a-file when shifting east
    EXPECT_EQ(shift_east(square_bb(H4)), kEmptyBB);
    EXPECT_EQ(shift_ne(square_bb(H4)), kEmptyBB);
    EXPECT_EQ(shift_se(square_bb(H4)), kEmptyBB);
}

// ── Attack tables ───────────────────────────────────────────────────────────

TEST(Bitboard, KnightAttacksCenter) {
    // Knight on E4 should attack 8 squares
    Bitboard attacks = knight_attacks(E4);
    EXPECT_EQ(popcount(attacks), 8);
    EXPECT_TRUE(test_bit(attacks, D6));
    EXPECT_TRUE(test_bit(attacks, F6));
    EXPECT_TRUE(test_bit(attacks, C5));
    EXPECT_TRUE(test_bit(attacks, G5));
    EXPECT_TRUE(test_bit(attacks, C3));
    EXPECT_TRUE(test_bit(attacks, G3));
    EXPECT_TRUE(test_bit(attacks, D2));
    EXPECT_TRUE(test_bit(attacks, F2));
}

TEST(Bitboard, KnightAttacksCorner) {
    // Knight on A1 attacks only 2 squares
    Bitboard attacks = knight_attacks(A1);
    EXPECT_EQ(popcount(attacks), 2);
    EXPECT_TRUE(test_bit(attacks, B3));
    EXPECT_TRUE(test_bit(attacks, C2));
}

TEST(Bitboard, KingAttacksCenter) {
    Bitboard attacks = king_attacks(E4);
    EXPECT_EQ(popcount(attacks), 8);
    EXPECT_TRUE(test_bit(attacks, D3));
    EXPECT_TRUE(test_bit(attacks, D4));
    EXPECT_TRUE(test_bit(attacks, D5));
    EXPECT_TRUE(test_bit(attacks, E3));
    EXPECT_TRUE(test_bit(attacks, E5));
    EXPECT_TRUE(test_bit(attacks, F3));
    EXPECT_TRUE(test_bit(attacks, F4));
    EXPECT_TRUE(test_bit(attacks, F5));
}

TEST(Bitboard, KingAttacksCorner) {
    Bitboard attacks = king_attacks(A1);
    EXPECT_EQ(popcount(attacks), 3);
    EXPECT_TRUE(test_bit(attacks, A2));
    EXPECT_TRUE(test_bit(attacks, B1));
    EXPECT_TRUE(test_bit(attacks, B2));
}

TEST(Bitboard, PawnAttacksWhite) {
    Bitboard attacks = pawn_attacks(Color::White, E4);
    EXPECT_EQ(popcount(attacks), 2);
    EXPECT_TRUE(test_bit(attacks, D5));
    EXPECT_TRUE(test_bit(attacks, F5));
}

TEST(Bitboard, PawnAttacksBlack) {
    Bitboard attacks = pawn_attacks(Color::Black, E4);
    EXPECT_EQ(popcount(attacks), 2);
    EXPECT_TRUE(test_bit(attacks, D3));
    EXPECT_TRUE(test_bit(attacks, F3));
}

TEST(Bitboard, PawnAttacksEdge) {
    // White pawn on A2: only one attack direction (NE)
    Bitboard attacks = pawn_attacks(Color::White, A2);
    EXPECT_EQ(popcount(attacks), 1);
    EXPECT_TRUE(test_bit(attacks, B3));

    // Black pawn on H7: only one attack direction (SW)
    attacks = pawn_attacks(Color::Black, H7);
    EXPECT_EQ(popcount(attacks), 1);
    EXPECT_TRUE(test_bit(attacks, G6));
}

}  // namespace chessie
