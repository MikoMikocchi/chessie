#pragma once

/// @file controller.hpp
/// GameController — central orchestrator of a chess game.

#include <chessie/game/clock.hpp>
#include <chessie/game/player.hpp>
#include <chessie/game/state.hpp>
#include <chessie/game/types.hpp>
#include <chessie/move.hpp>

#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace chessie {

using MoveCallback = std::function<void(Move, const std::string&, const GameState&)>;
using GameOverCallback = std::function<void(GameResult)>;
using PhaseCallback = std::function<void(GamePhase)>;

struct GameEvents {
    std::vector<MoveCallback> on_move;
    std::vector<GameOverCallback> on_game_over;
    std::vector<PhaseCallback> on_phase_changed;
};

class GameController {
   public:
    GameController();

    [[nodiscard]] GameState& state() noexcept { return state_; }
    [[nodiscard]] const GameState& state() const noexcept { return state_; }
    [[nodiscard]] Clock* clock() noexcept { return clock_.get(); }
    [[nodiscard]] const Clock* clock() const noexcept { return clock_.get(); }
    [[nodiscard]] IPlayer* current_player();
    [[nodiscard]] IPlayer* player(Color color);
    [[nodiscard]] const IPlayer* player(Color color) const;

    GameEvents events;

    void new_game(IPlayer& white,
                  IPlayer& black,
                  std::optional<TimeControl> time_control = std::nullopt,
                  std::optional<std::string_view> fen = std::nullopt);

    [[nodiscard]] bool submit_move(Move move);
    void resign(Color color);
    void offer_draw(Color color);
    void accept_draw(Color color);
    void decline_draw();
    [[nodiscard]] bool claim_draw(Color color);
    [[nodiscard]] bool undo_move();

   private:
    void prompt_current_player();
    void emit_move(Move move, const std::string& san);
    void emit_game_over(GameResult result);
    void emit_phase(GamePhase phase);

    GameState state_;
    std::array<IPlayer*, 2> players_{nullptr, nullptr};
    std::unique_ptr<Clock> clock_;
    std::vector<ClockSnapshot> clock_history_;
};

}  // namespace chessie
