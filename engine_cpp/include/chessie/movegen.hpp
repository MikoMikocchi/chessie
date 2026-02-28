#pragma once

/// @file movegen.hpp
/// Legal and pseudo-legal move generation + perft.
///
/// All functions require magic::init() to have been called first.

#include <chessie/position.hpp>

#include <cstdint>

namespace chessie::movegen {

/// Generate all pseudo-legal moves for the current side to move.
[[nodiscard]] MoveList pseudo_legal(const Position& pos);

/// Generate all strictly legal moves (uses internal make/unmake).
[[nodiscard]] MoveList legal(Position& pos);

/// Generate capture moves + all promotions (for quiescence search).
[[nodiscard]] MoveList captures(const Position& pos);

/// Count leaf nodes at `depth` plies (perft for validation).
[[nodiscard]] std::uint64_t perft(Position& pos, int depth);

}  // namespace chessie::movegen
