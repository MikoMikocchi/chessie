/// @file test_tt.cpp
/// Tests for the transposition table.

#include <chessie/tt.hpp>

#include <cstdint>
#include <gtest/gtest.h>

namespace chessie {
namespace {

// ── Construction & Sizing ───────────────────────────────────────────────────

TEST(TTTest, DefaultConstruction) {
    TranspositionTable tt(1);  // 1 MB
    // 1 MB / 16 bytes per entry = 65536 entries (already power of 2)
    EXPECT_EQ(tt.entry_count(), 65536U);
    EXPECT_EQ(tt.age(), 0);
}

TEST(TTTest, EntryCountIsPowerOfTwo) {
    TranspositionTable tt(3);  // 3 MB = 196608 entries raw, rounded to 131072
    auto count = tt.entry_count();
    EXPECT_GT(count, 0U);
    EXPECT_EQ(count & (count - 1), 0U);  // power of 2
}

TEST(TTTest, ResizeClearsTable) {
    TranspositionTable tt(1);
    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    tt.store(0x1234567890ABCDEF, 5, 100, Bound::Exact, m, 50);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(0x1234567890ABCDEF, entry));

    tt.resize(2);
    EXPECT_FALSE(tt.probe(0x1234567890ABCDEF, entry));
}

// ── Store & Probe ───────────────────────────────────────────────────────────

TEST(TTTest, StoreAndProbeHit) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0xDEADBEEFCAFEBABE;
    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};

    tt.store(key, 5, 150, Bound::Exact, m, 80);

    TTEntry entry{};
    bool hit = tt.probe(key, entry);
    EXPECT_TRUE(hit);
    EXPECT_EQ(entry.score, 150);
    EXPECT_EQ(entry.depth, 5);
    EXPECT_EQ(entry.bound, Bound::Exact);
    EXPECT_EQ(entry.best_move, m);
    EXPECT_EQ(entry.static_eval, 80);
    EXPECT_EQ(entry.age, 0);
}

TEST(TTTest, ProbeMiss) {
    TranspositionTable tt(1);
    TTEntry entry{};
    // Table is empty, any probe should miss
    EXPECT_FALSE(tt.probe(0xAAAABBBBCCCCDDDD, entry));
}

TEST(TTTest, ProbeMissWrongKey) {
    TranspositionTable tt(1);
    const std::uint64_t key1 = 0x1111222233334444;
    const std::uint64_t key2 = 0x5555222233334444;  // Same lower 32, different upper 32

    Move m{D2, D4, MoveFlag::DoublePawn, PieceType::None};
    tt.store(key1, 3, 50, Bound::Lower, m, 30);

    TTEntry entry{};
    // key2 may map to the same index but has different upper 32 bits
    // Whether this misses depends on the index mapping. If same index → miss due to key32 mismatch.
    // If different index → miss due to empty slot.
    EXPECT_FALSE(tt.probe(key2, entry));
}

// ── Overwrite / Replacement ─────────────────────────────────────────────────

TEST(TTTest, DeeperEntryReplacesSameIndex) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0xABCDABCDABCDABCD;
    Move m1{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    Move m2{D2, D4, MoveFlag::DoublePawn, PieceType::None};

    // Store at depth 3
    tt.store(key, 3, 50, Bound::Upper, m1, 30);
    // Store at depth 6 (should replace — deeper)
    tt.store(key, 6, 200, Bound::Exact, m2, 100);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.depth, 6);
    EXPECT_EQ(entry.score, 200);
    EXPECT_EQ(entry.best_move, m2);
}

TEST(TTTest, ShallowerEntryDoesNotReplace) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0x1234123412341234;
    Move m1{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    Move m2{D2, D4, MoveFlag::DoublePawn, PieceType::None};

    // Store deep entry
    tt.store(key, 10, 300, Bound::Exact, m1, 150);
    // Try to store shallow non-exact entry (should NOT replace)
    tt.store(key, 3, 50, Bound::Upper, m2, 30);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.depth, 10);  // original deeper entry preserved
    EXPECT_EQ(entry.score, 300);
}

TEST(TTTest, ExactReplacesNonExactAtSameDepth) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0xFFFFFFFFAAAAAAAA;
    Move m1{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    Move m2{G1, F3, MoveFlag::Normal, PieceType::None};

    // Store upper-bound at depth 5
    tt.store(key, 5, 100, Bound::Upper, m1, 50);
    // Store exact at depth 4 (shallower but exact — should replace)
    tt.store(key, 4, 120, Bound::Exact, m2, 60);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.bound, Bound::Exact);
    EXPECT_EQ(entry.score, 120);
}

// ── Age / new_search() ──────────────────────────────────────────────────────

TEST(TTTest, NewSearchIncrementsAge) {
    TranspositionTable tt(1);
    EXPECT_EQ(tt.age(), 0);
    tt.new_search();
    EXPECT_EQ(tt.age(), 1);
    tt.new_search();
    EXPECT_EQ(tt.age(), 2);
}

