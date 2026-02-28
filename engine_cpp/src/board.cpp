/// @file board.cpp
/// Board implementation: initial position factory.

#include <chessie/board.hpp>

namespace chessie {

Board Board::initial() noexcept {
    Board b;

    // White pawns: rank 2
    for (int f = 0; f < 8; ++f) {
        b.put_piece(make_square(f, 1), {Color::White, PieceType::Pawn});
    }
    // Black pawns: rank 7
    for (int f = 0; f < 8; ++f) {
        b.put_piece(make_square(f, 6), {Color::Black, PieceType::Pawn});
    }

    // Back ranks
    constexpr PieceType kBackRank[] = {
        PieceType::Rook, PieceType::Knight, PieceType::Bishop, PieceType::Queen,
        PieceType::King, PieceType::Bishop, PieceType::Knight, PieceType::Rook,
    };

    for (int f = 0; f < 8; ++f) {
        b.put_piece(make_square(f, 0), {Color::White, kBackRank[f]});
        b.put_piece(make_square(f, 7), {Color::Black, kBackRank[f]});
    }

    return b;
}

}  // namespace chessie
