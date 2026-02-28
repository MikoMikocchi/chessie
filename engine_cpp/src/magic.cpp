/// @file magic.cpp
/// Magic bitboard implementation for sliding piece attack generation.
///
/// Finds magic numbers at init time via brute-force PRNG search.
/// This guarantees correctness regardless of the bit layout.

#include <chessie/magic.hpp>

#include <array>
#include <cstdint>
#include <vector>

namespace chessie::magic {

namespace {

// ── PRNG for magic number search ────────────────────────────────────────────

struct Rng {
    std::uint64_t s;
    explicit Rng(std::uint64_t seed) : s(seed) {}
    std::uint64_t next() {
        s ^= s >> 12;
        s ^= s << 25;
        s ^= s >> 27;
        return s * 0x2545F4914F6CDD1DULL;
    }
    /// Sparse random — good candidates for magic numbers have few bits set
    std::uint64_t sparse() { return next() & next() & next(); }
};

// ── Ray-traced sliding attacks (used to build tables) ───────────────────────

Bitboard ray_attacks(Square sq, Bitboard occupancy, int df, int dr) {
    Bitboard attacks = kEmptyBB;
    int f = file_of(sq) + df;
    int r = rank_of(sq) + dr;
    while (f >= 0 && f <= 7 && r >= 0 && r <= 7) {
        Square s = make_square(f, r);
        set_bit(attacks, s);
        if (test_bit(occupancy, s)) break;
        f += df;
        r += dr;
    }
    return attacks;
}

Bitboard bishop_attacks_slow(Square sq, Bitboard occupancy) {
    return ray_attacks(sq, occupancy, 1, 1) | ray_attacks(sq, occupancy, 1, -1) |
           ray_attacks(sq, occupancy, -1, 1) | ray_attacks(sq, occupancy, -1, -1);
}

Bitboard rook_attacks_slow(Square sq, Bitboard occupancy) {
    return ray_attacks(sq, occupancy, 1, 0) | ray_attacks(sq, occupancy, -1, 0) |
           ray_attacks(sq, occupancy, 0, 1) | ray_attacks(sq, occupancy, 0, -1);
}

// ── Relevant occupancy masks ────────────────────────────────────────────────

Bitboard bishop_mask(Square sq) {
    Bitboard mask = kEmptyBB;
    int f0 = file_of(sq);
    int r0 = rank_of(sq);
    constexpr int df[] = {1, 1, -1, -1};
    constexpr int dr[] = {1, -1, 1, -1};
    for (int d = 0; d < 4; ++d) {
        int f = f0 + df[d];
        int r = r0 + dr[d];
        while (f > 0 && f < 7 && r > 0 && r < 7) {
            set_bit(mask, make_square(f, r));
            f += df[d];
            r += dr[d];
        }
    }
    return mask;
}

Bitboard rook_mask(Square sq) {
    Bitboard mask = kEmptyBB;
    int f0 = file_of(sq);
    int r0 = rank_of(sq);
    for (int f = f0 + 1; f < 7; ++f) set_bit(mask, make_square(f, r0));
    for (int f = f0 - 1; f > 0; --f) set_bit(mask, make_square(f, r0));
    for (int r = r0 + 1; r < 7; ++r) set_bit(mask, make_square(f0, r));
    for (int r = r0 - 1; r > 0; --r) set_bit(mask, make_square(f0, r));
    return mask;
}

// ── Per-square magic entry ──────────────────────────────────────────────────

struct MagicEntry {
    Bitboard mask{};
    std::uint64_t magic{};
    int shift{};
    int offset{};  // into the flat attack table
};

MagicEntry g_bishop_entries[64]{};
MagicEntry g_rook_entries[64]{};

// Flat attack tables (dynamically filled at init)
// Bishop needs ~5248 entries; rook ~102400. We use vectors for simplicity.
std::vector<Bitboard> g_bishop_table;
std::vector<Bitboard> g_rook_table;

bool g_initialized = false;

// ── Enumerate subsets and build occupancy/attack arrays ─────────────────────

void enumerate_subsets(Bitboard mask, std::vector<Bitboard>& occupancies,
                       std::vector<Bitboard>& attacks, Square sq, bool is_rook) {
    Bitboard sub = 0;
    do {
        occupancies.push_back(sub);
        attacks.push_back(is_rook ? rook_attacks_slow(sq, sub) : bishop_attacks_slow(sq, sub));
        sub = (sub - mask) & mask;
    } while (sub != 0);
}

// ── Find a magic number for one square ──────────────────────────────────────

std::uint64_t find_magic(Square /*sq*/, int bits, Bitboard mask, const std::vector<Bitboard>& occs,
                         const std::vector<Bitboard>& atks, Rng& rng) {
    int table_size = 1 << bits;
    std::vector<Bitboard> used(static_cast<std::size_t>(table_size), 0);
    std::vector<bool> filled(static_cast<std::size_t>(table_size), false);

    for (int attempt = 0; attempt < 100'000'000; ++attempt) {
        std::uint64_t magic = rng.sparse();

        // Quick reject: top bits of mask*magic should have enough set bits
        if (popcount(static_cast<Bitboard>((mask * magic) & 0xFF00000000000000ULL)) < 6) continue;

        // Reset
        std::fill(filled.begin(), filled.end(), false);

        bool ok = true;
        for (std::size_t i = 0; i < occs.size(); ++i) {
            int idx = static_cast<int>((occs[i] * magic) >> (64 - bits));
            auto uidx = static_cast<std::size_t>(idx);
            if (!filled[uidx]) {
                filled[uidx] = true;
                used[uidx] = atks[i];
            } else if (used[uidx] != atks[i]) {
                ok = false;
                break;
            }
            // If filled and same attacks — constructive collision, fine
        }
        if (ok) return magic;
    }

    // Should never happen for valid chess positions
    return 0;
}

// ── Init one piece type ─────────────────────────────────────────────────────

void init_piece(MagicEntry* entries, std::vector<Bitboard>& table, bool is_rook, Rng& rng) {
    int total_offset = 0;

    for (int sq = 0; sq < 64; ++sq) {
        auto s = static_cast<Square>(sq);
        Bitboard mask = is_rook ? rook_mask(s) : bishop_mask(s);
        int bits = popcount(mask);

        std::vector<Bitboard> occs;
        std::vector<Bitboard> atks;
        enumerate_subsets(mask, occs, atks, s, is_rook);

        std::uint64_t magic = find_magic(s, bits, mask, occs, atks, rng);

        entries[sq].mask = mask;
        entries[sq].magic = magic;
        entries[sq].shift = 64 - bits;
        entries[sq].offset = total_offset;

        int table_size = 1 << bits;
        table.resize(static_cast<std::size_t>(total_offset + table_size), 0);

        // Fill the table
        for (std::size_t i = 0; i < occs.size(); ++i) {
            int idx = static_cast<int>((occs[i] * magic) >> entries[sq].shift);
            table[static_cast<std::size_t>(total_offset + idx)] = atks[i];
        }

        total_offset += table_size;
    }
}

}  // namespace

// ── Public API ──────────────────────────────────────────────────────────────

void init() {
    if (g_initialized) return;
    Rng rng(0x12345678ABCDEF01ULL);
    init_piece(g_bishop_entries, g_bishop_table, false, rng);
    init_piece(g_rook_entries, g_rook_table, true, rng);
    g_initialized = true;
}

Bitboard bishop_attacks(Square sq, Bitboard occupancy) noexcept {
    const auto& e = g_bishop_entries[sq];
    auto idx = static_cast<std::size_t>(
        e.offset + static_cast<int>(((occupancy & e.mask) * e.magic) >> e.shift));
    return g_bishop_table[idx];
}

Bitboard rook_attacks(Square sq, Bitboard occupancy) noexcept {
    const auto& e = g_rook_entries[sq];
    auto idx = static_cast<std::size_t>(
        e.offset + static_cast<int>(((occupancy & e.mask) * e.magic) >> e.shift));
    return g_rook_table[idx];
}

}  // namespace chessie::magic
