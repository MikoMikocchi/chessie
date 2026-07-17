#include <chessie/notation/pgn.hpp>

#include <cctype>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace chessie {

namespace {

const std::regex kPgnHeaderRe(R"re(^\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]\s*$)re");
const std::regex kMoveNumberRe(R"(^\d+\.(?:\.\.)?$)");

bool is_result_token(std::string_view token) {
    return token == "1-0" || token == "0-1" || token == "1/2-1/2" || token == "*";
}

void append_comment(PgnMove& move, std::string_view comment) {
    std::string clean;
    std::istringstream stream{std::string(comment)};
    std::string word;
    while (stream >> word) {
        if (!clean.empty()) {
            clean += ' ';
        }
        clean += word;
    }
    if (clean.empty()) {
        return;
    }
    if (!move.comment.empty()) {
        move.comment += ' ';
        move.comment += clean;
    } else {
        move.comment = clean;
    }
}

std::pair<std::vector<PgnMove>, std::string> parse_pgn_movetext_mainline(std::string_view movetext) {
    std::vector<PgnMove> moves;
    std::string result_token = "*";
    int variation_depth = 0;
    std::size_t idx = 0;
    const std::size_t total = movetext.size();

    while (idx < total) {
        const char ch = movetext[idx];

        if (std::isspace(static_cast<unsigned char>(ch)) != 0) {
            ++idx;
            continue;
        }

        if (ch == '{') {
            const std::size_t end = movetext.find('}', idx + 1);
            std::string_view comment;
            if (end == std::string_view::npos) {
                comment = movetext.substr(idx + 1);
                idx = total;
            } else {
                comment = movetext.substr(idx + 1, end - idx - 1);
                idx = end + 1;
            }
            if (variation_depth == 0 && !moves.empty()) {
                append_comment(moves.back(), comment);
            }
            continue;
        }

        if (ch == ';') {
            std::size_t end = movetext.find('\n', idx + 1);
            if (end == std::string_view::npos) {
                end = total;
            }
            const std::string_view comment = movetext.substr(idx + 1, end - idx - 1);
            if (variation_depth == 0 && !moves.empty()) {
                append_comment(moves.back(), comment);
            }
            idx = end;
            continue;
        }

        if (ch == '(') {
            ++variation_depth;
            ++idx;
            continue;
        }

        if (ch == ')') {
            variation_depth = std::max(0, variation_depth - 1);
            ++idx;
            continue;
        }

        std::size_t token_end = idx;
        while (token_end < total) {
            const char c = movetext[token_end];
            if (std::isspace(static_cast<unsigned char>(c)) != 0 || c == '{' || c == '}' ||
                c == ';' || c == '(' || c == ')') {
                break;
            }
            ++token_end;
        }

        std::string token(movetext.substr(idx, token_end - idx));
        idx = token_end;

        if (token.empty() || variation_depth > 0) {
            continue;
        }

        if (is_result_token(token)) {
            result_token = token;
            continue;
        }

        if (std::regex_match(token, kMoveNumberRe)) {
            continue;
        }

        if (token.starts_with('$') &&
            std::all_of(token.begin() + 1, token.end(),
                        [](char c) { return std::isdigit(static_cast<unsigned char>(c)) != 0; })) {
            continue;
        }

        if (token.starts_with("...")) {
            token.erase(0, 3);
        }
        while (!token.empty() && token.front() == '.') {
            token.erase(token.begin());
        }
        if (token.empty()) {
            continue;
        }

        moves.push_back(PgnMove{token, ""});
    }

    return {moves, result_token};
}

std::string escape_pgn_header_value(std::string_view value) {
    std::string escaped;
    escaped.reserve(value.size());
    for (const char ch : value) {
        if (ch == '\\') {
            escaped += "\\\\";
        } else if (ch == '"') {
            escaped += "\\\"";
        } else {
            escaped += ch;
        }
    }
    return escaped;
}

std::string unescape_pgn_header_value(std::string_view value) {
    std::string out;
    out.reserve(value.size());
    for (std::size_t i = 0; i < value.size(); ++i) {
        if (value[i] == '\\' && i + 1 < value.size()) {
            out += value[i + 1];
            ++i;
        } else {
            out += value[i];
        }
    }
    return out;
}

}  // namespace

std::string pgn_result_token(GameResult result) {
    switch (result) {
        case GameResult::WhiteWins:
            return "1-0";
        case GameResult::BlackWins:
            return "0-1";
        case GameResult::Draw:
            return "1/2-1/2";
        default:
            return "*";
    }
}

