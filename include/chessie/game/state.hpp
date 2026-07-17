#pragma once

/// @file state.hpp
/// Game state machine — tracks phase transitions and move history.

#include <chessie/game/rules.hpp>
#include <chessie/game/types.hpp>
#include <chessie/move.hpp>
#include <chessie/position.hpp>

#include <optional>
#include <string>
#include <vector>

namespace chessie {

struct MoveRecord {
    Move move;
    std::string san;
    std::string fen_after;
    bool was_check = false;
    bool was_capture = false;
};

class GameState {
   public:
    GameState();

    void setup(std::optional<std::string_view> fen = std::nullopt);

    [[nodiscard]] MoveRecord apply_move(Move move);
    [[nodiscard]] std::optional<Move> undo_last_move();

    void resign(Color color);
    void set_draw(GameEndReason reason = GameEndReason::DrawAgreed);
    void flag_fall(Color color);

    [[nodiscard]] bool can_claim_draw_by_rule() const;
    [[nodiscard]] bool claim_draw_by_rule();

    [[nodiscard]] Color side_to_move() const { return position_.side_to_move(); }
    [[nodiscard]] bool is_game_over() const { return phase == GamePhase::GameOver; }
    [[nodiscard]] int ply_count() const {
        return static_cast<int>(move_history.size());
    }
    [[nodiscard]] int fullmove_display() const { return (ply_count() / 2) + 1; }
    [[nodiscard]] MoveList legal_moves();

    [[nodiscard]] const Position& position() const noexcept { return position_; }
    [[nodiscard]] Position& position() noexcept { return position_; }

    GamePhase phase = GamePhase::NotStarted;
    GameResult result = GameResult::InProgress;
    GameEndReason end_reason = GameEndReason::None;
    DrawOffer draw_offer = DrawOffer::None;
    std::optional<Color> draw_offer_by;
    std::vector<MoveRecord> move_history;
    std::string start_fen;

   private:
    void check_game_over();

    Position position_;
};

}  // namespace chessie
