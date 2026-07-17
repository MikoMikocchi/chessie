/// @file test_search.cpp
/// Tests for the search engine.

#include <chessie/engine.hpp>
#include <chessie/magic.hpp>
#include <chessie/search.hpp>

#include <chrono>
#include <gtest/gtest.h>
#include <string_view>
#include <thread>

namespace chessie {
namespace {

// ── Test fixture ────────────────────────────────────────────────────────────

class SearchTest : public ::testing::Test {
   protected:
    static void SetUpTestSuite() { magic::init(); }

    // Helper: run search at given depth with small TT
    SearchResult run(std::string_view fen, int depth, int time_ms = -1) {
        Position pos = Position::from_fen(fen);
        Engine engine(1);  // 1 MB TT
        SearchLimits limits;
        limits.max_depth = depth;
        limits.time_limit_ms = time_ms;
        return engine.search(pos, limits);
    }

    // Helper: check if a move is in the legal move list
    bool is_legal(std::string_view fen, Move m) {
        Position pos = Position::from_fen(fen);
        MoveList moves = movegen::legal(pos);
        for (int i = 0; i < moves.size(); ++i) {
            if (moves[i] == m)
                return true;
        }
        return false;
    }
};

// ── Basic functionality ─────────────────────────────────────────────────────

TEST_F(SearchTest, ReturnsLegalMoveFromStartPosition) {
    auto result = run(kStartingFen, 3);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_TRUE(is_legal(kStartingFen, result.best_move));
    EXPECT_GT(result.depth, 0);
    EXPECT_GT(result.nodes, 0U);
}

TEST_F(SearchTest, DepthOneReturnsMove) {
    auto result = run(kStartingFen, 1);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_EQ(result.depth, 1);
}

TEST_F(SearchTest, DepthTwoReturnsMove) {
    auto result = run(kStartingFen, 2);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_EQ(result.depth, 2);
}

// ── Mate in 1 ───────────────────────────────────────────────────────────────

TEST_F(SearchTest, FindsMateInOneWhite) {
    // White: Kb6, Qb1; Black: Ka8.
    // Qb8# is mate (king trapped by Kb6 covering a7, b7; Qb8 delivers check on a8).
    auto result = run("k7/8/1K6/8/8/8/8/1Q6 w - - 0 1", 2);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_GT(result.score_cp, kMateScore - 20);
}

TEST_F(SearchTest, FindsMateInOneBlack) {
    // Mirror: Black: Kb3, Qb8; White: Ka1.
    // Qb1# is mate.
    auto result = run("1q6/8/8/8/8/1k6/8/K7 b - - 0 1", 2);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_GT(result.score_cp, kMateScore - 20);
}

TEST_F(SearchTest, FindsBackRankMate) {
    // White Rook on a1, Black king on h8 with pawns on f7, g7, h7.
    // Ra8# is mate (rook covers entire 8th rank, pawns block king).
    auto result = run("7k/5ppp/8/8/8/8/8/R3K3 w - - 0 1", 3);
    EXPECT_FALSE(result.best_move.is_null());
    Move ra8 = Move::from_uci("a1a8");
    EXPECT_EQ(result.best_move, ra8);
    EXPECT_GT(result.score_cp, kMateScore - 20);
}

// ── Mate in 2 ───────────────────────────────────────────────────────────────

TEST_F(SearchTest, FindsMateInTwo) {
    // White Ke1, Qe2, Rd1; Black Kg8 alone.
    // Many forced mates (e.g. Qe8+/Rd8+). Depth 4 should find it.
    auto result = run("6k1/8/8/8/8/8/4Q3/3RK3 w - - 0 1", 4);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_GT(result.score_cp, kMateScore - 20);
}

// ── Stalemate ───────────────────────────────────────────────────────────────

TEST_F(SearchTest, ReturnsNullOnStalemate) {
    // Black is stalemated (not in check, no legal moves).
    // Ka8 blocked by Qc7 and Kb6.
    auto result = run("k7/2Q5/1K6/8/8/8/8/8 b - - 0 1", 1);
    EXPECT_TRUE(result.best_move.is_null());
    EXPECT_EQ(result.score_cp, 0);
}

TEST_F(SearchTest, ReturnsNullOnCheckmate) {
    // Black king d8, White queen d7 (check!), White king d6.
    // All escape squares covered. This IS checkmate.
    auto result = run("3k4/3Q4/3K4/8/8/8/8/8 b - - 0 1", 1);
    EXPECT_TRUE(result.best_move.is_null());
    EXPECT_LT(result.score_cp, -kMateScore + 20);
}

// ── Cancellation ────────────────────────────────────────────────────────────

TEST_F(SearchTest, CancelStopsSearchViaThread) {
    Position pos = Position::initial();
    Search search(1);
    SearchLimits limits;
    limits.max_depth = 64;  // Very deep — would run forever without cancel

    SearchResult result;
    std::thread t([&]() { result = search.search(pos, limits); });

    // Wait a tiny bit then cancel
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    search.cancel();
    t.join();

    // Should have returned early (unlikely to reach depth 64)
    EXPECT_LT(result.depth, 20);
}

TEST_F(SearchTest, TimeLimitStopsSearch) {
    auto start = std::chrono::steady_clock::now();
    auto result = run(kStartingFen, 64, 100);  // 100ms time limit
    auto elapsed = std::chrono::steady_clock::now() - start;
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count();

    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_GT(result.depth, 0);
    // Should not take unreasonably long
    EXPECT_LT(ms, 2000);
}

// ── Tactical positions ──────────────────────────────────────────────────────

TEST_F(SearchTest, CapturesHangingQueen) {
    // White queen hanging on d5, Black to move with queen on d8.
    auto result = run("3q4/8/8/3Q4/8/8/8/4K2k b - - 0 1", 3);
    EXPECT_FALSE(result.best_move.is_null());
    Move qxd5 = Move::from_uci("d8d5");
    EXPECT_EQ(result.best_move, qxd5);
}

TEST_F(SearchTest, AvoidsBlundering) {
    auto result = run(kStartingFen, 3);
    EXPECT_FALSE(result.best_move.is_null());
    // Score should be approximately equal from the starting position
    EXPECT_GT(result.score_cp, -200);
    EXPECT_LT(result.score_cp, 200);
}

// ── Draw detection ──────────────────────────────────────────────────────────

TEST_F(SearchTest, DrawByInsufficientMaterialKvK) {
    auto result = run("4k3/8/8/8/8/8/8/4K3 w - - 0 1", 3);
    EXPECT_EQ(result.score_cp, 0);
}

TEST_F(SearchTest, DrawBy50MoveRule) {
    auto result = run("4k3/8/8/8/4K3/8/8/R7 w - - 100 50", 2);
    EXPECT_EQ(result.score_cp, 0);
}

// ── Engine facade ───────────────────────────────────────────────────────────

TEST_F(SearchTest, EngineFacadeWorks) {
    Position pos = Position::initial();
    Engine engine(1);
    SearchLimits limits;
    limits.max_depth = 2;
    auto result = engine.search(pos, limits);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_EQ(result.depth, 2);
}

TEST_F(SearchTest, EngineCancelViaThread) {
    Position pos = Position::initial();
    Engine engine(1);
    SearchLimits limits;
    limits.max_depth = 64;

    SearchResult result;
    std::thread t([&]() { result = engine.search(pos, limits); });

    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    engine.cancel();
    t.join();

    EXPECT_LT(result.depth, 20);
}

TEST_F(SearchTest, EngineSetTTSize) {
    Engine engine(1);
    engine.set_tt_size(2);
    engine.clear_tt();

    Position pos = Position::initial();
    SearchLimits limits;
    limits.max_depth = 2;
    auto result = engine.search(pos, limits);
    EXPECT_FALSE(result.best_move.is_null());
}

// ── Higher depth ────────────────────────────────────────────────────────────

TEST_F(SearchTest, DepthFourFromStart) {
    auto result = run(kStartingFen, 4);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_EQ(result.depth, 4);
    EXPECT_GT(result.nodes, 100U);
}

TEST_F(SearchTest, DepthFiveFromStart) {
    auto result = run(kStartingFen, 5);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_EQ(result.depth, 5);
}

// ── Promotion awareness ─────────────────────────────────────────────────────

TEST_F(SearchTest, FindsPromotionWin) {
    // White pawn on e7, Black king on h8, White king on e1.
    // e8=Q should be found.
    auto result = run("7k/4P3/8/8/8/8/8/4K3 w - - 0 1", 3);
    EXPECT_FALSE(result.best_move.is_null());
    EXPECT_EQ(result.best_move.from_sq, E7);
    EXPECT_EQ(result.best_move.to_sq, E8);
    EXPECT_EQ(result.best_move.flag, MoveFlag::Promotion);
}

// ── Null move support ───────────────────────────────────────────────────────

TEST_F(SearchTest, NullMoveRoundTrip) {
    // Verify that make_null_move / unmake_null_move preserves the position.
    Position pos = Position::initial();
    std::string fen_before = pos.to_fen();
    auto key_before = pos.key();

    pos.make_null_move();
    // Side should have flipped
    EXPECT_EQ(pos.side_to_move(), Color::Black);
    // EP should be cleared (was kNoSquare already, but test the mechanism)
    EXPECT_EQ(pos.en_passant(), kNoSquare);

    pos.unmake_null_move();
    EXPECT_EQ(pos.to_fen(), fen_before);
    EXPECT_EQ(pos.key(), key_before);
}

}  // namespace
}  // namespace chessie
