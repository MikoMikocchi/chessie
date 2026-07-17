#pragma once

/// @file pgn.hpp
/// PGN parsing and serialization helpers.

#include <chessie/game/types.hpp>

#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace chessie {

struct PgnMove {
    std::string san;
    std::string comment;
};

struct ParsedPgn {
    std::map<std::string, std::string> headers;
    std::vector<PgnMove> moves;
    std::string result_token;
};

[[nodiscard]] std::string pgn_result_token(GameResult result);
[[nodiscard]] GameResult game_result_from_pgn(std::string_view token);
[[nodiscard]] std::string pgn_movetext_from_sans(const std::vector<std::string>& sans,
                                                  std::string_view result_token);
[[nodiscard]] std::string pgn_movetext_from_moves(const std::vector<PgnMove>& moves,
                                                  std::string_view result_token);
[[nodiscard]] std::string build_pgn(const std::map<std::string, std::string>& headers,
                                    const std::vector<std::string>& sans,
                                    std::string_view result_token,
                                    const std::vector<std::optional<std::string>>* comments =
                                        nullptr);
[[nodiscard]] ParsedPgn parse_pgn_game(std::string_view pgn_text);
[[nodiscard]] std::tuple<std::map<std::string, std::string>, std::vector<std::string>, std::string>
parse_pgn(std::string_view pgn_text);

}  // namespace chessie
