#include <chessie/board.hpp>

#include <gtest/gtest.h>

using namespace chessie;

// ── Board::initial() ────────────────────────────────────────────────────────

TEST(Board, InitialPieceAt) {
    Board b = Board::initial();

    // White pieces
    EXPECT_EQ(b.piece_at(A1), Piece(Color::White, PieceType::Rook));
    EXPECT_EQ(b.piece_at(B1), Piece(Color::White, PieceType::Knight));
    EXPECT_EQ(b.piece_at(C1), Piece(Color::White, PieceType::Bishop));
    EXPECT_EQ(b.piece_at(D1), Piece(Color::White, PieceType::Queen));
    EXPECT_EQ(b.piece_at(E1), Piece(Color::White, PieceType::King));
    EXPECT_EQ(b.piece_at(F1), Piece(Color::White, PieceType::Bishop));
    EXPECT_EQ(b.piece_at(G1), Piece(Color::White, PieceType::Knight));
    EXPECT_EQ(b.piece_at(H1), Piece(Color::White, PieceType::Rook));

    // White pawns
    for (int f = 0; f < 8; ++f) {
        Square sq = make_square(f, 1);
        EXPECT_EQ(b.piece_at(sq), Piece(Color::White, PieceType::Pawn));
    }

    // Black pieces
    EXPECT_EQ(b.piece_at(A8), Piece(Color::Black, PieceType::Rook));
    EXPECT_EQ(b.piece_at(B8), Piece(Color::Black, PieceType::Knight));
    EXPECT_EQ(b.piece_at(C8), Piece(Color::Black, PieceType::Bishop));
    EXPECT_EQ(b.piece_at(D8), Piece(Color::Black, PieceType::Queen));
    EXPECT_EQ(b.piece_at(E8), Piece(Color::Black, PieceType::King));
    EXPECT_EQ(b.piece_at(F8), Piece(Color::Black, PieceType::Bishop));
    EXPECT_EQ(b.piece_at(G8), Piece(Color::Black, PieceType::Knight));
    EXPECT_EQ(b.piece_at(H8), Piece(Color::Black, PieceType::Rook));

    // Black pawns
    for (int f = 0; f < 8; ++f) {
        Square sq = make_square(f, 6);
        EXPECT_EQ(b.piece_at(sq), Piece(Color::Black, PieceType::Pawn));
    }
}

TEST(Board, InitialEmptySquares) {
    Board b = Board::initial();

    // Ranks 3-6 (indices 2-5) should be empty
    for (int r = 2; r <= 5; ++r) {
        for (int f = 0; f < 8; ++f) {
            Square sq = make_square(f, r);
            EXPECT_EQ(b.piece_at(sq), kNoPiece) << "Expected empty at " << square_name(sq);
        }
    }
}

TEST(Board, InitialKingSquares) {
    Board b = Board::initial();
    EXPECT_EQ(b.king_square(Color::White), E1);
    EXPECT_EQ(b.king_square(Color::Black), E8);
}

TEST(Board, InitialOccupancy) {
    Board b = Board::initial();

    // White has 16 pieces on ranks 1 and 2
    EXPECT_EQ(popcount(b.occupied(Color::White)), 16);
    // Black has 16 pieces on ranks 7 and 8
    EXPECT_EQ(popcount(b.occupied(Color::Black)), 16);
    // Total
    EXPECT_EQ(popcount(b.occupied_all()), 32);
}

TEST(Board, InitialPawnBitboard) {
    Board b = Board::initial();

    Bitboard white_pawns = b.pieces(Color::White, PieceType::Pawn);
    EXPECT_EQ(popcount(white_pawns), 8);
    // All white pawns on rank 2 (mask = 0xFF00)
    EXPECT_EQ(white_pawns, static_cast<Bitboard>(0xFF00ULL));

    Bitboard black_pawns = b.pieces(Color::Black, PieceType::Pawn);
    EXPECT_EQ(popcount(black_pawns), 8);
    // All black pawns on rank 7 (mask = 0x00FF000000000000)
    EXPECT_EQ(black_pawns, static_cast<Bitboard>(0x00FF000000000000ULL));
}

// ── put_piece / remove_piece / move_piece ───────────────────────────────────

TEST(Board, PutPiece) {
    Board b;
    b.put_piece(E4, Piece(Color::White, PieceType::Knight));

    EXPECT_EQ(b.piece_at(E4), Piece(Color::White, PieceType::Knight));
    EXPECT_TRUE(test_bit(b.pieces(Color::White, PieceType::Knight), E4));
    EXPECT_TRUE(test_bit(b.occupied(Color::White), E4));
    EXPECT_TRUE(test_bit(b.occupied_all(), E4));
}

TEST(Board, RemovePiece) {
    Board b;
    b.put_piece(E4, Piece(Color::White, PieceType::Knight));
    b.remove_piece(E4);

    EXPECT_EQ(b.piece_at(E4), kNoPiece);
    EXPECT_FALSE(test_bit(b.pieces(Color::White, PieceType::Knight), E4));
    EXPECT_FALSE(test_bit(b.occupied(Color::White), E4));
    EXPECT_FALSE(test_bit(b.occupied_all(), E4));
}

TEST(Board, MovePiece) {
    Board b;
    b.put_piece(D1, Piece(Color::Black, PieceType::Queen));
    b.move_piece(D1, D5);

    EXPECT_EQ(b.piece_at(D1), kNoPiece);
    EXPECT_EQ(b.piece_at(D5), Piece(Color::Black, PieceType::Queen));
    EXPECT_FALSE(test_bit(b.occupied_all(), D1));
    EXPECT_TRUE(test_bit(b.occupied_all(), D5));
}

// ── Bitboard consistency ────────────────────────────────────────────────────

TEST(Board, MailboxBitboardConsistency) {
    Board b = Board::initial();

    for (int sq = 0; sq < 64; ++sq) {
        Square s = static_cast<Square>(sq);
        Piece p = b.piece_at(s);
        if (p != kNoPiece) {
            EXPECT_TRUE(test_bit(b.pieces(p.color, p.type), s))
                << "Bitboard missing piece at " << square_name(s);
            EXPECT_TRUE(test_bit(b.occupied(p.color), s));
            EXPECT_TRUE(test_bit(b.occupied_all(), s));
        } else {
            EXPECT_FALSE(test_bit(b.occupied_all(), s))
                << "Occupied but mailbox empty at " << square_name(s);
        }
    }
}
