#pragma once

/// @file types.hpp
/// Game-layer enumerations and time-control presets.

#include <chessie/types.hpp>

#include <cmath>
#include <limits>
#include <string>

namespace chessie {

enum class GamePhase : std::uint8_t {
    NotStarted = 0,
    AwaitingMove,
    Thinking,
    GameOver,
};

enum class DrawOffer : std::uint8_t {
    None = 0,
    Offered,
    Accepted,
    Declined,
};

enum class GameEndReason : std::uint8_t {
    None = 0,
    Checkmate,
    Stalemate,
    Resign,
    FlagFall,
    DrawAgreed,
    DrawRule,
};

enum class GameResult : std::uint8_t {
    InProgress = 0,
    WhiteWins = 1,
    BlackWins = 2,
    Draw = 3,
};

struct TimeControl {
    double initial_seconds = 0.0;
    double increment_seconds = 0.0;

    TimeControl() = default;
    TimeControl(double initial, double increment = 0.0)
        : initial_seconds(initial), increment_seconds(increment) {}

    [[nodiscard]] bool is_unlimited() const noexcept {
        return std::isinf(initial_seconds);
    }

    static TimeControl bullet_1m() { return {60.0, 0.0}; }
    static TimeControl bullet_2m1s() { return {120.0, 1.0}; }
    static TimeControl blitz_3m() { return {180.0, 0.0}; }
    static TimeControl blitz_3m2s() { return {180.0, 2.0}; }
    static TimeControl blitz_5m() { return {300.0, 0.0}; }
    static TimeControl blitz_5m3s() { return {300.0, 3.0}; }
    static TimeControl rapid_10m() { return {600.0, 0.0}; }
    static TimeControl rapid_15m10s() { return {900.0, 10.0}; }
    static TimeControl classical_30m() { return {1800.0, 0.0}; }
    static TimeControl unlimited() {
        return {std::numeric_limits<double>::infinity(), 0.0};
    }

    [[nodiscard]] std::string repr() const {
        if (is_unlimited()) {
            return "TimeControl(unlimited)";
        }
        const int mins = static_cast<int>(initial_seconds / 60.0);
        if (increment_seconds > 0.0) {
            return "TimeControl(" + std::to_string(mins) + "m+" +
                   std::to_string(static_cast<int>(increment_seconds)) + "s)";
        }
        return "TimeControl(" + std::to_string(mins) + "m)";
    }
};

}  // namespace chessie
