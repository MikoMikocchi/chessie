/// @file position.cpp
/// Position implementation: constructors, FEN, make/unmake, attacks.

#include <chessie/position.hpp>

#include <chessie/magic.hpp>

#include <charconv>
#include <stdexcept>
#include <string>
#include <vector>

namespace chessie {

// ── Helpers ─────────────────────────────────────────────────────────────────

namespace {

/// Split a string_view by spaces into up to `max_parts` pieces.
auto split_spaces(std::string_view sv, int max_parts = 8) -> std::vector<std::string_view> {
    std::vector<std::string_view> parts;
    parts.reserve(static_cast<std::size_t>(max_parts));
    std::size_t i = 0;
    while (i < sv.size()) {
        // Skip leading spaces
        while (i < sv.size() && sv[i] == ' ') ++i;
        if (i >= sv.size()) break;
        std::size_t start = i;
        while (i < sv.size() && sv[i] != ' ') ++i;
        parts.push_back(sv.substr(start, i - start));
    }
    return parts;
}

int parse_int(std::string_view sv, int min_val = 0) {
    int val = 0;
    auto [ptr, ec] = std::from_chars(sv.data(), sv.data() + sv.size(), val);
    if (ec != std::errc{} || ptr != sv.data() + sv.size()) {
        throw std::invalid_argument("Invalid integer in FEN: " + std::string(sv));
    }
    if (val < min_val) {
        throw std::invalid_argument("Integer out of range in FEN: " + std::string(sv));
    }
    return val;
}

}  // namespace

// ── Constructors ────────────────────────────────────────────────────────────

Position::Position(Board board, Color side, CastlingRights castling, Square ep, int halfmove,
                   int fullmove)
    : board_(board),
      side_to_move_(side),
      castling_(castling),
      en_passant_(ep),
      halfmove_clock_(halfmove),
      fullmove_number_(fullmove),
      key_(0) {
    compute_key();
}

Position::Position()
    : board_(),
      side_to_move_(Color::White),
      castling_(kCastlingNone),
      en_passant_(kNoSquare),
      halfmove_clock_(0),
      fullmove_number_(1),
      key_(0) {
    compute_key();
}

// ── Factory ─────────────────────────────────────────────────────────────────

Position Position::initial() {
    return from_fen(kStartingFen);
}

Position Position::from_fen(std::string_view fen) {
    auto parts = split_spaces(fen);
    if (parts.size() < 4 || parts.size() > 6) {
        throw std::invalid_argument("Invalid FEN (need 4-6 fields): " + std::string(fen));
    }

    // 1. Piece placement
    std::string_view placement = parts[0];
    Board board;
    int rank = 7;
    int file = 0;

    for (char ch : placement) {
        if (ch == '/') {
            if (file != 8) {
                throw std::invalid_argument("Invalid FEN rank width: " + std::string(fen));
            }
            --rank;
            file = 0;
            if (rank < 0) {
                throw std::invalid_argument("Too many ranks in FEN: " + std::string(fen));
            }
        } else if (ch >= '1' && ch <= '8') {
            file += ch - '0';
            if (file > 8) {
                throw std::invalid_argument("Invalid FEN rank width: " + std::string(fen));
            }
        } else {
            if (file >= 8) {
                throw std::invalid_argument("Invalid FEN rank width: " + std::string(fen));
            }
            Piece p = Piece::from_fen_char(ch);
            if (p.type == PieceType::None) {
                throw std::invalid_argument(std::string("Invalid FEN piece char: ") + ch);
            }
            board.put_piece(make_square(file, rank), p);
            ++file;
        }
    }
    if (rank != 0 || file != 8) {
        throw std::invalid_argument("Invalid FEN board placement: " + std::string(fen));
    }

    // 2. Side to move
    Color side = Color::White;
    if (parts[1] == "w") {
        side = Color::White;
    } else if (parts[1] == "b") {
        side = Color::Black;
    } else {
        throw std::invalid_argument(
            "Invalid FEN side-to-move: " + std::string(parts[1]));
    }

    // 3. Castling rights
    CastlingRights castling = kCastlingNone;
    if (parts[2] != "-") {
        for (char ch : parts[2]) {
            switch (ch) {
                case 'K':
                    castling |= kWhiteKingside;
                    break;
                case 'Q':
                    castling |= kWhiteQueenside;
                    break;
                case 'k':
                    castling |= kBlackKingside;
                    break;
                case 'q':
                    castling |= kBlackQueenside;
                    break;
                default:
                    throw std::invalid_argument(
                        std::string("Invalid castling char in FEN: ") + ch);
            }
        }
    }

    // 4. En passant
    Square ep = kNoSquare;
    if (parts[3] != "-") {
        ep = parse_square(parts[3]);
        if (ep == kNoSquare) {
            throw std::invalid_argument(
                "Invalid FEN en-passant square: " + std::string(parts[3]));
        }
    }

    // 5-6. Clocks (optional)
    int halfmove = (parts.size() > 4) ? parse_int(parts[4], 0) : 0;
    int fullmove = (parts.size() > 5) ? parse_int(parts[5], 1) : 1;

    return Position(board, side, castling, ep, halfmove, fullmove);
}

// ── Serialization ───────────────────────────────────────────────────────────

std::string Position::to_fen() const {
    std::string fen;
    fen.reserve(80);

    // 1. Piece placement (rank 8 → rank 1)
    for (int rank = 7; rank >= 0; --rank) {
        if (rank < 7) fen += '/';
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            Piece p = board_.piece_at(make_square(file, rank));
            if (p == kNoPiece) {
                ++empty;
            } else {
                if (empty > 0) {
                    fen += static_cast<char>('0' + empty);
                    empty = 0;
                }
                fen += p.fen_char();
            }
        }
        if (empty > 0) fen += static_cast<char>('0' + empty);
    }