GameResult game_result_from_pgn(std::string_view token) {
    if (token == "1-0") {
        return GameResult::WhiteWins;
    }
    if (token == "0-1") {
        return GameResult::BlackWins;
    }
    if (token == "1/2-1/2") {
        return GameResult::Draw;
    }
    return GameResult::InProgress;
}

std::string pgn_movetext_from_sans(const std::vector<std::string>& sans,
                                   std::string_view result_token) {
    std::vector<PgnMove> moves;
    moves.reserve(sans.size());
    for (const std::string& san : sans) {
        moves.push_back(PgnMove{san, ""});
    }
    return pgn_movetext_from_moves(moves, result_token);
}

std::string pgn_movetext_from_moves(const std::vector<PgnMove>& moves,
                                    std::string_view result_token) {
    std::ostringstream out;
    bool first = true;
    for (std::size_t ply = 0; ply < moves.size(); ++ply) {
        if (ply % 2 == 0) {
            if (!first) {
                out << ' ';
            }
            out << (ply / 2 + 1) << '.';
            first = false;
        } else {
            out << ' ';
        }
        out << moves[ply].san;
        if (!moves[ply].comment.empty()) {
            std::string safe_comment = moves[ply].comment;
            for (char& ch : safe_comment) {
                if (ch == '}') {
                    ch = ']';
                }
            }
            out << '{' << safe_comment << '}';
        }
    }
    if (!first) {
        out << ' ';
    }
    out << result_token;
    return out.str();
}

std::string build_pgn(const std::map<std::string, std::string>& headers,
                      const std::vector<std::string>& sans,
                      std::string_view result_token,
                      const std::vector<std::optional<std::string>>* comments) {
    if (comments != nullptr && comments->size() != sans.size()) {
        throw std::invalid_argument("PGN comments length must match SAN move length");
    }

    std::vector<PgnMove> moves;
    moves.reserve(sans.size());
    for (std::size_t idx = 0; idx < sans.size(); ++idx) {
        std::string comment;
        if (comments != nullptr && (*comments)[idx].has_value()) {
            comment = *(*comments)[idx];
        }
        moves.push_back(PgnMove{sans[idx], comment});
    }

    std::ostringstream out;
    for (const auto& [key, value] : headers) {
        out << '[' << key << " \"" << escape_pgn_header_value(value) << "\"]\n";
    }
    out << '\n';
    out << pgn_movetext_from_moves(moves, result_token) << '\n';
    return out.str();
}

ParsedPgn parse_pgn_game(std::string_view pgn_text) {
    std::map<std::string, std::string> headers;
    std::vector<std::string> move_lines;
    bool in_headers = true;

    std::istringstream stream{std::string(pgn_text)};
    std::string raw_line;
    while (std::getline(stream, raw_line)) {
        std::string line = raw_line;
        while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) {
            line.pop_back();
        }

        const auto start = line.find_first_not_of(" \t");
        if (start == std::string::npos) {
            if (in_headers && headers.empty()) {
                continue;
            }
            in_headers = false;
            continue;
        }
        line = line.substr(start);
        const auto end = line.find_last_not_of(" \t");
        if (end != std::string::npos) {
            line = line.substr(0, end + 1);
        }

        if (in_headers && line.starts_with('[')) {
            std::smatch match;
            if (!std::regex_match(line, match, kPgnHeaderRe)) {
                throw std::invalid_argument("Invalid PGN header line: " + line);
            }
            headers[match[1].str()] = unescape_pgn_header_value(match[2].str());
            continue;
        }

        in_headers = false;
        if (line.starts_with('%')) {
            continue;
        }
        move_lines.push_back(line);
    }

    std::ostringstream movetext;
    for (std::size_t i = 0; i < move_lines.size(); ++i) {
        if (i > 0) {
            movetext << '\n';
        }
        movetext << move_lines[i];
    }

    auto [moves, result_token] = parse_pgn_movetext_mainline(movetext.str());
    const auto header_result = headers.find("Result");
    if (result_token == "*" && header_result != headers.end() &&
        is_result_token(header_result->second)) {
        result_token = header_result->second;
    }

    return ParsedPgn{std::move(headers), std::move(moves), result_token};
}

std::tuple<std::map<std::string, std::string>, std::vector<std::string>, std::string>
parse_pgn(std::string_view pgn_text) {
    const ParsedPgn parsed = parse_pgn_game(pgn_text);
    std::vector<std::string> sans;
    sans.reserve(parsed.moves.size());
    for (const PgnMove& move : parsed.moves) {
        sans.push_back(move.san);
    }
    return {parsed.headers, std::move(sans), parsed.result_token};
}

}  // namespace chessie
