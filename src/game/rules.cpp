#include <chessie/game/rules.hpp>

#include <chessie/bitboard.hpp>
#include <chessie/movegen.hpp>

namespace chessie {

bool Rules::is_in_check(const Position& position) {
    return position.is_in_check(position.side_to_move());
}

bool Rules::is_checkmate(Position& position) {
    if (!is_in_check(position)) {
        return false;
    }
    return movegen::legal(position).empty();
}

bool Rules::is_stalemate(Position& position) {
    if (is_in_check(position)) {
        return false;
    }
    return movegen::legal(position).empty();
}

bool Rules::is_insufficient_material(const Position& position) {
    const Board& board = position.board();
    const Bitboard white_occ = board.occupied(Color::White);
    const Bitboard black_occ = board.occupied(Color::Black);
    const int total = popcount(white_occ | black_occ);

    if (total == 2) {
        return true;
    }

    if (total == 3) {
        return board.pieces(Color::White, PieceType::Knight) != 0 ||
               board.pieces(Color::White, PieceType::Bishop) != 0 ||
               board.pieces(Color::Black, PieceType::Knight) != 0 ||
               board.pieces(Color::Black, PieceType::Bishop) != 0;
    }

    if (total == 4) {
        const Bitboard wb = board.pieces(Color::White, PieceType::Bishop);
        const Bitboard bb = board.pieces(Color::Black, PieceType::Bishop);
        if (popcount(wb) == 1 && popcount(bb) == 1) {
            const Square w_sq = lsb(wb);
            const Square b_sq = lsb(bb);
            const int w_color = (file_of(w_sq) + rank_of(w_sq)) % 2;
            const int b_color = (file_of(b_sq) + rank_of(b_sq)) % 2;
            return w_color == b_color;
        }
    }

    return false;
}

bool Rules::is_fifty_move_rule(const Position& position) {
    return position.halfmove_clock() >= 100;
}

bool Rules::is_seventy_five_move_rule(const Position& position) {
    return position.halfmove_clock() >= 150;
}

bool Rules::is_threefold_repetition(const Position& position) {
    return position.repetition_count() >= 3;
}

bool Rules::is_fivefold_repetition(const Position& position) {
    return position.repetition_count() >= 5;
}

bool Rules::is_claimable_draw(const Position& position) {
    return is_fifty_move_rule(position) || is_threefold_repetition(position);
}

bool Rules::is_automatic_draw(const Position& position) {
    return is_insufficient_material(position) || is_seventy_five_move_rule(position) ||
           is_fivefold_repetition(position);
}

GameResult Rules::game_result(Position& position) {
    const MoveList legal_moves = movegen::legal(position);

    if (legal_moves.empty()) {
        if (position.is_in_check(position.side_to_move())) {
            return position.side_to_move() == Color::White ? GameResult::BlackWins
                                                           : GameResult::WhiteWins;
        }
        return GameResult::Draw;
    }

    if (is_automatic_draw(position)) {
        return GameResult::Draw;
    }

    return GameResult::InProgress;
}

}  // namespace chessie
