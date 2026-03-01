#pragma once

/// @file search.hpp
/// Alpha-beta search with iterative deepening, TT, null move pruning,
/// LMR, quiescence, killer moves, and history heuristic.

#include <chessie/evaluation.hpp>
#include <chessie/movegen.hpp>
#include <chessie/tt.hpp>

#include <atomic>
#include <chrono>
#include <cstdint>

namespace chessie {

// ── Constants ───────────────────────────────────────────────────────────────

inline constexpr int kInfScore = 1'000'000;
inline constexpr int kMateScore = 100'000;
inline constexpr int kMaxPly = 128;

// ── Search limits ───────────────────────────────────────────────────────────

struct SearchLimits {
    int max_depth = 64;
    std::int64_t time_limit_ms = -1;  ///< -1 = no time limit.
};

// ── Search result ───────────────────────────────────────────────────────────

struct SearchResult {
    Move best_move{};
    int score_cp = 0;
    int depth = 0;
    std::uint64_t nodes = 0;
};

// ── Search class ────────────────────────────────────────────────────────────

class Search {
   public:
    explicit Search(std::size_t tt_mb = 64);

    /// Run iterative-deepening search. Returns the best move and score.
    SearchResult search(Position& pos, const SearchLimits& limits);

    /// Cancel the search from another thread (or same thread via callback).
    void cancel() noexcept { cancelled_.store(true, std::memory_order_relaxed); }

    /// Access the TT for resizing, etc.
    TranspositionTable& tt() noexcept { return tt_; }

   private:
    // ── Core search routines ────────────────────────────────────────────
    int negamax(Position& pos, int depth, int alpha, int beta, int ply, bool allow_null);
    int quiescence(Position& pos, int alpha, int beta, int ply, int q_depth);

    // ── Move ordering ───────────────────────────────────────────────────
    void order_moves(const Position& pos, MoveList& ml, Move tt_move, int ply);
    int move_score(const Position& pos, Move m, Move tt_move, int ply) const;

    // ── Helpers ─────────────────────────────────────────────────────────
    [[nodiscard]] bool should_stop() const;
    [[nodiscard]] bool is_draw(const Position& pos) const;
    [[nodiscard]] bool has_non_pawn_material(const Position& pos, Color side) const;

    void record_killer(Move m, int ply);
    void update_history(Color side, Move m, int depth);
    void reset_heuristics();

    // ── Data members ────────────────────────────────────────────────────
    TranspositionTable tt_;

    // Killer moves: 2 per ply
    Move killers_[kMaxPly][2]{};

    // History heuristic: [color][from][to]
    int history_[2][64][64]{};

    // Cancellation
    std::atomic<bool> cancelled_{false};

    // Time management
    std::chrono::steady_clock::time_point deadline_{};
    bool has_deadline_ = false;

    // Stats
    std::uint64_t nodes_ = 0;
};

}  // namespace chessie
