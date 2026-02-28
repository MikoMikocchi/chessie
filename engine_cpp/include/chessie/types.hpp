#pragma once

/// @file types.hpp
/// Core type aliases and enumerations for the chess engine.

#include <cstdint>
#include <string>
#include <string_view>

namespace chessie {

// ── Square ──────────────────────────────────────────────────────────────────
// Little-Endian Rank-File: a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63
using Square = std::uint8_t;

inline constexpr Square kNoSquare = 64;

[[nodiscard]] constexpr int file_of(Square sq) noexcept {
    return sq & 7;
}
[[nodiscard]] constexpr int rank_of(Square sq) noexcept {
    return sq >> 3;
}
[[nodiscard]] constexpr Square make_square(int file, int rank) noexcept {
    return static_cast<Square>(rank * 8 + file);
}
[[nodiscard]] constexpr bool is_valid_square(int sq) noexcept {
    return sq >= 0 && sq < 64;
}

[[nodiscard]] inline std::string square_name(Square sq) {
    return {static_cast<char>('a' + file_of(sq)), static_cast<char>('1' + rank_of(sq))};
}

[[nodiscard]] inline Square parse_square(std::string_view name) {
    if (name.size() != 2)
        return kNoSquare;
    int f = name[0] - 'a';
    int r = name[1] - '1';
    if (f < 0 || f > 7 || r < 0 || r > 7)
        return kNoSquare;
    return make_square(f, r);
}

// Named square constants
// clang-format off
enum SquareConstants : Square {
    A1, B1, C1, D1, E1, F1, G1, H1,
    A2, B2, C2, D2, E2, F2, G2, H2,
    A3, B3, C3, D3, E3, F3, G3, H3,
    A4, B4, C4, D4, E4, F4, G4, H4,
    A5, B5, C5, D5, E5, F5, G5, H5,
    A6, B6, C6, D6, E6, F6, G6, H6,
    A7, B7, C7, D7, E7, F7, G7, H7,
    A8, B8, C8, D8, E8, F8, G8, H8,
};
// clang-format on

// ── Color ───────────────────────────────────────────────────────────────────
enum class Color : std::uint8_t { White = 0, Black = 1 };

[[nodiscard]] constexpr Color opposite(Color c) noexcept {
    return static_cast<Color>(static_cast<int>(c) ^ 1);
}
[[nodiscard]] constexpr int color_index(Color c) noexcept {
    return static_cast<int>(c);
}

// ── PieceType ───────────────────────────────────────────────────────────────
enum class PieceType : std::uint8_t {
    None = 0,
    Pawn = 1,
    Knight = 2,
    Bishop = 3,
    Rook = 4,
    Queen = 5,
    King = 6,
};

inline constexpr int kNumPieceTypes = 6;

[[nodiscard]] constexpr int piece_index(PieceType pt) noexcept {
    return static_cast<int>(pt) - 1;  // Pawn=0 .. King=5
}

// ── MoveFlag ────────────────────────────────────────────────────────────────
enum class MoveFlag : std::uint8_t {
    Normal = 0,
    DoublePawn = 1,
    EnPassant = 2,
    CastleKingside = 3,
    CastleQueenside = 4,
    Promotion = 5,
};

// ── CastlingRights ──────────────────────────────────────────────────────────
enum CastlingRights : std::uint8_t {
    kCastlingNone = 0,
    kWhiteKingside = 1,
    kWhiteQueenside = 2,
    kBlackKingside = 4,
    kBlackQueenside = 8,
    kWhiteBoth = kWhiteKingside | kWhiteQueenside,
    kBlackBoth = kBlackKingside | kBlackQueenside,
    kCastlingAll = kWhiteBoth | kBlackBoth,
};

[[nodiscard]] constexpr CastlingRights operator|(CastlingRights a, CastlingRights b) noexcept {
    return static_cast<CastlingRights>(static_cast<int>(a) | static_cast<int>(b));
}
[[nodiscard]] constexpr CastlingRights operator&(CastlingRights a, CastlingRights b) noexcept {
    return static_cast<CastlingRights>(static_cast<int>(a) & static_cast<int>(b));
}
[[nodiscard]] constexpr CastlingRights operator~(CastlingRights a) noexcept {
    return static_cast<CastlingRights>(~static_cast<int>(a) & 0xF);
}
constexpr CastlingRights& operator|=(CastlingRights& a, CastlingRights b) noexcept {
    a = a | b;
    return a;
}
constexpr CastlingRights& operator&=(CastlingRights& a, CastlingRights b) noexcept {
    a = a & b;
    return a;
}

}  // namespace chessie
