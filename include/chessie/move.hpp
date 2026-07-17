#pragma once

/// @file move.hpp
/// Move representation and MoveList container.

#include <chessie/types.hpp>

#include <array>
#include <string>

namespace chessie {

/// A chess move: from-square, to-square, flag, and optional promotion type.
struct Move {
    Square from_sq = 0;
    Square to_sq = 0;
    MoveFlag flag = MoveFlag::Normal;
    PieceType promotion = PieceType::None;

    [[nodiscard]] constexpr bool operator==(const Move&) const noexcept = default;

    /// UCI long-algebraic notation, e.g. "e2e4", "e7e8q".
    [[nodiscard]] inline std::string uci() const {
        std::string s = square_name(from_sq) + square_name(to_sq);
        if (promotion != PieceType::None) {
            // clang-format off
            constexpr char kPromoChars[] = {' ', ' ', 'n', 'b', 'r', 'q', ' '};
            // clang-format on
            s += kPromoChars[static_cast<int>(promotion)];
        }
        return s;
    }

    /// Parse a UCI move string (4 or 5 chars). Returns a default (invalid) move on failure.
    [[nodiscard]] static inline Move from_uci(std::string_view uci_str) {
        if (uci_str.size() < 4)
            return {};
        Square from = parse_square(uci_str.substr(0, 2));
        Square to = parse_square(uci_str.substr(2, 2));
        if (from == kNoSquare || to == kNoSquare)
            return {};

        Move m{from, to, MoveFlag::Normal, PieceType::None};

        if (uci_str.size() >= 5) {
            m.flag = MoveFlag::Promotion;
            switch (uci_str[4]) {
                case 'n':
                    m.promotion = PieceType::Knight;
                    break;
                case 'b':
                    m.promotion = PieceType::Bishop;
                    break;
                case 'r':
                    m.promotion = PieceType::Rook;
                    break;
                case 'q':
                    m.promotion = PieceType::Queen;
                    break;
                default:
                    break;
            }
        }
        return m;
    }

    /// Check whether this move is null / invalid.
    [[nodiscard]] constexpr bool is_null() const noexcept {
        return from_sq == 0 && to_sq == 0 && flag == MoveFlag::Normal &&
               promotion == PieceType::None;
    }
};

/// Sentinel for "no move".
inline constexpr Move kNullMove{};

// ── MoveList ────────────────────────────────────────────────────────────────

/// Fixed-capacity list of moves (max theoretical legal moves in chess ≈ 218).
class MoveList {
   public:
    static constexpr int kMaxMoves = 256;

    constexpr void push(Move m) noexcept { moves_[count_++] = m; }
    [[nodiscard]] constexpr int size() const noexcept { return count_; }
    [[nodiscard]] constexpr bool empty() const noexcept { return count_ == 0; }
    constexpr void clear() noexcept { count_ = 0; }

    [[nodiscard]] constexpr Move& operator[](int i) noexcept { return moves_[i]; }
    [[nodiscard]] constexpr const Move& operator[](int i) const noexcept { return moves_[i]; }

    // Iterator support
    [[nodiscard]] constexpr Move* begin() noexcept { return moves_.data(); }
    [[nodiscard]] constexpr Move* end() noexcept { return moves_.data() + count_; }
    [[nodiscard]] constexpr const Move* begin() const noexcept { return moves_.data(); }
    [[nodiscard]] constexpr const Move* end() const noexcept { return moves_.data() + count_; }

   private:
    std::array<Move, kMaxMoves> moves_{};
    int count_ = 0;
};

}  // namespace chessie
