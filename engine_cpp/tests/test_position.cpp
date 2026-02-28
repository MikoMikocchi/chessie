#include <chessie/magic.hpp>
#include <chessie/position.hpp>

#include <gtest/gtest.h>

using namespace chessie;

// ── Test fixture: init magic once ──────────────────────────────────────────

class PositionTest : public ::testing::Test {
   protected:
    static void SetUpTestSuite() { magic::init(); }
};

// ── FEN parsing ─────────────────────────────────────────────────────────────

TEST_F(PositionTest, StartingFen) {
    Position pos = Position::initial();
    EXPECT_EQ(pos.to_fen(), kStartingFen);
}

TEST_F(PositionTest, FenRoundTrip) {
    // Kiwipete
    std::string fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    Position pos = Position::from_fen(fen);
    EXPECT_EQ(pos.to_fen(), fen);
}

TEST_F(PositionTest, FenWithEP) {
    std::string fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1";
    Position pos = Position::from_fen(fen);
    EXPECT_EQ(pos.to_fen(), fen);
    EXPECT_EQ(pos.en_passant(), E3);
    EXPECT_EQ(pos.side_to_move(), Color::Black);
}

TEST_F(PositionTest, FenMinimalFields) {
    // Only 4 mandatory fields
    Position pos = Position::from_fen("8/8/8/8/8/8/8/4K2k w - -");
    EXPECT_EQ(pos.side_to_move(), Color::White);
    EXPECT_EQ(pos.castling(), kCastlingNone);
    EXPECT_EQ(pos.en_passant(), kNoSquare);
    EXPECT_EQ(pos.halfmove_clock(), 0);
    EXPECT_EQ(pos.fullmove_number(), 1);
}

TEST_F(PositionTest, FenInvalidThrows) {
    EXPECT_THROW((void)Position::from_fen(""), std::invalid_argument);
    EXPECT_THROW((void)Position::from_fen("not a fen"), std::invalid_argument);
    EXPECT_THROW((void)Position::from_fen("8/8/8 w KQkq -"), std::invalid_argument);
}

TEST_F(PositionTest, InitialPosition) {
    Position pos = Position::initial();
    EXPECT_EQ(pos.side_to_move(), Color::White);
    EXPECT_EQ(pos.castling(), kCastlingAll);
    EXPECT_EQ(pos.en_passant(), kNoSquare);
    EXPECT_EQ(pos.halfmove_clock(), 0);
    EXPECT_EQ(pos.fullmove_number(), 1);
    EXPECT_EQ(pos.board().piece_at(E1), Piece(Color::White, PieceType::King));
    EXPECT_EQ(pos.board().piece_at(E8), Piece(Color::Black, PieceType::King));
}

// ── Make / Unmake: basic pawn move ──────────────────────────────────────────

TEST_F(PositionTest, MakeUnmakeNormalPawnMove) {
    Position pos = Position::initial();
    std::string original_fen = pos.to_fen();
    std::uint64_t original_key = pos.key();

    // e2-e3 (single step, Normal flag)
    Move m{E2, E3, MoveFlag::Normal, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(E2), kNoPiece);
    EXPECT_EQ(pos.board().piece_at(E3), Piece(Color::White, PieceType::Pawn));
    EXPECT_EQ(pos.side_to_move(), Color::Black);
    EXPECT_EQ(pos.en_passant(), kNoSquare);
    EXPECT_EQ(pos.halfmove_clock(), 0);  // pawn move resets

    pos.unmake_move(m);

    EXPECT_EQ(pos.to_fen(), original_fen);
    EXPECT_EQ(pos.key(), original_key);
}

// ── Double pawn push + en passant ───────────────────────────────────────────

TEST_F(PositionTest, DoublePawnPushSetsEP) {
    Position pos = Position::initial();

    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.en_passant(), E3);
    EXPECT_EQ(pos.board().piece_at(E4), Piece(Color::White, PieceType::Pawn));
    EXPECT_EQ(pos.board().piece_at(E2), kNoPiece);
}

TEST_F(PositionTest, EnPassantCapture) {
    // Set up: White pawn on e5, Black pawn on d5, EP on d6
    Position pos = Position::from_fen("8/8/8/3pP3/8/8/8/4K2k w - d6 0 1");

    // e5xd6 en passant
    Move m{E5, D6, MoveFlag::EnPassant, PieceType::None};
    std::string original_fen = pos.to_fen();
    std::uint64_t original_key = pos.key();

    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(E5), kNoPiece);
    EXPECT_EQ(pos.board().piece_at(D5), kNoPiece);  // captured pawn removed
    EXPECT_EQ(pos.board().piece_at(D6), Piece(Color::White, PieceType::Pawn));

    pos.unmake_move(m);

    EXPECT_EQ(pos.to_fen(), original_fen);
    EXPECT_EQ(pos.key(), original_key);
}

// ── Castling ────────────────────────────────────────────────────────────────