    // 2. Side to move
    fen += ' ';
    fen += (side_to_move_ == Color::White) ? 'w' : 'b';

    // 3. Castling
    fen += ' ';
    if (castling_ == kCastlingNone) {
        fen += '-';
    } else {
        if (castling_ & kWhiteKingside) fen += 'K';
        if (castling_ & kWhiteQueenside) fen += 'Q';
        if (castling_ & kBlackKingside) fen += 'k';
        if (castling_ & kBlackQueenside) fen += 'q';
    }

    // 4. En passant
    fen += ' ';
    if (en_passant_ == kNoSquare) {
        fen += '-';
    } else {
        fen += square_name(en_passant_);
    }

    // 5-6. Clocks
    fen += ' ';
    fen += std::to_string(halfmove_clock_);
    fen += ' ';
    fen += std::to_string(fullmove_number_);

    return fen;
}

// ── Move operations ─────────────────────────────────────────────────────────

void Position::make_move(Move m) {
    Piece piece = board_.piece_at(m.from_sq);

    // Determine capture
    Piece captured = kNoPiece;
    Square capture_sq = m.to_sq;
    if (m.flag == MoveFlag::EnPassant) {
        capture_sq = make_square(file_of(m.to_sq), rank_of(m.from_sq));
        captured = board_.piece_at(capture_sq);
    } else {
        captured = board_.piece_at(m.to_sq);
    }

    // Save undo state
    history_.push_back({castling_, en_passant_, halfmove_clock_, captured, key_});

    // Remove moving piece from origin
    toggle_piece_hash(piece, m.from_sq);
    board_.remove_piece(m.from_sq);

    // Remove captured piece
    if (captured != kNoPiece) {
        toggle_piece_hash(captured, capture_sq);
        board_.remove_piece(capture_sq);
    }

    // Determine placed piece (handle promotion)
    Piece placed = piece;
    if (m.flag == MoveFlag::Promotion && m.promotion != PieceType::None) {
        placed = Piece{piece.color, m.promotion};
    }

    // Place piece at destination
    board_.put_piece(m.to_sq, placed);
    toggle_piece_hash(placed, m.to_sq);

    // Slide the rook for castling
    if (m.flag == MoveFlag::CastleKingside) {
        int r = rank_of(m.from_sq);
        Square rook_from = make_square(7, r);
        Square rook_to = make_square(5, r);
        Piece rook = board_.piece_at(rook_from);
        toggle_piece_hash(rook, rook_from);
        board_.remove_piece(rook_from);
        board_.put_piece(rook_to, rook);
        toggle_piece_hash(rook, rook_to);
    } else if (m.flag == MoveFlag::CastleQueenside) {
        int r = rank_of(m.from_sq);
        Square rook_from = make_square(0, r);
        Square rook_to = make_square(3, r);
        Piece rook = board_.piece_at(rook_from);
        toggle_piece_hash(rook, rook_from);
        board_.remove_piece(rook_from);
        board_.put_piece(rook_to, rook);
        toggle_piece_hash(rook, rook_to);
    }

    // En passant target for next move
    if (m.flag == MoveFlag::DoublePawn) {
        set_en_passant(
            make_square(file_of(m.from_sq), (rank_of(m.from_sq) + rank_of(m.to_sq)) / 2));
    } else {
        set_en_passant(kNoSquare);
    }

    // Castling rights update via mask table
    set_castling(castling_ & detail::kCastleMask[m.from_sq] & detail::kCastleMask[m.to_sq]);

    // Clocks
    if (piece.type == PieceType::Pawn || captured != kNoPiece) {
        halfmove_clock_ = 0;
    } else {
        ++halfmove_clock_;
    }
    if (side_to_move_ == Color::Black) {
        ++fullmove_number_;
    }

    // Switch side
    side_to_move_ = opposite(side_to_move_);
    toggle_side_hash();

    // Record key for repetition detection
    key_history_.push_back(key_);
}

