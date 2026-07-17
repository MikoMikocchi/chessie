#pragma once

/// @file bitboard.hpp
/// Bitboard type and manipulation utilities.

#include <chessie/types.hpp>

#include <bit>
#include <cstdint>

namespace chessie {

using Bitboard = std::uint64_t;

inline constexpr Bitboard kEmptyBB = 0ULL;
inline constexpr Bitboard kFullBB = ~0ULL;

// ── Bit manipulation ────────────────────────────────────────────────────────

/// Single bit for a square.
[[nodiscard]] constexpr Bitboard square_bb(Square sq) noexcept {
    return 1ULL << sq;
}

/// Population count (number of set bits).
[[nodiscard]] constexpr int popcount(Bitboard b) noexcept {
    return std::popcount(b);
}

/// Index of the least significant set bit.
[[nodiscard]] constexpr Square lsb(Bitboard b) noexcept {
    return static_cast<Square>(std::countr_zero(b));
}

/// Index of the most significant set bit.
[[nodiscard]] constexpr Square msb(Bitboard b) noexcept {
    return static_cast<Square>(63 - std::countl_zero(b));
}

/// Pop (return and clear) the least significant bit.
[[nodiscard]] constexpr Square pop_lsb(Bitboard& b) noexcept {
    Square sq = lsb(b);
    b &= b - 1;
    return sq;
}

/// Test if a square is set.
[[nodiscard]] constexpr bool test_bit(Bitboard b, Square sq) noexcept {
    return (b >> sq) & 1;
}

/// Set a square bit.
constexpr void set_bit(Bitboard& b, Square sq) noexcept {
    b |= square_bb(sq);
}

/// Clear a square bit.
constexpr void clear_bit(Bitboard& b, Square sq) noexcept {
    b &= ~square_bb(sq);
}

/// Check if the bitboard has more than one bit set.
[[nodiscard]] constexpr bool more_than_one(Bitboard b) noexcept {
    return b & (b - 1);
}

// ── Rank / File masks ───────────────────────────────────────────────────────

// clang-format off
inline constexpr Bitboard kFileA = 0x0101010101010101ULL;
inline constexpr Bitboard kFileB = kFileA << 1;
inline constexpr Bitboard kFileC = kFileA << 2;
inline constexpr Bitboard kFileD = kFileA << 3;
inline constexpr Bitboard kFileE = kFileA << 4;
inline constexpr Bitboard kFileF = kFileA << 5;
inline constexpr Bitboard kFileG = kFileA << 6;
inline constexpr Bitboard kFileH = kFileA << 7;

inline constexpr Bitboard kRank1 = 0x00000000000000FFULL;
inline constexpr Bitboard kRank2 = kRank1 << 8;
inline constexpr Bitboard kRank3 = kRank1 << 16;
inline constexpr Bitboard kRank4 = kRank1 << 24;
inline constexpr Bitboard kRank5 = kRank1 << 32;
inline constexpr Bitboard kRank6 = kRank1 << 40;
inline constexpr Bitboard kRank7 = kRank1 << 48;
inline constexpr Bitboard kRank8 = kRank1 << 56;
// clang-format on

[[nodiscard]] constexpr Bitboard file_bb(int f) noexcept {
    return kFileA << f;
}
[[nodiscard]] constexpr Bitboard rank_bb(int r) noexcept {
    return kRank1 << (r * 8);
}

// ── Shift helpers ───────────────────────────────────────────────────────────

[[nodiscard]] constexpr Bitboard shift_north(Bitboard b) noexcept {
    return b << 8;
}
[[nodiscard]] constexpr Bitboard shift_south(Bitboard b) noexcept {
    return b >> 8;
}
[[nodiscard]] constexpr Bitboard shift_east(Bitboard b) noexcept {
    return (b << 1) & ~kFileA;
}
[[nodiscard]] constexpr Bitboard shift_west(Bitboard b) noexcept {
    return (b >> 1) & ~kFileH;
}
[[nodiscard]] constexpr Bitboard shift_ne(Bitboard b) noexcept {
    return (b << 9) & ~kFileA;
}
[[nodiscard]] constexpr Bitboard shift_nw(Bitboard b) noexcept {
    return (b << 7) & ~kFileH;
}
[[nodiscard]] constexpr Bitboard shift_se(Bitboard b) noexcept {
    return (b >> 7) & ~kFileA;
}
[[nodiscard]] constexpr Bitboard shift_sw(Bitboard b) noexcept {
    return (b >> 9) & ~kFileH;
}

// ── Pre-computed attack tables for non-sliding pieces ───────────────────────

namespace detail {

constexpr auto compute_knight_attacks() noexcept {
    struct Result {
        Bitboard table[64]{};
    };
    Result r{};
    for (int sq = 0; sq < 64; ++sq) {
        Bitboard bb = square_bb(static_cast<Square>(sq));
        Bitboard attacks = kEmptyBB;
        attacks |= (bb << 17) & ~kFileA;             // NNE
        attacks |= (bb << 15) & ~kFileH;             // NNW
        attacks |= (bb << 10) & ~(kFileA | kFileB);  // NEE
        attacks |= (bb << 6) & ~(kFileG | kFileH);   // NWW
        attacks |= (bb >> 6) & ~(kFileA | kFileB);   // SEE
        attacks |= (bb >> 10) & ~(kFileG | kFileH);  // SWW
        attacks |= (bb >> 15) & ~kFileA;             // SSE
        attacks |= (bb >> 17) & ~kFileH;             // SSW
        r.table[sq] = attacks;
    }
    return r;
}

constexpr auto compute_king_attacks() noexcept {
    struct Result {
        Bitboard table[64]{};
    };
    Result r{};
    for (int sq = 0; sq < 64; ++sq) {
        Bitboard bb = square_bb(static_cast<Square>(sq));
        Bitboard attacks = kEmptyBB;
        attacks |= shift_north(bb);
        attacks |= shift_south(bb);
        attacks |= shift_east(bb);
        attacks |= shift_west(bb);
        attacks |= shift_ne(bb);
        attacks |= shift_nw(bb);
        attacks |= shift_se(bb);
        attacks |= shift_sw(bb);
        r.table[sq] = attacks;
    }
    return r;
}

constexpr auto compute_pawn_attacks() noexcept {
    struct Result {
        Bitboard table[2][64]{};
    };
    Result r{};
    for (int sq = 0; sq < 64; ++sq) {
        Bitboard bb = square_bb(static_cast<Square>(sq));
        // White pawn attacks: NE, NW
        r.table[0][sq] = shift_ne(bb) | shift_nw(bb);
        // Black pawn attacks: SE, SW
        r.table[1][sq] = shift_se(bb) | shift_sw(bb);
    }
    return r;
}

inline constexpr auto kKnightAttacksData = compute_knight_attacks();
inline constexpr auto kKingAttacksData = compute_king_attacks();
inline constexpr auto kPawnAttacksData = compute_pawn_attacks();

}  // namespace detail

/// Knight attack bitboard for a given square.
[[nodiscard]] constexpr Bitboard knight_attacks(Square sq) noexcept {
    return detail::kKnightAttacksData.table[sq];
}

/// King attack bitboard for a given square.
[[nodiscard]] constexpr Bitboard king_attacks(Square sq) noexcept {
    return detail::kKingAttacksData.table[sq];
}

/// Pawn attack bitboard for a given square and color.
[[nodiscard]] constexpr Bitboard pawn_attacks(Color c, Square sq) noexcept {
    return detail::kPawnAttacksData.table[color_index(c)][sq];
}

}  // namespace chessie
