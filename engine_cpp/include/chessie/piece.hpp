#pragma once

/// @file piece.hpp
/// Piece value object (color + type).

#include <chessie/types.hpp>

#include <string>

namespace chessie {

/// An immutable piece on the board (color + type).
struct Piece {
    Color color;
    PieceType type;

    [[nodiscard]] constexpr bool operator==(const Piece&) const noexcept = default;

    /// FEN character for this piece ('P','N','B','R','Q','K' for white, lowercase for black).
    [[nodiscard]] constexpr char fen_char() const noexcept {
        // clang-format off
        constexpr char kChars[2][7] = {
            {' ', 'P', 'N', 'B', 'R', 'Q', 'K'},
            {' ', 'p', 'n', 'b', 'r', 'q', 'k'},
        };
        // clang-format on
        return kChars[color_index(color)][static_cast<int>(type)];
    }

    /// Parse a FEN piece character. Returns Piece with PieceType::None on failure.
    [[nodiscard]] static constexpr Piece from_fen_char(char ch) noexcept {
        switch (ch) {
                // clang-format off
            case 'P': return {Color::White, PieceType::Pawn};
            case 'N': return {Color::White, PieceType::Knight};
            case 'B': return {Color::White, PieceType::Bishop};
            case 'R': return {Color::White, PieceType::Rook};
            case 'Q': return {Color::White, PieceType::Queen};
            case 'K': return {Color::White, PieceType::King};
            case 'p': return {Color::Black, PieceType::Pawn};
            case 'n': return {Color::Black, PieceType::Knight};
            case 'b': return {Color::Black, PieceType::Bishop};
            case 'r': return {Color::Black, PieceType::Rook};
            case 'q': return {Color::Black, PieceType::Queen};
            case 'k': return {Color::Black, PieceType::King};
            default:  return {Color::White, PieceType::None};
                // clang-format on
        }
    }
};

/// Sentinel value for "no piece".
inline constexpr Piece kNoPiece{Color::White, PieceType::None};

}  // namespace chessie
