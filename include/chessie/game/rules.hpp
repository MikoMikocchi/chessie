#pragma once

/// @file rules.hpp
/// High-level chess rules: checkmate, stalemate, draw detection.

#include <chessie/game/types.hpp>
#include <chessie/position.hpp>

namespace chessie {

class Rules {
   public:
    [[nodiscard]] static bool is_in_check(const Position& position);
    [[nodiscard]] static bool is_checkmate(Position& position);
    [[nodiscard]] static bool is_stalemate(Position& position);
    [[nodiscard]] static bool is_insufficient_material(const Position& position);
    [[nodiscard]] static bool is_fifty_move_rule(const Position& position);
    [[nodiscard]] static bool is_seventy_five_move_rule(const Position& position);
    [[nodiscard]] static bool is_threefold_repetition(const Position& position);
    [[nodiscard]] static bool is_fivefold_repetition(const Position& position);
    [[nodiscard]] static bool is_claimable_draw(const Position& position);
    [[nodiscard]] static bool is_automatic_draw(const Position& position);
    [[nodiscard]] static GameResult game_result(Position& position);
};

}  // namespace chessie
