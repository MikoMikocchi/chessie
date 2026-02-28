#pragma once

/// @file board.hpp
/// Bitboard-based chess board with mailbox redundancy.

#include <chessie/bitboard.hpp>
#include <chessie/piece.hpp>
#include <chessie/types.hpp>

#include <cstdint>

namespace chessie {

/// Bitboard-based board representation.
///
/// Maintains 12 piece bitboards (2 colors × 6 piece types),
/// aggregate occupancy bitboards, and a 64-element mailbox
/// for O(1) piece-at-square lookups.
class Board {
public:
    Board() noexcept { clear(); }

    // ── Piece placement ─────────────────────────────────────────────────

    /// Place a piece on the board. Square must be empty.
    void put_piece(Square sq, Piece p) noexcept {
        int ci = color_index(p.color);
        int pi = piece_index(p.type);
        set_bit(pieces_[ci][pi], sq);
        set_bit(occupied_[ci], sq);
        set_bit(occupied_all_, sq);
        mailbox_[sq] = p;
    }

    /// Remove a piece from the board. Square must be occupied.
    void remove_piece(Square sq) noexcept {
        Piece p = mailbox_[sq];
        int ci = color_index(p.color);
        int pi = piece_index(p.type);
        clear_bit(pieces_[ci][pi], sq);
        clear_bit(occupied_[ci], sq);
        clear_bit(occupied_all_, sq);
        mailbox_[sq] = kNoPiece;
    }

    /// Move a piece from one square to another. `from` must be occupied, `to` must be empty.
    void move_piece(Square from, Square to) noexcept {
        Piece p = mailbox_[from];
        int ci = color_index(p.color);
        int pi = piece_index(p.type);
        Bitboard mask = square_bb(from) | square_bb(to);
        pieces_[ci][pi] ^= mask;
        occupied_[ci] ^= mask;
        occupied_all_ ^= mask;
        mailbox_[to] = p;
        mailbox_[from] = kNoPiece;
    }

    // ── Queries ─────────────────────────────────────────────────────────

    /// Piece at a given square (kNoPiece if empty).
    [[nodiscard]] Piece piece_at(Square sq) const noexcept { return mailbox_[sq]; }

    /// Whether a square is empty.
    [[nodiscard]] bool is_empty(Square sq) const noexcept {
        return mailbox_[sq].type == PieceType::None;
    }

    /// Bitboard of all pieces of a given color and type.
    [[nodiscard]] Bitboard pieces(Color c, PieceType pt) const noexcept {
        return pieces_[color_index(c)][piece_index(pt)];
    }

    /// Bitboard of all pieces of a given color.
    [[nodiscard]] Bitboard occupied(Color c) const noexcept {
        return occupied_[color_index(c)];
    }

    /// Bitboard of all pieces on the board.
    [[nodiscard]] Bitboard occupied_all() const noexcept { return occupied_all_; }

    /// Square of the king for a given color.
    [[nodiscard]] Square king_square(Color c) const noexcept {
        return lsb(pieces(c, PieceType::King));
    }

    // ── Bulk operations ─────────────────────────────────────────────────

    void clear() noexcept {
        for (auto& color_pieces : pieces_) {
            for (auto& bb : color_pieces) {
                bb = kEmptyBB;
            }
        }
        occupied_[0] = kEmptyBB;
        occupied_[1] = kEmptyBB;
        occupied_all_ = kEmptyBB;
        for (auto& sq : mailbox_) {
            sq = kNoPiece;
        }
    }

    [[nodiscard]] bool operator==(const Board& other) const noexcept {
        for (int c = 0; c < 2; ++c) {
            for (int p = 0; p < kNumPieceTypes; ++p) {
                if (pieces_[c][p] != other.pieces_[c][p]) return false;
            }
        }
        return true;
    }

    // ── Factory ─────────────────────────────────────────────────────────

    /// Standard starting position.
    [[nodiscard]] static Board initial() noexcept;

private:
    Bitboard pieces_[2][6]{};   // [color_index][piece_index]
    Bitboard occupied_[2]{};    // [color_index]
    Bitboard occupied_all_{};
    Piece mailbox_[64]{};
};

}  // namespace chessie
