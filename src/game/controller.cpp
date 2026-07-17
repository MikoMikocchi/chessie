#include <chessie/game/controller.hpp>

#include <chessie/movegen.hpp>

#include <algorithm>

namespace chessie {

GameController::GameController() = default;

IPlayer* GameController::current_player() {
    return player(state_.side_to_move());
}

IPlayer* GameController::player(Color color) {
    return players_[color_index(color)];
}

const IPlayer* GameController::player(Color color) const {
    return players_[color_index(color)];
}

void GameController::new_game(IPlayer& white,
                              IPlayer& black,
                              std::optional<TimeControl> time_control,
                              std::optional<std::string_view> fen) {
    players_[color_index(Color::White)] = &white;
    players_[color_index(Color::Black)] = &black;

    if (time_control.has_value()) {
        clock_ = std::make_unique<Clock>(*time_control);
    } else {
        clock_.reset();
    }
    clock_history_.clear();

    state_ = GameState();
    state_.setup(fen);

    emit_phase(GamePhase::AwaitingMove);
    prompt_current_player();
}

bool GameController::submit_move(Move move) {
    if (state_.is_game_over()) {
        return false;
    }
    if (state_.phase != GamePhase::AwaitingMove && state_.phase != GamePhase::Thinking) {
        return false;
    }

    const MoveList legal = movegen::legal(state_.position());
    if (!std::any_of(legal.begin(), legal.end(), [&](const Move& m) { return m == move; })) {
        return false;
    }

    std::optional<ClockSnapshot> clock_snapshot;
    if (clock_) {
        const Color color = state_.side_to_move();
        clock_snapshot = clock_->snapshot();
        clock_->stop();
        if (clock_->is_flag_fallen(color)) {
            state_.flag_fall(color);
            emit_game_over(state_.result);
            return false;
        }
        clock_->add_increment(color);
    }

    const MoveRecord record = state_.apply_move(move);
    if (clock_snapshot.has_value()) {
        clock_history_.push_back(*clock_snapshot);
    }

    emit_move(move, record.san);

    if (state_.is_game_over()) {
        emit_game_over(state_.result);
        return true;
    }

    if (clock_) {
        clock_->switch_side();
    }

    prompt_current_player();
    return true;
}

void GameController::resign(Color color) {
    if (state_.is_game_over()) {
        return;
    }
    if (clock_) {
        clock_->stop();
    }
    state_.resign(color);
    emit_game_over(state_.result);
}

void GameController::offer_draw(Color color) {
    if (state_.is_game_over()) {
        return;
    }
    if (state_.draw_offer == DrawOffer::Offered) {
        return;
    }
    state_.draw_offer = DrawOffer::Offered;
    state_.draw_offer_by = color;
}

void GameController::accept_draw(Color color) {
    if (state_.draw_offer != DrawOffer::Offered) {
        return;
    }
    if (!state_.draw_offer_by.has_value() || *state_.draw_offer_by == color) {
        return;
    }
    if (clock_) {
        clock_->stop();
    }
    state_.draw_offer = DrawOffer::Accepted;
    state_.draw_offer_by.reset();
    state_.set_draw(GameEndReason::DrawAgreed);
    emit_game_over(GameResult::Draw);
}

void GameController::decline_draw() {
    state_.draw_offer = DrawOffer::Declined;
    state_.draw_offer_by.reset();
}

bool GameController::claim_draw(Color color) {
    if (state_.is_game_over()) {
        return false;
    }
    if (color != state_.side_to_move()) {
        return false;
    }
    if (clock_) {
        clock_->stop();
    }
    if (!state_.claim_draw_by_rule()) {
        if (clock_) {
            if (IPlayer* cp = current_player(); cp != nullptr && !clock_->is_running()) {
                clock_->start(cp->color());
            }
        }
        return false;
    }
    emit_game_over(GameResult::Draw);
    return true;
}

bool GameController::undo_move() {
    if (state_.is_game_over() || state_.move_history.empty()) {
        return false;
    }

    if (IPlayer* cp = current_player(); cp != nullptr && !cp->is_human()) {
        cp->cancel();
    }

    (void)state_.undo_last_move();
    if (clock_) {
        clock_->stop();
        if (!clock_history_.empty()) {
            clock_->restore(clock_history_.back());
            clock_history_.pop_back();
        }
    }
    emit_phase(GamePhase::AwaitingMove);
    prompt_current_player();
    return true;
}

void GameController::prompt_current_player() {
    IPlayer* cp = current_player();
    if (cp == nullptr) {
        return;
    }

    if (cp->is_human()) {
        state_.phase = GamePhase::AwaitingMove;
        emit_phase(GamePhase::AwaitingMove);
        if (clock_ && !clock_->is_running()) {
            clock_->start(cp->color());
        }
    } else {
        state_.phase = GamePhase::Thinking;
        emit_phase(GamePhase::Thinking);
        if (clock_ && !clock_->is_running()) {
            clock_->start(cp->color());
        }
        cp->request_move(state_.position());
    }
}

void GameController::emit_move(Move move, const std::string& san) {
    for (const MoveCallback& cb : events.on_move) {
        if (cb) {
            cb(move, san, state_);
        }
    }
}

void GameController::emit_game_over(GameResult result) {
    emit_phase(GamePhase::GameOver);
    for (const GameOverCallback& cb : events.on_game_over) {
        if (cb) {
            cb(result);
        }
    }
}

void GameController::emit_phase(GamePhase phase) {
    for (const PhaseCallback& cb : events.on_phase_changed) {
        if (cb) {
            cb(phase);
        }
    }
}

}  // namespace chessie
