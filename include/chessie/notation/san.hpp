#pragma once

/// @file san.hpp
/// SAN (Standard Algebraic Notation) conversion and parsing.

#include <chessie/move.hpp>
#include <chessie/position.hpp>

#include <string>
#include <string_view>

namespace chessie {

[[nodiscard]] std::string move_to_san(Position& position, Move move);
[[nodiscard]] Move parse_san(Position& position, std::string_view san);

}  // namespace chessie
