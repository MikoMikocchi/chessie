#pragma once

/// @file evaluation.hpp
/// Static evaluation using Piece-Square Tables with tapered eval.
///
/// Uses PeSTO-style middlegame/endgame PST and material values
/// with game-phase tapering between the two scores.

#include <chessie/position.hpp>

namespace chessie::eval {

/// Evaluate the position from the side-to-move's perspective.
/// Returns centipawns. Positive = side-to-move is better.
[[nodiscard]] int evaluate(const Position& pos);

/// Material-only evaluation (no PST, no tapering). Useful for tests.
[[nodiscard]] int material(const Position& pos);

}  // namespace chessie::eval
