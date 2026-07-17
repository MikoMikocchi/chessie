#include <chessie/game/player.hpp>

namespace chessie {

HumanPlayer::HumanPlayer(Color color, std::string name)
    : color_(color), name_(name.empty() ? "Player (" + std::string(color == Color::White ? "White" : "Black") + ")" : std::move(name)) {}

void HumanPlayer::request_move(const Position& /*position*/) {}

void HumanPlayer::cancel() {}

AIPlayer::AIPlayer(Color color,
                   std::string name,
                   MoveRequestFn on_request_move,
                   CancelFn on_cancel)
    : color_(color),
      name_(std::move(name)),
      on_request_move_(std::move(on_request_move)),
      on_cancel_(std::move(on_cancel)) {}

void AIPlayer::request_move(const Position& position) {
    if (on_request_move_) {
        on_request_move_(position);
    }
}

void AIPlayer::cancel() {
    if (on_cancel_) {
        on_cancel_();
    }
}

}  // namespace chessie
