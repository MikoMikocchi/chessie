/// @file test_move.cpp
/// Tests for move.hpp: Move creation, UCI serialization, MoveList.

#include <chessie/move.hpp>

#include <gtest/gtest.h>

namespace chessie {

// ── Move UCI ────────────────────────────────────────────────────────────────

TEST(Move, UciNormal) {
    Move m{E2, E4, MoveFlag::Normal, PieceType::None};
    EXPECT_EQ(m.uci(), "e2e4");
}

TEST(Move, UciPromotion) {
    Move m{E7, E8, MoveFlag::Promotion, PieceType::Queen};
    EXPECT_EQ(m.uci(), "e7e8q");

    Move mk{A7, A8, MoveFlag::Promotion, PieceType::Knight};
    EXPECT_EQ(mk.uci(), "a7a8n");
}

TEST(Move, FromUciNormal) {
    Move m = Move::from_uci("e2e4");
    EXPECT_EQ(m.from_sq, E2);
    EXPECT_EQ(m.to_sq, E4);
    EXPECT_EQ(m.flag, MoveFlag::Normal);
    EXPECT_EQ(m.promotion, PieceType::None);
}

TEST(Move, FromUciPromotion) {
    Move m = Move::from_uci("e7e8q");
    EXPECT_EQ(m.from_sq, E7);
    EXPECT_EQ(m.to_sq, E8);
    EXPECT_EQ(m.flag, MoveFlag::Promotion);
    EXPECT_EQ(m.promotion, PieceType::Queen);
}

TEST(Move, FromUciInvalid) {
    Move m = Move::from_uci("xy");
    EXPECT_TRUE(m.is_null());

    Move m2 = Move::from_uci("");
    EXPECT_TRUE(m2.is_null());
}

TEST(Move, UciRoundTrip) {
    std::string uci_strs[] = {"e2e4", "d7d5", "g1f3", "a7a8q", "b2b1n"};
    for (const auto& s : uci_strs) {
        Move m = Move::from_uci(s);
        EXPECT_EQ(m.uci(), s) << "Round-trip failed for " << s;
    }
}

TEST(Move, Equality) {
    Move a{E2, E4, MoveFlag::Normal, PieceType::None};
    Move b{E2, E4, MoveFlag::Normal, PieceType::None};
    Move c{D2, D4, MoveFlag::Normal, PieceType::None};
    EXPECT_EQ(a, b);
    EXPECT_NE(a, c);
}

TEST(Move, NullMove) {
    EXPECT_TRUE(kNullMove.is_null());
    Move m{E2, E4};
    EXPECT_FALSE(m.is_null());
}

// ── MoveList ────────────────────────────────────────────────────────────────

TEST(MoveList, PushAndSize) {
    MoveList ml;
    EXPECT_TRUE(ml.empty());
    EXPECT_EQ(ml.size(), 0);

    ml.push({E2, E4});
    EXPECT_EQ(ml.size(), 1);
    EXPECT_FALSE(ml.empty());

    ml.push({D2, D4});
    EXPECT_EQ(ml.size(), 2);
}

TEST(MoveList, IndexAccess) {
    MoveList ml;
    ml.push({E2, E4});
    ml.push({D2, D4});

    EXPECT_EQ(ml[0].from_sq, E2);
    EXPECT_EQ(ml[0].to_sq, E4);
    EXPECT_EQ(ml[1].from_sq, D2);
    EXPECT_EQ(ml[1].to_sq, D4);
}

TEST(MoveList, RangeFor) {
    MoveList ml;
    ml.push({E2, E4});
    ml.push({D2, D4});
    ml.push({G1, F3});

    int count = 0;
    for ([[maybe_unused]] const auto& m : ml) {
        ++count;
    }
    EXPECT_EQ(count, 3);
}

TEST(MoveList, Clear) {
    MoveList ml;
    ml.push({E2, E4});
    ml.push({D2, D4});
    EXPECT_EQ(ml.size(), 2);

    ml.clear();
    EXPECT_TRUE(ml.empty());
    EXPECT_EQ(ml.size(), 0);
}

}  // namespace chessie
