#pragma once

/// @file tt.hpp
/// Transposition table for caching search results.
///
/// Uses a power-of-2 sized hash table with single-entry buckets.
/// Replacement policy: always-replace with age preference (newer entries
/// take priority; among same-age entries, deeper entries are preferred).

#include <chessie/move.hpp>
#include <chessie/types.hpp>

#include <cstdint>
#include <vector>

namespace chessie {

// ── Bound type ──────────────────────────────────────────────────────────────

/// The type of score stored in a TT entry.
enum class Bound : std::uint8_t {
    None = 0,   ///< Invalid / empty entry.
    Exact = 1,  ///< Exact minimax score (PV node).
    Lower = 2,  ///< Beta cutoff — score is a lower bound (fail-high).
    Upper = 3,  ///< Alpha not improved — score is an upper bound (fail-low).
};

// ── TT entry ────────────────────────────────────────────────────────────────

/// A single transposition table entry (16 bytes).
struct TTEntry {
    std::uint32_t key32 = 0;       ///< Upper 32 bits of Zobrist key for verification.
    std::int16_t score = 0;        ///< Search score (centipawns).
    std::int16_t static_eval = 0;  ///< Static eval at this node (for future pruning).
    Move best_move{};              ///< Best move found (4 bytes).
    std::uint8_t depth = 0;        ///< Search depth for this entry.
    Bound bound = Bound::None;     ///< Type of bound.
    std::uint8_t age = 0;          ///< Search generation (for replacement).
    std::uint8_t padding_ = 0;     ///< Padding to 16 bytes.
};

static_assert(sizeof(TTEntry) == 16, "TTEntry must be 16 bytes for cache efficiency");

// ── Transposition table ─────────────────────────────────────────────────────

class TranspositionTable {
   public:
    /// Default size: 64 MB.
    static constexpr std::size_t kDefaultSizeMB = 64;

    /// Construct with given size in megabytes. Rounds to nearest power of 2 entry count.
    explicit TranspositionTable(std::size_t mb = kDefaultSizeMB);

    /// Resize the table (clears all entries).
    void resize(std::size_t mb);

    /// Clear all entries (zero-fill).
    void clear();

    /// Increment the age counter. Call at the start of each new search.
    void new_search() noexcept;

    /// Probe the table for the given Zobrist key.
    /// @param key Full 64-bit Zobrist hash.
    /// @param[out] entry Filled with the stored entry on hit.
    /// @return true if the entry matches the key (hit), false otherwise (miss).
    [[nodiscard]] bool probe(std::uint64_t key, TTEntry& entry) const noexcept;

    /// Store / overwrite an entry.
    /// @param key Full 64-bit Zobrist hash.
    /// @param depth Search depth.
    /// @param score Search score.
    /// @param bound Bound type.
    /// @param best_move Best move found.
    /// @param static_eval Static evaluation at this node.
    void store(std::uint64_t key, int depth, int score, Bound bound, Move best_move,
               int static_eval) noexcept;

    /// Number of entries in the table. Useful for tests.
    [[nodiscard]] std::size_t entry_count() const noexcept { return table_.size(); }

    /// Current age. Useful for tests.
    [[nodiscard]] std::uint8_t age() const noexcept { return age_; }

    /// Approximate fill rate in per-mille (0-1000).
    /// Samples the first 1000 entries.
    [[nodiscard]] int hashfull() const noexcept;

   private:
    /// Extract the upper 32 bits as verification key.
    [[nodiscard]] static constexpr std::uint32_t key_upper(std::uint64_t key) noexcept {
        return static_cast<std::uint32_t>(key >> 32);
    }

    /// Map a Zobrist key to a table index.
    [[nodiscard]] std::size_t index(std::uint64_t key) const noexcept {
        return static_cast<std::size_t>(key) & mask_;
    }

    std::vector<TTEntry> table_;
    std::size_t mask_ = 0;  ///< entry_count - 1 (power-of-2 mask)
    std::uint8_t age_ = 0;  ///< Current search generation
};

}  // namespace chessie