TEST(TTTest, StaleEntryReplacedByNewAge) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0xBEEFBEEFBEEFBEEF;
    Move m1{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    Move m2{A2, A3, MoveFlag::Normal, PieceType::None};

    // Store deep entry in age 0
    tt.store(key, 15, 500, Bound::Exact, m1, 250);

    // Advance to new search
    tt.new_search();

    // Store shallow entry in age 1 (should replace because old is stale)
    tt.store(key, 1, 10, Bound::Upper, m2, 5);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.depth, 1);
    EXPECT_EQ(entry.age, 1);
}

TEST(TTTest, ProbeStillFindsOldAgeEntry) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0xCCCCDDDDEEEEFFFF;
    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};

    tt.store(key, 5, 100, Bound::Exact, m, 50);
    tt.new_search();

    // Probe should still find the entry (age doesn't affect probe success)
    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.score, 100);
    EXPECT_EQ(entry.age, 0);  // stored with age 0
}

// ── Clear ───────────────────────────────────────────────────────────────────

TEST(TTTest, ClearRemovesAllEntries) {
    TranspositionTable tt(1);
    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};

    // Store several entries
    for (std::uint64_t i = 0; i < 100; ++i) {
        tt.store(i * 0x1234567890ULL, 3, 50, Bound::Lower, m, 25);
    }

    tt.clear();

    // All probes should miss
    TTEntry entry{};
    for (std::uint64_t i = 0; i < 100; ++i) {
        EXPECT_FALSE(tt.probe(i * 0x1234567890ULL, entry));
    }
    EXPECT_EQ(tt.age(), 0);  // clear resets age
}

// ── hashfull ────────────────────────────────────────────────────────────────

TEST(TTTest, HashfullEmptyTable) {
    TranspositionTable tt(1);
    EXPECT_EQ(tt.hashfull(), 0);
}

TEST(TTTest, HashfullAfterStores) {
    TranspositionTable tt(1);
    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};

    // Store entries at indices 0..499 (first 500 of 1000 sample)
    // The exact indices depend on key-to-index mapping, so just store many entries
    // and check hashfull is reasonable
    for (std::uint64_t i = 0; i < 1000; ++i) {
        tt.store(i, 3, 50, Bound::Lower, m, 25);
    }

    int fill = tt.hashfull();
    // With 1000 stores into 65536 entries, fill ≈ 15 per mille
    // Exact value depends on hash distribution, but should be > 0
    EXPECT_GT(fill, 0);
    EXPECT_LE(fill, 1000);
}

// ── Move preservation ───────────────────────────────────────────────────────

TEST(TTTest, PreserveBestMoveOnSameKeyNullMove) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0x9999888877776666;
    Move good_move{E2, E4, MoveFlag::DoublePawn, PieceType::None};

    // Store entry with a real best move
    tt.store(key, 5, 100, Bound::Exact, good_move, 50);

    // Overwrite with null move (e.g., from a fail-low where no best move was found)
    tt.store(key, 6, 120, Bound::Upper, kNullMove, 60);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    // Score and depth should be updated
    EXPECT_EQ(entry.score, 120);
    EXPECT_EQ(entry.depth, 6);
    // But best_move should be preserved from the previous entry
    EXPECT_EQ(entry.best_move, good_move);
}

// ── Bound types ─────────────────────────────────────────────────────────────

TEST(TTTest, AllBoundTypesStored) {
    TranspositionTable tt(1);
    Move m{G1, F3, MoveFlag::Normal, PieceType::None};

    const Bound bounds[] = {Bound::Exact, Bound::Lower, Bound::Upper};
    for (int i = 0; i < 3; ++i) {
        std::uint64_t key = 0xAAAA000000000000ULL + static_cast<std::uint64_t>(i) * 0x1111ULL;
        tt.store(key, 5, 100 + i * 50, bounds[i], m, 50);

        TTEntry entry{};
        EXPECT_TRUE(tt.probe(key, entry));
        EXPECT_EQ(entry.bound, bounds[i]);
        EXPECT_EQ(entry.score, 100 + i * 50);
    }
}

// ── Negative scores ─────────────────────────────────────────────────────────

TEST(TTTest, NegativeScoreRoundTrip) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0x5555666677778888;
    Move m{E7, E5, MoveFlag::DoublePawn, PieceType::None};

    tt.store(key, 4, -350, Bound::Exact, m, -200);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.score, -350);
    EXPECT_EQ(entry.static_eval, -200);
}

// ── Large scores (mate scores) ──────────────────────────────────────────────

TEST(TTTest, MateScoreRoundTrip) {
    TranspositionTable tt(1);
    const std::uint64_t key = 0x1111222233334444;
    Move m{D1, H7, MoveFlag::Normal, PieceType::None};

    // Typical mate score: 30000 - ply
    int mate_score = 29998;
    tt.store(key, 10, mate_score, Bound::Exact, m, 500);

    TTEntry entry{};
    EXPECT_TRUE(tt.probe(key, entry));
    EXPECT_EQ(entry.score, 29998);
}

}  // namespace
}  // namespace chessie
