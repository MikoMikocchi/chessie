#pragma once

/// @file position.hpp
/// Complete chess position: board + side-to-move + castling + en passant + clocks.
///
/// Supports efficient make_move / unmake_move with an internal history stack
/// and incremental Zobrist hashing.

#include <chessie/board.hpp>
#include <chessie/move.hpp>
#include <chessie/zobrist.hpp>

#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace chessie {

// ── Constants ───────────────────────────────────────────────────────────────

inline constexpr std::string_view kStartingFen =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

// ── Undo info ───────────────────────────────────────────────────────────────

/// Snapshot saved before each move so we can undo it.
struct UndoInfo {
    CastlingRights castling;
    Square en_passant;
    int halfmove_clock;
    Piece captured;       ///< kNoPiece if no capture
    std::uint64_t key;    ///< Zobrist key before the move
};

// ── Castling rights update table ────────────────────────────────────────────
/// For each square, holds the castling rights to PRESERVE when that square is
/// involved as from or to in a move. Usage: `castling &= kCastleMask[from] & kCastleMask[to]`

namespace detail {

constexpr CastlingRights castling_mask_for(int sq) noexcept {
    // King starting squares remove both rights for their side.
    // Rook corner squares remove their specific right.
    switch (sq) {
        case A1:
            return static_cast<CastlingRights>(kCastlingAll & ~kWhiteQueenside);
        case H1:
            return static_cast<CastlingRights>(kCastlingAll & ~kWhiteKingside);
        case E1:
            return static_cast<CastlingRights>(kCastlingAll & ~kWhiteBoth);
        case A8:
            return static_cast<CastlingRights>(kCastlingAll & ~kBlackQueenside);
        case H8:
            return static_cast<CastlingRights>(kCastlingAll & ~kBlackKingside);
        case E8:
            return static_cast<CastlingRights>(kCastlingAll & ~kBlackBoth);
        default:
            return kCastlingAll;
    }
}

constexpr auto make_castling_masks() noexcept {
    std::array<CastlingRights, 64> masks{};
    for (int i = 0; i < 64; ++i) {
        masks[i] = castling_mask_for(i);
    }
    return masks;
}

inline constexpr auto kCastleMask = make_castling_masks();

}  // namespace detail

// ── Position ────────────────────────────────────────────────────────────────

class Position {
   public:
    /// Construct from explicit fields. Computes Zobrist hash.
    Position(Board board, Color side, CastlingRights castling, Square ep, int halfmove,
             int fullmove);

    /// Default: empty board, white to move, no castling, no EP.
    Position();

    // ── Factory ─────────────────────────────────────────────────────────

    /// Standard starting position.
    [[nodiscard]] static Position initial();

    /// Parse a FEN string. Throws std::invalid_argument on bad input.
    [[nodiscard]] static Position from_fen(std::string_view fen);

    // ── Serialization ───────────────────────────────────────────────────

    /// Serialize to FEN string.
    [[nodiscard]] std::string to_fen() const;

    // ── Move operations ─────────────────────────────────────────────────

    /// Apply a move, pushing undo state onto the history stack.
    void make_move(Move m);

    /// Undo the last make_move.
    void unmake_move(Move m);

    // ── Accessors ───────────────────────────────────────────────────────

    [[nodiscard]] const Board& board() const noexcept { return board_; }
    [[nodiscard]] Board& board() noexcept { return board_; }
    [[nodiscard]] Color side_to_move() const noexcept { return side_to_move_; }
    [[nodiscard]] CastlingRights castling() const noexcept { return castling_; }
    [[nodiscard]] Square en_passant() const noexcept { return en_passant_; }
    [[nodiscard]] int halfmove_clock() const noexcept { return halfmove_clock_; }
    [[nodiscard]] int fullmove_number() const noexcept { return fullmove_number_; }
    [[nodiscard]] std::uint64_t key() const noexcept { return key_; }

    // ── Attack queries ──────────────────────────────────────────────────
    // NOTE: magic::init() must be called once before using these.

    /// Is `sq` attacked by any piece of color `by`?
    [[nodiscard]] bool is_square_attacked(Square sq, Color by) const noexcept;

    /// Is the side-to-move's king in check?
    [[nodiscard]] bool is_in_check() const noexcept;

    /// Is the specified color's king in check?
    [[nodiscard]] bool is_in_check(Color c) const noexcept;

    // ── Repetition ──────────────────────────────────────────────────────

    /// How many times the current position key has occurred (including current).
    [[nodiscard]] int repetition_count() const;

   private:
    void compute_key();
    void toggle_piece_hash(Piece p, Square sq);
    void toggle_side_hash();
    void set_castling(CastlingRights cr);
    void set_en_passant(Square ep);

    Board board_;
    Color side_to_move_ = Color::White;
    CastlingRights castling_ = kCastlingNone;
    Square en_passant_ = kNoSquare;
    int halfmove_clock_ = 0;
    int fullmove_number_ = 1;
    std::uint64_t key_ = 0;
    std::vector<UndoInfo> history_;
    std::vector<std::uint64_t> key_history_;  ///< All keys since game start (for repetition)
};

}  // namespace chessie