void Position::unmake_move(Move m) {
    // Pop key history
    key_history_.pop_back();

    // Restore undo info
    UndoInfo undo = history_.back();
    history_.pop_back();

    // Unswitch side
    side_to_move_ = opposite(side_to_move_);
    if (side_to_move_ == Color::Black) {
        --fullmove_number_;
    }

    // Get the piece currently at to_sq
    Piece placed = board_.piece_at(m.to_sq);

    // Undo promotion: restore to pawn
    Piece original = placed;
    if (m.flag == MoveFlag::Promotion) {
        original = Piece{placed.color, PieceType::Pawn};
    }

    // Remove piece from destination
    board_.remove_piece(m.to_sq);

    // Put piece back at origin
    board_.put_piece(m.from_sq, original);

    // Restore captured piece
    if (undo.captured != kNoPiece) {
        if (m.flag == MoveFlag::EnPassant) {
            Square capture_sq = make_square(file_of(m.to_sq), rank_of(m.from_sq));
            board_.put_piece(capture_sq, undo.captured);
        } else {
            board_.put_piece(m.to_sq, undo.captured);
        }
    }

    // Undo castling rook slide
    if (m.flag == MoveFlag::CastleKingside) {
        int r = rank_of(m.from_sq);
        Square rook_at = make_square(5, r);
        Square rook_home = make_square(7, r);
        Piece rook = board_.piece_at(rook_at);
        board_.remove_piece(rook_at);
        board_.put_piece(rook_home, rook);
    } else if (m.flag == MoveFlag::CastleQueenside) {
        int r = rank_of(m.from_sq);
        Square rook_at = make_square(3, r);
        Square rook_home = make_square(0, r);
        Piece rook = board_.piece_at(rook_at);
        board_.remove_piece(rook_at);
        board_.put_piece(rook_home, rook);
    }

    // Restore state from undo
    castling_ = undo.castling;
    en_passant_ = undo.en_passant;
    halfmove_clock_ = undo.halfmove_clock;
    key_ = undo.key;
}

// ── Attack queries ──────────────────────────────────────────────────────────

bool Position::is_square_attacked(Square sq, Color by) const noexcept {
    Bitboard occ = board_.occupied_all();

    // Pawn attacks: a pawn of color `by` attacks `sq` if `sq` is in pawn_attacks
    // of a pawn of `by`. Equivalently, check if any `by` pawn sits on
    // pawn_attacks(opposite(by), sq).
    if (pawn_attacks(opposite(by), sq) & board_.pieces(by, PieceType::Pawn)) {
        return true;
    }

    // Knight
    if (knight_attacks(sq) & board_.pieces(by, PieceType::Knight)) {
        return true;
    }

    // King
    if (king_attacks(sq) & board_.pieces(by, PieceType::King)) {
        return true;
    }

    // Bishop / Queen (diagonal)
    Bitboard diag_sliders =
        board_.pieces(by, PieceType::Bishop) | board_.pieces(by, PieceType::Queen);
    if (magic::bishop_attacks(sq, occ) & diag_sliders) {
        return true;
    }

    // Rook / Queen (straight)
    Bitboard straight_sliders =
        board_.pieces(by, PieceType::Rook) | board_.pieces(by, PieceType::Queen);
    if (magic::rook_attacks(sq, occ) & straight_sliders) {
        return true;
    }

    return false;
}

bool Position::is_in_check() const noexcept {
    return is_in_check(side_to_move_);
}

bool Position::is_in_check(Color c) const noexcept {
    return is_square_attacked(board_.king_square(c), opposite(c));
}

// ── Repetition ──────────────────────────────────────────────────────────────

int Position::repetition_count() const {
    int count = 0;
    for (auto k : key_history_) {
        if (k == key_) ++count;
    }
    return count;
}

// ── Private helpers ─────────────────────────────────────────────────────────

void Position::compute_key() {
    key_ = 0;
    key_ ^= zobrist::castling_key(castling_);
    if (side_to_move_ == Color::Black) {
        key_ ^= zobrist::side_to_move_key();
    }
    if (en_passant_ != kNoSquare) {
        key_ ^= zobrist::en_passant_key(en_passant_);
    }
    for (int sq = 0; sq < 64; ++sq) {
        Piece p = board_.piece_at(static_cast<Square>(sq));
        if (p != kNoPiece) {
            key_ ^= zobrist::piece_key(p.color, p.type, static_cast<Square>(sq));
        }
    }
    key_history_.clear();
    key_history_.push_back(key_);
}

void Position::toggle_piece_hash(Piece p, Square sq) {
    key_ ^= zobrist::piece_key(p.color, p.type, sq);
}

void Position::toggle_side_hash() {
    key_ ^= zobrist::side_to_move_key();
}

void Position::set_castling(CastlingRights cr) {
    if (cr == castling_) return;
    key_ ^= zobrist::castling_key(castling_);
    castling_ = cr;
    key_ ^= zobrist::castling_key(castling_);
}

void Position::set_en_passant(Square ep) {
    if (ep == en_passant_) return;
    if (en_passant_ != kNoSquare) {
        key_ ^= zobrist::en_passant_key(en_passant_);
    }
    en_passant_ = ep;
    if (en_passant_ != kNoSquare) {
        key_ ^= zobrist::en_passant_key(en_passant_);
    }
}

}  // namespace chessie
