/// @file test_perft.cpp
/// Perft validation of the move generator against known node counts.
///
/// These are the gold-standard tests: if perft matches published values,
/// make_move / unmake_move / legal move generation are correct.

#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>
#include <chessie/position.hpp>

#include <gtest/gtest.h>

using namespace chessie;

class PerftTest : public ::testing::Test {
   public:
    static void SetUpTestSuite() { magic::init(); }
};

// ── Starting position ───────────────────────────────────────────────────────
// rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

TEST_F(PerftTest, StartingDepth1) {
    auto pos = Position::initial();
    EXPECT_EQ(movegen::perft(pos, 1), 20ULL);
}

TEST_F(PerftTest, StartingDepth2) {
    auto pos = Position::initial();
    EXPECT_EQ(movegen::perft(pos, 2), 400ULL);
}

TEST_F(PerftTest, StartingDepth3) {
    auto pos = Position::initial();
    EXPECT_EQ(movegen::perft(pos, 3), 8902ULL);
}

TEST_F(PerftTest, StartingDepth4) {
    auto pos = Position::initial();
    EXPECT_EQ(movegen::perft(pos, 4), 197281ULL);
}

TEST_F(PerftTest, StartingDepth5) {
    auto pos = Position::initial();
    EXPECT_EQ(movegen::perft(pos, 5), 4865609ULL);
}

// ── Kiwipete ────────────────────────────────────────────────────────────────
// r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -

static constexpr const char* kKiwipete =
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";

TEST_F(PerftTest, KiwipeteDepth1) {
    auto pos = Position::from_fen(kKiwipete);
    EXPECT_EQ(movegen::perft(pos, 1), 48ULL);
}

TEST_F(PerftTest, KiwipeteDepth2) {
    auto pos = Position::from_fen(kKiwipete);
    EXPECT_EQ(movegen::perft(pos, 2), 2039ULL);
}

TEST_F(PerftTest, KiwipeteDepth3) {
    auto pos = Position::from_fen(kKiwipete);
    EXPECT_EQ(movegen::perft(pos, 3), 97862ULL);
}

TEST_F(PerftTest, KiwipeteDepth4) {
    auto pos = Position::from_fen(kKiwipete);
    EXPECT_EQ(movegen::perft(pos, 4), 4085603ULL);
}

// ── Position 3 ──────────────────────────────────────────────────────────────
// 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -

static constexpr const char* kPosition3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1";

TEST_F(PerftTest, Position3Depth1) {
    auto pos = Position::from_fen(kPosition3);
    EXPECT_EQ(movegen::perft(pos, 1), 14ULL);
}

TEST_F(PerftTest, Position3Depth2) {
    auto pos = Position::from_fen(kPosition3);
    EXPECT_EQ(movegen::perft(pos, 2), 191ULL);
}

TEST_F(PerftTest, Position3Depth3) {
    auto pos = Position::from_fen(kPosition3);
    EXPECT_EQ(movegen::perft(pos, 3), 2812ULL);
}

TEST_F(PerftTest, Position3Depth4) {
    auto pos = Position::from_fen(kPosition3);
    EXPECT_EQ(movegen::perft(pos, 4), 43238ULL);
}

TEST_F(PerftTest, Position3Depth5) {
    auto pos = Position::from_fen(kPosition3);
    EXPECT_EQ(movegen::perft(pos, 5), 674624ULL);
}

// ── Position 4 ──────────────────────────────────────────────────────────────
// r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1

static constexpr const char* kPosition4 =
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1";

TEST_F(PerftTest, Position4Depth1) {
    auto pos = Position::from_fen(kPosition4);
    EXPECT_EQ(movegen::perft(pos, 1), 6ULL);
}

TEST_F(PerftTest, Position4Depth2) {
    auto pos = Position::from_fen(kPosition4);
    EXPECT_EQ(movegen::perft(pos, 2), 264ULL);
}

TEST_F(PerftTest, Position4Depth3) {
    auto pos = Position::from_fen(kPosition4);
    EXPECT_EQ(movegen::perft(pos, 3), 9467ULL);
}

TEST_F(PerftTest, Position4Depth4) {
    auto pos = Position::from_fen(kPosition4);
    EXPECT_EQ(movegen::perft(pos, 4), 422333ULL);
}

// ── Position 5 ──────────────────────────────────────────────────────────────
// rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8

static constexpr const char* kPosition5 =
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8";

TEST_F(PerftTest, Position5Depth1) {
    auto pos = Position::from_fen(kPosition5);
    EXPECT_EQ(movegen::perft(pos, 1), 44ULL);
}

TEST_F(PerftTest, Position5Depth2) {
    auto pos = Position::from_fen(kPosition5);
    EXPECT_EQ(movegen::perft(pos, 2), 1486ULL);
}

TEST_F(PerftTest, Position5Depth3) {
    auto pos = Position::from_fen(kPosition5);
    EXPECT_EQ(movegen::perft(pos, 3), 62379ULL);
}

TEST_F(PerftTest, Position5Depth4) {
    auto pos = Position::from_fen(kPosition5);
    EXPECT_EQ(movegen::perft(pos, 4), 2103487ULL);
}

// ── Position 6 ──────────────────────────────────────────────────────────────
// r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/3P1N1P/PPP1NPP1/R2Q1RK1 w - - 0 10

static constexpr const char* kPosition6 =
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/3P1N1P/PPP1NPP1/R2Q1RK1 w - - 0 10";

TEST_F(PerftTest, Position6Depth1) {
    auto pos = Position::from_fen(kPosition6);
    EXPECT_EQ(movegen::perft(pos, 1), 42ULL);
}

TEST_F(PerftTest, Position6Depth2) {
    auto pos = Position::from_fen(kPosition6);
    EXPECT_EQ(movegen::perft(pos, 2), 1892ULL);
}

TEST_F(PerftTest, Position6Depth3) {
    auto pos = Position::from_fen(kPosition6);
    EXPECT_EQ(movegen::perft(pos, 3), 76031ULL);
}

TEST_F(PerftTest, Position6Depth4) {
    auto pos = Position::from_fen(kPosition6);
    EXPECT_EQ(movegen::perft(pos, 4), 3288373ULL);
}