TEST_F(PositionTest, CastleKingside) {
    Position pos = Position::from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");
    std::string original_fen = pos.to_fen();
    std::uint64_t original_key = pos.key();

    Move m{E1, G1, MoveFlag::CastleKingside, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(G1), Piece(Color::White, PieceType::King));
    EXPECT_EQ(pos.board().piece_at(F1), Piece(Color::White, PieceType::Rook));
    EXPECT_EQ(pos.board().piece_at(E1), kNoPiece);
    EXPECT_EQ(pos.board().piece_at(H1), kNoPiece);
    // White castling rights removed
    EXPECT_EQ(pos.castling() & kWhiteBoth, kCastlingNone);
    // Black castling rights preserved
    EXPECT_EQ(pos.castling() & kBlackBoth, kBlackBoth);

    pos.unmake_move(m);
    EXPECT_EQ(pos.to_fen(), original_fen);
    EXPECT_EQ(pos.key(), original_key);
}

TEST_F(PositionTest, CastleQueenside) {
    Position pos = Position::from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");

    Move m{E1, C1, MoveFlag::CastleQueenside, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(C1), Piece(Color::White, PieceType::King));
    EXPECT_EQ(pos.board().piece_at(D1), Piece(Color::White, PieceType::Rook));
    EXPECT_EQ(pos.board().piece_at(E1), kNoPiece);
    EXPECT_EQ(pos.board().piece_at(A1), kNoPiece);
}

// ── Promotion ───────────────────────────────────────────────────────────────

TEST_F(PositionTest, PromotionToQueen) {
    Position pos = Position::from_fen("8/4P3/8/8/8/8/8/4K2k w - - 0 1");
    std::string original_fen = pos.to_fen();
    std::uint64_t original_key = pos.key();

    Move m{E7, E8, MoveFlag::Promotion, PieceType::Queen};
    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(E8), Piece(Color::White, PieceType::Queen));
    EXPECT_EQ(pos.board().piece_at(E7), kNoPiece);

    pos.unmake_move(m);
    EXPECT_EQ(pos.to_fen(), original_fen);
    EXPECT_EQ(pos.key(), original_key);
}

TEST_F(PositionTest, PromotionToKnight) {
    Position pos = Position::from_fen("8/4P3/8/8/8/8/8/4K2k w - - 0 1");

    Move m{E7, E8, MoveFlag::Promotion, PieceType::Knight};
    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(E8), Piece(Color::White, PieceType::Knight));
}

// ── Capture ─────────────────────────────────────────────────────────────────

TEST_F(PositionTest, NormalCapture) {
    Position pos =
        Position::from_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2");
    std::string original_fen = pos.to_fen();
    std::uint64_t original_key = pos.key();

    // e4xd5
    Move m{E4, D5, MoveFlag::Normal, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.board().piece_at(D5), Piece(Color::White, PieceType::Pawn));
    EXPECT_EQ(pos.board().piece_at(E4), kNoPiece);
    EXPECT_EQ(pos.halfmove_clock(), 0);  // pawn move + capture

    pos.unmake_move(m);
    EXPECT_EQ(pos.to_fen(), original_fen);
    EXPECT_EQ(pos.key(), original_key);
}

// ── Castling rights updates ─────────────────────────────────────────────────

TEST_F(PositionTest, KingMoveRemovesBothRights) {
    Position pos = Position::from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");

    // King move (not castle) e1-d1
    Move m{E1, D1, MoveFlag::Normal, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.castling() & kWhiteBoth, kCastlingNone);
    EXPECT_EQ(pos.castling() & kBlackBoth, kBlackBoth);  // preserved
}

TEST_F(PositionTest, RookMoveRemovesOneRight) {
    Position pos = Position::from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");

    // Rook a1-a2
    Move m{A1, A2, MoveFlag::Normal, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.castling() & kWhiteQueenside, kCastlingNone);  // removed
    EXPECT_EQ(pos.castling() & kWhiteKingside, kWhiteKingside);  // preserved
}

TEST_F(PositionTest, CaptureOnRookSquareRemovesRight) {
    // Black rook on h8, white bishop captures it
    Position pos =
        Position::from_fen("r3k2r/pppppppp/6B1/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");

    // Bxh8 (captures black rook on kingside)
    Move m{G6, H8, MoveFlag::Normal, PieceType::None};
    pos.make_move(m);

    EXPECT_EQ(pos.castling() & kBlackKingside, kCastlingNone);   // removed
    EXPECT_EQ(pos.castling() & kBlackQueenside, kBlackQueenside);  // preserved
}

// ── Zobrist consistency ─────────────────────────────────────────────────────

