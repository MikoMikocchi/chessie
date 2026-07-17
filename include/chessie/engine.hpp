#pragma once

/// @file engine.hpp
/// High-level engine facade: wraps Search + TranspositionTable.

#include <chessie/search.hpp>

#include <cstddef>

namespace chessie {

/// Top-level chess engine API.
class Engine {
   public:
    explicit Engine(std::size_t tt_mb = 64);

    /// Run search and return the result.
    SearchResult search(Position& pos, const SearchLimits& limits);

    /// Cancel a running search (thread-safe).
    void cancel() noexcept;

    /// Resize the transposition table (clears it).
    void set_tt_size(std::size_t mb);

    /// Clear the transposition table.
    void clear_tt();

   private:
    Search search_;
};

}  // namespace chessie
