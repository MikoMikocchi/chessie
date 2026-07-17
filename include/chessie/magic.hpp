#pragma once

/// @file magic.hpp
/// Magic bitboard attack generation for sliding pieces (bishop, rook, queen).
///
/// Uses "plain" magic bitboards with pre-computed magic numbers.
/// Call `magic::init()` once at program startup before using attack functions.

#include <chessie/bitboard.hpp>
#include <chessie/types.hpp>

#include <cstdint>

namespace chessie::magic {

/// Initialize magic bitboard tables. Must be called once before any attack lookups.
void init();

/// Bishop attack bitboard for a given square and board occupancy.
[[nodiscard]] Bitboard bishop_attacks(Square sq, Bitboard occupancy) noexcept;

/// Rook attack bitboard for a given square and board occupancy.
[[nodiscard]] Bitboard rook_attacks(Square sq, Bitboard occupancy) noexcept;

/// Queen attack bitboard (union of bishop + rook attacks).
[[nodiscard]] inline Bitboard queen_attacks(Square sq, Bitboard occupancy) noexcept {
    return bishop_attacks(sq, occupancy) | rook_attacks(sq, occupancy);
}

}  // namespace chessie::magic
