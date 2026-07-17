#pragma once

/// @file zobrist.hpp
/// Zobrist hashing keys for incremental position hashing.
/// Uses the same seed and splitmix64 algorithm as the Python version
/// for full key compatibility.

#include <chessie/types.hpp>

#include <cstdint>

namespace chessie::zobrist {

// ── splitmix64 key generator (matches Python's _splitmix64) ─────────────────

inline constexpr std::uint64_t kSeed = 0xA5B3C7D9E1F23412ULL;
inline constexpr std::uint64_t kMask64 = 0xFFFFFFFFFFFFFFFFULL;

[[nodiscard]] constexpr std::uint64_t splitmix64(std::uint64_t state) noexcept {
    std::uint64_t z = (state + 0x9E3779B97F4A7C15ULL) & kMask64;
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL) & kMask64;
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EBULL) & kMask64;
    return z ^ (z >> 31);
}

[[nodiscard]] constexpr std::uint64_t nth_key(int index) noexcept {
    return splitmix64(kSeed + static_cast<std::uint64_t>(index));
}

// ── Pre-computed key tables ─────────────────────────────────────────────────

namespace detail {

struct ZobristKeys {
    // piece_keys[color][piece_type_index][square]
    // piece_type_index: Pawn=0 .. King=5 (same as Python's ptype 0..5)
    std::uint64_t piece_keys[2][6][64]{};
    std::uint64_t side_to_move_key{};
    std::uint64_t castling_keys[16]{};
    std::uint64_t en_passant_keys[64]{};
};

constexpr ZobristKeys compute_keys() noexcept {
    ZobristKeys keys{};

    // Piece keys: index = (color * 384) + (ptype * 64) + sq
    for (int color = 0; color < 2; ++color) {
        for (int ptype = 0; ptype < 6; ++ptype) {
            for (int sq = 0; sq < 64; ++sq) {
                keys.piece_keys[color][ptype][sq] = nth_key(color * 384 + ptype * 64 + sq);
            }
        }
    }

    // Side to move key: index = 2 * 6 * 64 = 768
    keys.side_to_move_key = nth_key(2 * 6 * 64);

    // Castling keys: index = 769 + idx (0..15)
    for (int idx = 0; idx < 16; ++idx) {
        keys.castling_keys[idx] = nth_key(2 * 6 * 64 + 1 + idx);
    }

    // En passant keys: index = 785 + sq (0..63)
    for (int sq = 0; sq < 64; ++sq) {
        keys.en_passant_keys[sq] = nth_key(2 * 6 * 64 + 1 + 16 + sq);
    }

    return keys;
}

inline constexpr ZobristKeys kKeys = compute_keys();

}  // namespace detail

// ── Public API ──────────────────────────────────────────────────────────────

/// Hash key for a specific piece on a square.
/// @param color  Piece color.
/// @param pt     Piece type (Pawn..King).
/// @param sq     Square index (0-63).
[[nodiscard]] constexpr std::uint64_t piece_key(Color color, PieceType pt, Square sq) noexcept {
    return detail::kKeys.piece_keys[color_index(color)][piece_index(pt)][sq];
}

/// Hash toggle key for side to move.
[[nodiscard]] constexpr std::uint64_t side_to_move_key() noexcept {
    return detail::kKeys.side_to_move_key;
}

/// Hash key for castling rights state.
[[nodiscard]] constexpr std::uint64_t castling_key(CastlingRights cr) noexcept {
    return detail::kKeys.castling_keys[static_cast<int>(cr) & 0xF];
}

/// Hash key for an en passant target square.
[[nodiscard]] constexpr std::uint64_t en_passant_key(Square sq) noexcept {
    return detail::kKeys.en_passant_keys[sq];
}

}  // namespace chessie::zobrist
