#pragma once

/// @file clock.hpp
/// Dual chess clock with Fischer increment (monotonic, no Qt).

#include <chessie/game/types.hpp>

#include <chrono>
#include <optional>

namespace chessie {

struct ClockSnapshot {
    double white_remaining = 0.0;
    double black_remaining = 0.0;
    std::optional<Color> active_color;
    bool is_running = false;
};

class Clock {
   public:
    explicit Clock(TimeControl time_control);

    void start(Color color);
    void stop();
    void switch_side();

    [[nodiscard]] double remaining(Color color) const;
    [[nodiscard]] bool is_flag_fallen(Color color) const;
    void add_increment(Color color);

    [[nodiscard]] bool is_unlimited() const noexcept;
    [[nodiscard]] bool is_running() const noexcept { return running_; }
    [[nodiscard]] std::optional<Color> active_color() const noexcept { return active_color_; }

    void set_remaining(Color color, double seconds);

    [[nodiscard]] ClockSnapshot snapshot() const;
    void restore(const ClockSnapshot& snapshot);

   private:
    void consume_elapsed();

    TimeControl time_control_;
    double remaining_[2]{};
    std::optional<Color> active_color_;
    std::chrono::steady_clock::time_point last_tick_{};
    bool running_ = false;
};

}  // namespace chessie
