#include <chessie/notation/san.hpp>

#include <chessie/movegen.hpp>

#include <cctype>
#include <stdexcept>
#include <unordered_map>

namespace chessie {

namespace {

const std::unordered_map<PieceType, char> kSanPiece = {
    {PieceType::Knight, 'N'},
    {PieceType::Bishop, 'B'},
    {PieceType::Rook, 'R'},
    {PieceType::Queen, 'Q'},
    {PieceType::King, 'K'},
};

const std::unordered_map<char, PieceType> kSanPieceRev = {
    {'N', PieceType::Knight},
    {'B', PieceType::Bishop},
    {'R', PieceType::Rook},
    {'Q', PieceType::Queen},
    {'K', PieceType::King},
};

}  // namespace

std::string move_to_san(Position& position, Move move) {
    const Board& board = position.board();
    const Piece piece = board.piece_at(move.from_sq);
    if (piece.type == PieceType::None) {
        throw std::invalid_argument("move_to_san: empty from-square");
    }

    std::string san;
    if (move.flag == MoveFlag::CastleKingside) {
        san = "O-O";
    } else if (move.flag == MoveFlag::CastleQueenside) {
        san = "O-O-O";
    } else {
        const bool is_capture =
            board.piece_at(move.to_sq).type != PieceType::None || move.flag == MoveFlag::EnPassant;

        if (piece.type == PieceType::Pawn) {
            if (is_capture) {
                san += static_cast<char>('a' + file_of(move.from_sq));
            }
        } else {
            san += kSanPiece.at(piece.type);

            const MoveList legal = movegen::legal(position);
            std::vector<Move> ambiguous;
            for (const Move& m : legal) {
                if (m.to_sq != move.to_sq || m.from_sq == move.from_sq) {
                    continue;
                }
                const Piece other = board.piece_at(m.from_sq);
                if (other.type == piece.type) {
                    ambiguous.push_back(m);
                }
            }

            if (!ambiguous.empty()) {
                bool same_file = false;
                bool same_rank = false;
                for (const Move& m : ambiguous) {
                    if (file_of(m.from_sq) == file_of(move.from_sq)) {
                        same_file = true;
                    }
                    if (rank_of(m.from_sq) == rank_of(move.from_sq)) {
                        same_rank = true;
                    }
                }
                if (!same_file) {
                    san += static_cast<char>('a' + file_of(move.from_sq));
                } else if (!same_rank) {
                    san += static_cast<char>('1' + rank_of(move.from_sq));
                } else {
                    san += square_name(move.from_sq);
                }
            }
        }

        if (is_capture) {
            san += 'x';
        }
        san += square_name(move.to_sq);

        if (move.flag == MoveFlag::Promotion && move.promotion != PieceType::None) {
            san += '=';
            san += kSanPiece.at(move.promotion);
        }
    }

    position.make_move(move);
    if (position.is_in_check(position.side_to_move())) {
        const MoveList legal_after = movegen::legal(position);
        san += legal_after.empty() ? '#' : '+';
    }
    position.unmake_move(move);

    return san;
}

Move parse_san(Position& position, std::string_view san) {
    const MoveList legal = movegen::legal(position);

    std::string clean(san);
    while (!clean.empty() && (clean.back() == '+' || clean.back() == '#' || clean.back() == '!' ||
                              clean.back() == '?')) {
        clean.pop_back();
    }

    if (clean == "O-O" || clean == "0-0") {
        for (const Move& m : legal) {
            if (m.flag == MoveFlag::CastleKingside) {
                return m;
            }
        }
        throw std::invalid_argument(std::string("Illegal move: ") + std::string(san));
    }

    if (clean == "O-O-O" || clean == "0-0-0") {
        for (const Move& m : legal) {
            if (m.flag == MoveFlag::CastleQueenside) {
                return m;
            }
        }
        throw std::invalid_argument(std::string("Illegal move: ") + std::string(san));
    }

    PieceType promotion = PieceType::None;
    if (const auto eq = clean.find('='); eq != std::string::npos) {
        const char promo_char = clean.back();
        const auto it = kSanPieceRev.find(promo_char);
        if (it == kSanPieceRev.end()) {
            throw std::invalid_argument(std::string("Illegal move: ") + std::string(san));
        }
        promotion = it->second;
        clean.erase(eq);
    }

    if (clean.size() < 2) {
        throw std::invalid_argument(std::string("Illegal move: ") + std::string(san));
    }

    const Square to_sq = parse_square(clean.substr(clean.size() - 2));
    if (to_sq == kNoSquare) {
        throw std::invalid_argument(std::string("Illegal move: ") + std::string(san));
    }
    clean.erase(clean.size() - 2);

    if (!clean.empty() && clean.back() == 'x') {
        clean.pop_back();
    }

    PieceType piece_type = PieceType::Pawn;
    if (!clean.empty() && kSanPieceRev.contains(clean.front())) {
        piece_type = kSanPieceRev.at(clean.front());
        clean.erase(clean.begin());
    }

    std::optional<int> from_file;
    std::optional<int> from_rank;
    if (clean.size() == 2) {
        from_file = clean[0] - 'a';
        from_rank = clean[1] - '1';
    } else if (clean.size() == 1) {
        if (std::isalpha(static_cast<unsigned char>(clean[0])) != 0) {
            from_file = clean[0] - 'a';
        } else {
            from_rank = clean[0] - '1';
        }
    }

    std::vector<Move> candidates;
    for (const Move& m : legal) {
        const Piece p = position.board().piece_at(m.from_sq);
        if (p.type != piece_type) {
            continue;
        }
        if (m.to_sq != to_sq) {
            continue;
        }
        if (promotion != PieceType::None && m.promotion != promotion) {
            continue;
        }
        if (from_file.has_value() && file_of(m.from_sq) != *from_file) {
            continue;
        }
        if (from_rank.has_value() && rank_of(m.from_sq) != *from_rank) {
            continue;
        }
        candidates.push_back(m);
    }

    if (candidates.size() == 1) {
        return candidates.front();
    }
    if (candidates.empty()) {
        throw std::invalid_argument(std::string("Illegal move: ") + std::string(san));
    }
    throw std::invalid_argument(std::string("Ambiguous move: ") + std::string(san));
}

}  // namespace chessie
