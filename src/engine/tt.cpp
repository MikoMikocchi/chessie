/// @file tt.cpp
/// Transposition table implementation.

#include <chessie/tt.hpp>

#include <algorithm>
#include <cstring>

namespace chessie {

// ── Helpers ─────────────────────────────────────────────────────────────────

/// Round down to the nearest power of 2.
static std::size_t round_down_pow2(std::size_t v) noexcept {
    if (v == 0)
        return 1;
    v |= v >> 1;
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;
    v |= v >> 32;
    return (v >> 1) + 1;
}

// ── TranspositionTable ──────────────────────────────────────────────────────

TranspositionTable::TranspositionTable(std::size_t mb) {
    resize(mb);
}

void TranspositionTable::resize(std::size_t mb) {
    if (mb == 0)
        mb = 1;

    // Calculate how many entries fit in the given MB
    constexpr std::size_t kEntrySize = sizeof(TTEntry);
    std::size_t bytes = mb * 1024ULL * 1024ULL;
    std::size_t num_entries = bytes / kEntrySize;

    // Round down to power of 2
    num_entries = round_down_pow2(num_entries);

    // Minimum 1024 entries
    num_entries = std::max(num_entries, std::size_t{1024});

    table_.assign(num_entries, TTEntry{});
    mask_ = num_entries - 1;
    age_ = 0;
}

void TranspositionTable::clear() {
    std::fill(table_.begin(), table_.end(), TTEntry{});
    age_ = 0;
}

void TranspositionTable::new_search() noexcept {
    ++age_;
}

bool TranspositionTable::probe(std::uint64_t key, TTEntry& entry) const noexcept {
    const auto idx = index(key);
    const auto& slot = table_[idx];

    if (slot.bound != Bound::None && slot.key32 == key_upper(key)) {
        entry = slot;
        return true;
    }
    return false;
}

void TranspositionTable::store(std::uint64_t key, int depth, int score, Bound bound, Move best_move,
                               int static_eval) noexcept {
    const auto idx = index(key);
    auto& slot = table_[idx];
    const auto key32 = key_upper(key);

    // Replacement policy:
    // 1. Always replace empty entries.
    // 2. Always replace entries from older searches.
    // 3. For same-age entries, replace if new depth >= stored depth,
    //    or if the new entry is exact and the old one isn't.
    bool should_replace =
        (slot.bound == Bound::None)                                // empty
        || (slot.age != age_)                                      // stale
        || (depth >= slot.depth)                                   // deeper or equal
        || (bound == Bound::Exact && slot.bound != Bound::Exact);  // exact > non-exact

    if (!should_replace)
        return;

    // If we're storing to existing entry with same key, preserve best_move if new one is null
    if (slot.key32 == key32 && best_move.is_null() && !slot.best_move.is_null()) {
        best_move = slot.best_move;
    }

    slot.key32 = key32;
    slot.score = static_cast<std::int16_t>(score);
    slot.static_eval = static_cast<std::int16_t>(static_eval);
    slot.best_move = best_move;
    slot.depth = static_cast<std::uint8_t>(depth);
    slot.bound = bound;
    slot.age = age_;
}

int TranspositionTable::hashfull() const noexcept {
    if (table_.empty())
        return 0;
    const std::size_t sample_size = std::min(table_.size(), std::size_t{1000});
    int used = 0;
    for (std::size_t i = 0; i < sample_size; ++i) {
        if (table_[i].bound != Bound::None && table_[i].age == age_) {
            ++used;
        }
    }
    return static_cast<int>(used * 1000 / sample_size);
}

}  // namespace chessie
