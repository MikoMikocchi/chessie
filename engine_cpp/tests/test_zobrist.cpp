#include <chessie/zobrist.hpp>

#include <gtest/gtest.h>
#include <set>

using namespace chessie;

// ── Basic key properties ────────────────────────────────────────────────────

TEST(Zobrist, PieceKeysNonZero) {
    // Every piece key should be non-zero
    for (int c = 0; c < 2; ++c) {
        for (int pt = 0; pt < 6; ++pt) {
            for (int sq = 0; sq < 64; ++sq) {
                auto key = zobrist::piece_key(static_cast<Color>(c), static_cast<PieceType>(pt + 1),
                                              static_cast<Square>(sq));
                EXPECT_NE(key, 0ULL) << "color=" << c << " pt=" << pt + 1 << " sq=" << sq;
            }
        }
    }
}

TEST(Zobrist, SideKeyNonZero) {
    EXPECT_NE(zobrist::side_to_move_key(), 0ULL);
}

TEST(Zobrist, CastlingKeysNonZeroExceptIndex0) {
    // Index 0 (no castling rights) is fine to be anything, but 1..15 should be non-zero
    for (int i = 1; i < 16; ++i) {
        EXPECT_NE(zobrist::castling_key(static_cast<CastlingRights>(i)), 0ULL) << "i=" << i;
    }
}

TEST(Zobrist, EnPassantKeysNonZero) {
    for (int sq = 0; sq < 64; ++sq) {
        EXPECT_NE(zobrist::en_passant_key(static_cast<Square>(sq)), 0ULL) << "sq=" << sq;
    }
}

// ── Uniqueness checks ──────────────────────────────────────────────────────

TEST(Zobrist, PieceKeysUnique) {
    std::set<std::uint64_t> keys;
    for (int c = 0; c < 2; ++c) {
        for (int pt = 0; pt < 6; ++pt) {
            for (int sq = 0; sq < 64; ++sq) {
                auto key = zobrist::piece_key(static_cast<Color>(c), static_cast<PieceType>(pt + 1),
                                              static_cast<Square>(sq));
                auto [_, inserted] = keys.insert(key);
                EXPECT_TRUE(inserted)
                    << "Duplicate piece key at c=" << c << " pt=" << pt + 1 << " sq=" << sq;
            }
        }
    }
    EXPECT_EQ(keys.size(), 768U);  // 2 * 6 * 64
}

TEST(Zobrist, CastlingKeysUnique) {
    std::set<std::uint64_t> keys;
    for (int i = 0; i < 16; ++i) {
        keys.insert(zobrist::castling_key(static_cast<CastlingRights>(i)));
    }
    EXPECT_EQ(keys.size(), 16U);
}

TEST(Zobrist, EnPassantKeysUnique) {
    std::set<std::uint64_t> keys;
    for (int sq = 0; sq < 64; ++sq) {
        keys.insert(zobrist::en_passant_key(static_cast<Square>(sq)));
    }
    EXPECT_EQ(keys.size(), 64U);
}

// ── Deterministic ───────────────────────────────────────────────────────────

TEST(Zobrist, Deterministic) {
    // Same arguments must always produce the same key (constexpr keys)
    auto k1 = zobrist::piece_key(Color::White, PieceType::Pawn, static_cast<Square>(0));
    auto k2 = zobrist::piece_key(Color::White, PieceType::Pawn, static_cast<Square>(0));
    EXPECT_EQ(k1, k2);
}

// ── Compatible with Python seed ─────────────────────────────────────────────
// Verify the very first piece key matches what Python's zobrist.py produces
// with seed 0xA5B3C7D9E1F23412 and splitmix64.
// Python: ZobristKeys._generate(seed) -> keys[0] is for piece_keys[0][0][0]
//         = splitmix64(0xA5B3C7D9E1F23412) -> state becomes 0xA5B3C7D9E1F23412 + 0x9E3779B97F4A7C15
//         then the returned value goes through splitmix64 computation.

TEST(Zobrist, MatchesPythonSeedFirstKey) {
    // We compute what Python's splitmix64 would give for the first generated value.
    // state = seed = 0xA5B3C7D9E1F23412
    // state += 0x9E3779B97F4A7C15  => state = 0x43EB4193613CB027
    // z = state
    // z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
    // z = (z ^ (z >> 27)) * 0x94D049BB133111EB
    // z = z ^ (z >> 31)

    constexpr std::uint64_t seed = 0xA5B3C7D9E1F23412ULL;
    constexpr std::uint64_t golden = 0x9E3779B97F4A7C15ULL;
    std::uint64_t state = seed + golden;

    auto smix = [](std::uint64_t z) -> std::uint64_t {
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    };

    std::uint64_t expected_first = smix(state);

    // In our indexing: piece_key(White, Pawn, A1) should be the first generated key
    // Because Python generates keys in flat order: color=0..1, ptype=0..5, sq=0..63
    // and our index is (color * 384 + ptype_idx * 64 + sq) where ptype_idx starts at 0 for Pawn
    auto actual = zobrist::piece_key(Color::White, PieceType::Pawn, static_cast<Square>(0));
    EXPECT_EQ(actual, expected_first);
}
