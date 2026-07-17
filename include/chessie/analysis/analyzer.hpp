#pragma once

/// @file analyzer.hpp
/// Game analyzer service based on the built-in search engine.

#include <chessie/analysis/models.hpp>
#include <chessie/engine.hpp>
#include <chessie/game/state.hpp>
#include <chessie/search.hpp>

#include <functional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace chessie {

class AnalysisCancelled : public std::runtime_error {
   public:
    AnalysisCancelled() : std::runtime_error("Analysis cancelled") {}
};

using AnalysisProgressCallback = std::function<void(int done, int total)>;
using AnalysisCancelCallback = std::function<bool()>;

class GameAnalyzer {
   public:
    explicit GameAnalyzer(Engine* engine = nullptr);

    [[nodiscard]] GameAnalysisReport analyzeGame(
        std::string_view start_fen,
        const std::vector<MoveRecord>& move_history,
        const SearchLimits& limits,
        const AnalysisCancelCallback& is_cancelled = {},
        const AnalysisProgressCallback& on_progress = {});

   private:
    Engine owned_engine_;
    Engine* engine_;
};

[[nodiscard]] std::string computeMoveFingerprint(std::string_view start_fen,
                                                 const std::vector<MoveRecord>& history);

}  // namespace chessie