TEST_F(PositionTest, ZobristIncrementalMatchesFull) {
    Position pos = Position::initial();

    // Make several moves
    Move e2e4{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    Move e7e5{E7, E5, MoveFlag::DoublePawn, PieceType::None};
    Move g1f3{G1, F3, MoveFlag::Normal, PieceType::None};

    pos.make_move(e2e4);
    // Verify incremental key matches full computation
    Position verify1 = Position::from_fen(pos.to_fen());
    EXPECT_EQ(pos.key(), verify1.key());

    pos.make_move(e7e5);
    Position verify2 = Position::from_fen(pos.to_fen());
    EXPECT_EQ(pos.key(), verify2.key());

    pos.make_move(g1f3);
    Position verify3 = Position::from_fen(pos.to_fen());
    EXPECT_EQ(pos.key(), verify3.key());
}

TEST_F(PositionTest, ZobristMakeUnmakeIdentity) {
    Position pos = Position::initial();
    std::uint64_t original = pos.key();

    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    pos.make_move(m);
    EXPECT_NE(pos.key(), original);  // key should change
    pos.unmake_move(m);
    EXPECT_EQ(pos.key(), original);  // key restored
}

// ── Halfmove clock ──────────────────────────────────────────────────────────

TEST_F(PositionTest, HalfmoveClockNonPawnNonCapture) {
    Position pos = Position::from_fen(
        "r1bqkbnr/pppppppp/2n5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2");

    EXPECT_EQ(pos.halfmove_clock(), 1);

    // Knight move (not pawn, not capture) → increment
    Move m{G1, F3, MoveFlag::Normal, PieceType::None};
    pos.make_move(m);
    EXPECT_EQ(pos.halfmove_clock(), 2);
}

TEST_F(PositionTest, HalfmoveClockResetOnPawnMove) {
    Position pos = Position::from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 5 3");

    Move m{E2, E4, MoveFlag::DoublePawn, PieceType::None};
    pos.make_move(m);
    EXPECT_EQ(pos.halfmove_clock(), 0);
}

// ── Fullmove number ─────────────────────────────────────────────────────────

TEST_F(PositionTest, FullmoveIncrements) {
    Position pos = Position::initial();
    EXPECT_EQ(pos.fullmove_number(), 1);

    // White move
    pos.make_move({E2, E4, MoveFlag::DoublePawn, PieceType::None});
    EXPECT_EQ(pos.fullmove_number(), 1);  // Only increments after Black's move

    // Black move
    pos.make_move({E7, E5, MoveFlag::DoublePawn, PieceType::None});
    EXPECT_EQ(pos.fullmove_number(), 2);  // Now 2
}

// ── Attack queries ──────────────────────────────────────────────────────────

TEST_F(PositionTest, IsInCheckStarting) {
    Position pos = Position::initial();
    EXPECT_FALSE(pos.is_in_check());
}

TEST_F(PositionTest, IsInCheckScholar) {
    // White Qf7 checking Black king on e8
    Position pos = Position::from_fen("rnbqkb1r/pppp1Qpp/5n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4");
    EXPECT_TRUE(pos.is_in_check());
    EXPECT_TRUE(pos.is_in_check(Color::Black));
    EXPECT_FALSE(pos.is_in_check(Color::White));
}

TEST_F(PositionTest, IsSquareAttacked) {
    Position pos = Position::initial();

    // e2 pawn attacks d3 and f3
    EXPECT_TRUE(pos.is_square_attacked(D3, Color::White));
    EXPECT_TRUE(pos.is_square_attacked(F3, Color::White));

    // d7 pawn attacks c6 and e6
    EXPECT_TRUE(pos.is_square_attacked(C6, Color::Black));
    EXPECT_TRUE(pos.is_square_attacked(E6, Color::Black));

    // e4 is not attacked by anyone in starting position
    EXPECT_FALSE(pos.is_square_attacked(E4, Color::White));
    EXPECT_FALSE(pos.is_square_attacked(E4, Color::Black));

    // Knight on b1 attacks a3 and c3
    EXPECT_TRUE(pos.is_square_attacked(A3, Color::White));
    EXPECT_TRUE(pos.is_square_attacked(C3, Color::White));
}

// ── Repetition ──────────────────────────────────────────────────────────────

TEST_F(PositionTest, RepetitionCount) {
    Position pos = Position::initial();
    EXPECT_EQ(pos.repetition_count(), 1);  // initial position counts once

    // Nf3, Nc6, Ng1, Nb8 — returns to starting position
    pos.make_move({G1, F3, MoveFlag::Normal, PieceType::None});
    pos.make_move({B8, C6, MoveFlag::Normal, PieceType::None});
    pos.make_move({F3, G1, MoveFlag::Normal, PieceType::None});
    pos.make_move({C6, B8, MoveFlag::Normal, PieceType::None});

    EXPECT_EQ(pos.repetition_count(), 2);  // position occurred twice now
}

// ── Multi-move sequence ─────────────────────────────────────────────────────

TEST_F(PositionTest, MultiMoveUnmake) {
    Position pos = Position::initial();
    std::string original_fen = pos.to_fen();
    std::uint64_t original_key = pos.key();

    Move moves[] = {
        {E2, E4, MoveFlag::DoublePawn, PieceType::None},
        {E7, E5, MoveFlag::DoublePawn, PieceType::None},
        {G1, F3, MoveFlag::Normal, PieceType::None},
        {B8, C6, MoveFlag::Normal, PieceType::None},
    };

    for (auto& m : moves) {
        pos.make_move(m);
    }

    // Unmake in reverse order
    for (int i = 3; i >= 0; --i) {
        pos.unmake_move(moves[i]);
    }

    EXPECT_EQ(pos.to_fen(), original_fen);
    EXPECT_EQ(pos.key(), original_key);
}
