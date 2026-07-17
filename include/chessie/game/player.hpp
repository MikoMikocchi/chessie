#pragma once

/// @file player.hpp
/// Human and AI player implementations.

#include <chessie/game/types.hpp>
#include <chessie/position.hpp>

#include <functional>
#include <string>

namespace chessie {

class IPlayer {
   public:
    virtual ~IPlayer() = default;

    [[nodiscard]] virtual Color color() const = 0;
    [[nodiscard]] virtual std::string name() const = 0;
    [[nodiscard]] virtual bool is_human() const = 0;
    virtual void request_move(const Position& position) = 0;
    virtual void cancel() = 0;
};

class HumanPlayer final : public IPlayer {
   public:
    HumanPlayer(Color color, std::string name = "");

    [[nodiscard]] Color color() const override { return color_; }
    [[nodiscard]] std::string name() const override { return name_; }
    [[nodiscard]] bool is_human() const override { return true; }
    void request_move(const Position& position) override;
    void cancel() override;

   private:
    Color color_;
    std::string name_;
};

class AIPlayer final : public IPlayer {
   public:
    using MoveRequestFn = std::function<void(const Position&)>;
    using CancelFn = std::function<void()>;

    AIPlayer(Color color,
             std::string name = "Engine",
             MoveRequestFn on_request_move = nullptr,
             CancelFn on_cancel = nullptr);

    [[nodiscard]] Color color() const override { return color_; }
    [[nodiscard]] std::string name() const override { return name_; }
    [[nodiscard]] bool is_human() const override { return false; }
    void request_move(const Position& position) override;
    void cancel() override;

   private:
    Color color_;
    std::string name_;
    MoveRequestFn on_request_move_;
    CancelFn on_cancel_;
};

}  // namespace chessie
