/// @file test_evaluation.cpp
/// Unit tests for the static evaluation function.

#include <chessie/evaluation.hpp>
#include <chessie/magic.hpp>
#include <chessie/position.hpp>

#include <cmath>
#include <gtest/gtest.h>

using namespace chessie;

class EvalTest : public ::testing::Test {
   public:
    static void SetUpTestSuite() { magic::init(); }
};

// ── Starting position ───────────────────────────────────────────────────────

TEST_F(EvalTest, StartingPositionNearZero) {
    auto pos = Position::initial();
    int score = eval::evaluate(pos);
    // Starting position is symmetric — score should be very close to 0.
    EXPECT_NEAR(score, 0, 5);
}

TEST_F(EvalTest, StartingMaterialZero) {
    auto pos = Position::initial();
    int mat = eval::material(pos);
    // Material is perfectly balanced.
    EXPECT_EQ(mat, 0);
}

// ── Material advantage ──────────────────────────────────────────────────────

TEST_F(EvalTest, WhiteQueenAdvantage) {
    // White has an extra queen.
    auto pos = Position::from_fen("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1");
    int score = eval::evaluate(pos);
    EXPECT_GT(score, 800);  // Queen is worth ~1000 cp.
}

TEST_F(EvalTest, BlackQueenAdvantage) {
    // Black has an extra queen.
    auto pos = Position::from_fen("4k3/8/8/3q4/8/8/8/4K3 w - - 0 1");
    int score = eval::evaluate(pos);
    EXPECT_LT(score, -800);  // From white's perspective, negative.
}

TEST_F(EvalTest, BlackToMoveQueenAdvantage) {
    // Black has an extra queen, black to move.
    auto pos = Position::from_fen("4k3/8/8/3q4/8/8/8/4K3 b - - 0 1");
    int score = eval::evaluate(pos);
    // From side-to-move (black) perspective, positive.
    EXPECT_GT(score, 800);
}

TEST_F(EvalTest, ExtraPawnPositive) {
    // White has an extra pawn.
    auto pos = Position::from_fen("4k3/8/8/8/4P3/8/8/4K3 w - - 0 1");
    int score = eval::evaluate(pos);
    EXPECT_GT(score, 50);
}

// ── Symmetry ────────────────────────────────────────────────────────────────

TEST_F(EvalTest, MirroredPositionSymmetric) {
    // Position with white pieces on rank 1-2 vs same black pieces on rank 7-8.
    auto pos_w = Position::from_fen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1");
    auto pos_b = Position::from_fen("4k3/4p3/8/8/8/8/8/4K3 b - - 0 1");
    int score_w = eval::evaluate(pos_w);
    int score_b = eval::evaluate(pos_b);
    // Both should be roughly the same — side-to-move has similar advantage.
    EXPECT_NEAR(score_w, score_b, 10);
}

// ── Tapered eval ────────────────────────────────────────────────────────────

TEST_F(EvalTest, EndgameKingCentralization) {
    // In pure endgame (kings + pawns only), king centralization matters.
    // Central king should score better than corner king for same material.
    auto pos_center = Position::from_fen("8/8/8/3k4/8/8/4P3/4K3 w - - 0 1");
    auto pos_corner = Position::from_fen("k7/8/8/8/8/8/4P3/4K3 w - - 0 1");
    int score_center = eval::evaluate(pos_center);
    int score_corner = eval::evaluate(pos_corner);
    // Both have same material, but PST differs due to black king position.
    // Corner position: black king worse → white scores higher.
    EXPECT_GT(score_corner, score_center);
}

// ── Material function ───────────────────────────────────────────────────────

TEST_F(EvalTest, MaterialCountsCorrectly) {
    // White: K + Q + R. Black: K only.
    auto pos = Position::from_fen("4k3/8/8/8/3Q4/8/4R3/4K3 w - - 0 1");
    int mat = eval::material(pos);
    // Queen + Rook in middlegame values = 1025 + 477 = 1502.
    EXPECT_GT(mat, 1400);
    EXPECT_LT(mat, 1600);
}

TEST_F(EvalTest, EqualMaterialReturnsZero) {
    // Symmetric position with equal material.
    auto pos = Position::from_fen("r3k2r/ppp1pppp/8/8/8/8/PPP1PPPP/R3K2R w KQkq - 0 1");
    int mat = eval::material(pos);
    EXPECT_EQ(mat, 0);
}

// ── Evaluate is always from side-to-move perspective ────────────────────────

TEST_F(EvalTest, FlipSideFlipsSign) {
    // Same board, different side to move — score should negate.
    auto pos_w = Position::from_fen("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1");
    auto pos_b = Position::from_fen("4k3/8/8/8/3Q4/8/8/4K3 b - - 0 1");
    int score_w = eval::evaluate(pos_w);
    int score_b = eval::evaluate(pos_b);
    // score_w is from white's view (positive, has queen).
    // score_b is from black's view (negative, opponent has queen).
    EXPECT_EQ(score_w, -score_b);
}

// ── Piece values sanity ─────────────────────────────────────────────────────

TEST_F(EvalTest, QueenWorthMoreThanRook) {
    auto pos_q = Position::from_fen("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1");
    auto pos_r = Position::from_fen("4k3/8/8/8/3R4/8/8/4K3 w - - 0 1");
    EXPECT_GT(eval::evaluate(pos_q), eval::evaluate(pos_r));
}

TEST_F(EvalTest, RookWorthMoreThanBishop) {
    auto pos_r = Position::from_fen("4k3/8/8/8/3R4/8/8/4K3 w - - 0 1");
    auto pos_b = Position::from_fen("4k3/8/8/8/3B4/8/8/4K3 w - - 0 1");
    EXPECT_GT(eval::evaluate(pos_r), eval::evaluate(pos_b));
}

TEST_F(EvalTest, BishopWorthMoreThanPawn) {
    auto pos_b = Position::from_fen("4k3/8/8/8/3B4/8/8/4K3 w - - 0 1");
    auto pos_p = Position::from_fen("4k3/8/8/8/3P4/8/8/4K3 w - - 0 1");
    EXPECT_GT(eval::evaluate(pos_b), eval::evaluate(pos_p));
}
