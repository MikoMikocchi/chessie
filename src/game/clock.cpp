#include <chessie/game/clock.hpp>

#include <algorithm>

namespace chessie {

Clock::Clock(TimeControl time_control) : time_control_(time_control) {
    remaining_[color_index(Color::White)] = time_control.initial_seconds;
    remaining_[color_index(Color::Black)] = time_control.initial_seconds;
}

void Clock::start(Color color) {
    active_color_ = color;
    last_tick_ = std::chrono::steady_clock::now();
    running_ = true;
}

void Clock::stop() {
    if (running_) {
        consume_elapsed();
        running_ = false;
    }
}

void Clock::switch_side() {
    if (!active_color_.has_value()) {
        return;
    }
    if (running_) {
        consume_elapsed();
    }
    active_color_ = opposite(*active_color_);
    last_tick_ = std::chrono::steady_clock::now();
}

double Clock::remaining(Color color) const {
    const int idx = color_index(color);
    if (running_ && active_color_.has_value() && *active_color_ == color) {
        const auto now = std::chrono::steady_clock::now();
        const double elapsed =
            std::chrono::duration<double>(now - last_tick_).count();
        return std::max(0.0, remaining_[idx] - elapsed);
    }
    return std::max(0.0, remaining_[idx]);
}

bool Clock::is_flag_fallen(Color color) const {
    return remaining(color) <= 0.0;
}

void Clock::add_increment(Color color) {
    remaining_[color_index(color)] += time_control_.increment_seconds;
}

bool Clock::is_unlimited() const noexcept {
    return time_control_.is_unlimited();
}

void Clock::set_remaining(Color color, double seconds) {
    remaining_[color_index(color)] = seconds;
}

ClockSnapshot Clock::snapshot() const {
    return ClockSnapshot{
        remaining(Color::White),
        remaining(Color::Black),
        active_color_,
        running_,
    };
}

void Clock::restore(const ClockSnapshot& snapshot) {
    remaining_[color_index(Color::White)] = snapshot.white_remaining;
    remaining_[color_index(Color::Black)] = snapshot.black_remaining;
    active_color_ = snapshot.active_color;
    running_ = snapshot.is_running && snapshot.active_color.has_value();
    last_tick_ = std::chrono::steady_clock::now();
}

void Clock::consume_elapsed() {
    if (!active_color_.has_value()) {
        return;
    }
    const auto now = std::chrono::steady_clock::now();
    const double elapsed = std::chrono::duration<double>(now - last_tick_).count();
    const int idx = color_index(*active_color_);
    remaining_[idx] = std::max(0.0, remaining_[idx] - elapsed);
    last_tick_ = now;
}

}  // namespace chessie
