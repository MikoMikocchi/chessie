#pragma once

/// @file models.hpp
/// Data models produced by game analysis.

#include <chessie/move.hpp>
#include <chessie/types.hpp>

#include <optional>
#include <string>
#include <vector>

namespace chessie {

enum class MoveJudgment {
    Brilliant,
    Great,
    Best,
    Good,
    Inaccuracy,
    Mistake,
    Blunder,
};

[[nodiscard]] inline std::string_view judgment_nag(MoveJudgment judgment) noexcept {
    switch (judgment) {
        case MoveJudgment::Brilliant:
            return "!!";
        case MoveJudgment::Great:
            return "!";
        case MoveJudgment::Best:
            return "";
        case MoveJudgment::Good:
            return "";
        case MoveJudgment::Inaccuracy:
            return "?!";
        case MoveJudgment::Mistake:
            return "?";
        case MoveJudgment::Blunder:
            return "??";
    }
    return "";
}

[[nodiscard]] inline std::string_view judgment_color_hex(MoveJudgment judgment) noexcept {
    switch (judgment) {
        case MoveJudgment::Brilliant:
            return "#1baaa7";
        case MoveJudgment::Great:
            return "#5c8bb0";
        case MoveJudgment::Best:
            return "#9bc700";
        case MoveJudgment::Good:
            return "#97af8b";
        case MoveJudgment::Inaccuracy:
            return "#f7c631";
        case MoveJudgment::Mistake:
            return "#e68a2e";
        case MoveJudgment::Blunder:
            return "#ca3431";
    }
    return "#97af8b";
}

struct SideAnalysisSummary {
    int moves = 0;
    double avg_cp_loss = 0.0;
    int inaccuracies = 0;
    int mistakes = 0;
    int blunders = 0;
    int brilliant = 0;
    int great = 0;
    int best = 0;
    int good = 0;
    double accuracy = 0.0;
};

struct MoveAnalysis {
    int ply = 0;
    Color color = Color::White;
    Move played_move{};
    std::string played_san;
    std::optional<Move> best_move;
    std::optional<std::string> best_san;
    int eval_before_white_cp = 0;
    int eval_after_white_cp = 0;
    int cp_loss = 0;
    MoveJudgment judgment = MoveJudgment::Best;
};

struct GameAnalysisReport {
    std::string start_fen;
    int total_plies = 0;
    std::vector<MoveAnalysis> moves;
    SideAnalysisSummary white;
    SideAnalysisSummary black;
    std::vector<int> critical_plies;
    std::string move_fingerprint;
};

}  // namespace chessie
