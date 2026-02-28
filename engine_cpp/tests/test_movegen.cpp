/// @file test_movegen.cpp
/// Unit tests for move generation.

#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>
#include <chessie/position.hpp>

#include <gtest/gtest.h>

#include <algorithm>
#include <string>
#include <vector>

using namespace chessie;

// ── Fixture with magic init ─────────────────────────────────────────────────

class MoveGenTest : public ::testing::Test {
   public:
    static void SetUpTestSuite() { magic::init(); }
};

// Helper: check that a specific UCI move is present among legal moves.
static bool has_move(Position& pos, const std::string& uci_str) {
    MoveList ml = movegen::legal(pos);
    for (const Move& m : ml) {
        if (m.uci() == uci_str) return true;
    }
    return false;
}

// ── Starting position ───────────────────────────────────────────────────────

TEST_F(MoveGenTest, StartingPosHas20LegalMoves) {
    auto pos = Position::initial();
    MoveList ml = movegen::legal(pos);
    EXPECT_EQ(ml.size(), 20);
}

TEST_F(MoveGenTest, StartingPosHas20PseudoLegalMoves) {
    auto pos = Position::initial();
    MoveList ml = movegen::pseudo_legal(pos);
    // In starting position, all pseudo-legal moves are legal.
    EXPECT_EQ(ml.size(), 20);
}

// ── Pawn moves ──────────────────────────────────────────────────────────────

TEST_F(MoveGenTest, PawnSinglePush) {
    auto pos = Position::initial();
    EXPECT_TRUE(has_move(pos, "e2e3"));
    EXPECT_TRUE(has_move(pos, "a2a3"));
}

TEST_F(MoveGenTest, PawnDoublePush) {
    auto pos = Position::initial();
    EXPECT_TRUE(has_move(pos, "e2e4"));
    EXPECT_TRUE(has_move(pos, "d2d4"));
}

TEST_F(MoveGenTest, PawnCapture) {
    // White pawn on e4, black pawn on d5 — e4xd5 should be legal.
    auto pos = Position::from_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2");
    EXPECT_TRUE(has_move(pos, "e4d5"));
}

TEST_F(MoveGenTest, EnPassant) {
    // White pawn on e5, black just played d7-d5 → ep square d6.
    auto pos =
        Position::from_fen("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3");
    EXPECT_TRUE(has_move(pos, "e5d6"));
}

TEST_F(MoveGenTest, EnPassantBlack) {
    // Black pawn on d4, white just played e2-e4 → ep square e3.
    auto pos =
        Position::from_fen("rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 2");
    EXPECT_TRUE(has_move(pos, "d4e3"));
}

// ── Promotion ───────────────────────────────────────────────────────────────

TEST_F(MoveGenTest, PawnPromotion) {
    // White pawn on a7, no pieces blocking a8.
    auto pos = Position::from_fen("8/P7/8/8/8/8/6k1/4K3 w - - 0 1");
    EXPECT_TRUE(has_move(pos, "a7a8q"));
    EXPECT_TRUE(has_move(pos, "a7a8r"));
    EXPECT_TRUE(has_move(pos, "a7a8b"));
    EXPECT_TRUE(has_move(pos, "a7a8n"));
}

TEST_F(MoveGenTest, PawnPromotionCapture) {
    // White pawn on a7, black rook on b8.
    auto pos = Position::from_fen("1r6/P7/8/8/8/8/6k1/4K3 w - - 0 1");
    EXPECT_TRUE(has_move(pos, "a7b8q"));
    EXPECT_TRUE(has_move(pos, "a7b8r"));
    EXPECT_TRUE(has_move(pos, "a7b8b"));
    EXPECT_TRUE(has_move(pos, "a7b8n"));
}

TEST_F(MoveGenTest, BlackPawnPromotion) {
    // Black pawn on h2, no blocking on h1.
    auto pos = Position::from_fen("4k3/8/8/8/8/8/6Kp/8 b - - 0 1");
    EXPECT_TRUE(has_move(pos, "h2h1q"));
    EXPECT_TRUE(has_move(pos, "h2h1r"));
    EXPECT_TRUE(has_move(pos, "h2h1b"));
    EXPECT_TRUE(has_move(pos, "h2h1n"));
}

// ── Knight ──────────────────────────────────────────────────────────────────

TEST_F(MoveGenTest, KnightMoves) {
    auto pos = Position::initial();
    EXPECT_TRUE(has_move(pos, "b1a3"));
    EXPECT_TRUE(has_move(pos, "b1c3"));
    EXPECT_TRUE(has_move(pos, "g1f3"));
    EXPECT_TRUE(has_move(pos, "g1h3"));
}

// ── King & castling ─────────────────────────────────────────────────────────

TEST_F(MoveGenTest, CastlingKingside) {
    // White can castle kingside: clear f1 and g1.
    auto pos =
        Position::from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");
    EXPECT_TRUE(has_move(pos, "e1g1"));
}

TEST_F(MoveGenTest, CastlingQueenside) {
    auto pos =
        Position::from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1");
    EXPECT_TRUE(has_move(pos, "e1c1"));
}

TEST_F(MoveGenTest, CastlingBlockByPiece) {
    // Standard starting position: can't castle (f1/g1 occupied).
    auto pos = Position::initial();
    EXPECT_FALSE(has_move(pos, "e1g1"));
    EXPECT_FALSE(has_move(pos, "e1c1"));
}

TEST_F(MoveGenTest, CastlingBlockedByCheck) {
    // King in check — can't castle.
    auto pos =
        Position::from_fen("r3k2r/pppp1ppp/8/4q3/8/8/PPPP1PPP/R3K2R w KQkq - 0 1");
    // Black queen on e5 attacks e1 — so king is in check.
    // Actually let me verify: e5 queen attacks e1 through e2. But e2 has a pawn.
    // Let me use a position where king IS in check.
    auto pos2 =
        Position::from_fen("r3k2r/pppppppp/8/8/1b6/8/PPPPPPPP/R3K2R w KQkq - 0 1");
    // Bishop on b4 attacks e1? No, d2 pawn blocks.
    // Use a direct check position.
    auto pos3 =
        Position::from_fen("r3k2r/pppppppp/8/8/8/4q3/PPPPPPPP/R3K2R w KQkq - 0 1");
    // e3 queen doesn't attack e1 because e2 pawn blocks.
    // Let me construct a proper check position.
    auto pos4 =
        Position::from_fen("4k3/8/8/8/8/8/8/R3K2r w Q - 0 1");
    // Black rook on h1 gives check to white king on e1.
    EXPECT_TRUE(pos4.is_in_check());
    EXPECT_FALSE(has_move(pos4, "e1c1"));
}

TEST_F(MoveGenTest, CastlingThroughAttack) {
    // White can't castle kingside if f1 is attacked.
    auto pos =
        Position::from_fen("4k3/8/8/8/5b2/8/8/R3K2R w KQ - 0 1");
    // Bishop on f4 attacks... let me check. f4 bishop goes diag to c1, e3, g5, h6 and also e5, d6, c7, b8.
    // f4 doesn't directly attack f1. Let me use a different setup.
    auto pos2 =
        Position::from_fen("4k3/8/8/8/8/5n2/8/R3K2R w KQ - 0 1");
    // Knight on f3 attacks e1? No. Attacks d2, d4, e5, g5, h4, h2, g1, e1. YES, attacks e1.
    // So king would be in check — not quite what we want. We want f1 attacked.
    auto pos3 =
        Position::from_fen("4k3/8/8/8/8/8/5r2/R3K2R w KQ - 0 1");
    // Rook on f2 attacks f1. So kingside castling through attacked f1 is illegal.
    EXPECT_FALSE(has_move(pos3, "e1g1"));
    // Queenside should still be legal if c1, d1 not attacked.
    EXPECT_TRUE(has_move(pos3, "e1c1"));
}

// ── Check evasion ───────────────────────────────────────────────────────────

TEST_F(MoveGenTest, CheckEvasionKingMoves) {
    // King in check — must escape.
    auto pos = Position::from_fen("4k3/8/8/8/8/8/8/R3K2r w Q - 0 1");
    MoveList ml = movegen::legal(pos);
    // All legal moves should be king moves or blocking/capturing.
    EXPECT_GT(ml.size(), 0);
    // King can't stay on e1 (in check), can't castle.
    EXPECT_FALSE(has_move(pos, "e1c1"));
}

TEST_F(MoveGenTest, Stalemate) {
    // Stalemate position: black king on a8, white queen on b6, white king on a6.
    // Actually let's use a known stalemate: Ka1, Qc2, ka8 — nope.
    // Black king on a8, white queen on c7, white king on b6.
    // a7 attacked by Qc7 (rank 7) & Kb6. b8 attacked by Qc7 (diagonal). b7 attacked by both.
    auto pos = Position::from_fen("k7/2Q5/1K6/8/8/8/8/8 b - - 0 1");
    MoveList ml = movegen::legal(pos);
    EXPECT_EQ(ml.size(), 0);
    EXPECT_FALSE(pos.is_in_check());  // Not checkmate — stalemate.
}

TEST_F(MoveGenTest, Checkmate) {
    // Scholar's mate final position.
    auto pos =
        Position::from_fen("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4");
    MoveList ml = movegen::legal(pos);
    EXPECT_EQ(ml.size(), 0);
    EXPECT_TRUE(pos.is_in_check());
}

// ── Sliding pieces ──────────────────────────────────────────────────────────

TEST_F(MoveGenTest, BishopMoves) {
    // Bishop on e4, no other pieces except kings.
    auto pos = Position::from_fen("4k3/8/8/8/4B3/8/8/4K3 w - - 0 1");
    MoveList ml = movegen::legal(pos);
    // Bishop on e4: 13 squares on diagonals. King on e1: 5 moves (d1,d2,f1,f2,e2).
    // But some king moves may be restricted. Let me just check bishop has 13 moves.
    int bishop_moves = 0;
    for (const Move& m : ml) {
        if (m.from_sq == E4) ++bishop_moves;
    }
    EXPECT_EQ(bishop_moves, 13);
}

TEST_F(MoveGenTest, RookMoves) {
    // Rook on a1, no other pieces except kings.
    auto pos = Position::from_fen("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1");
    MoveList ml = movegen::legal(pos);
    // Rook on a1: can go a2-a8 (7) + b1-d1 (3) = 10 moves (e1 blocked by king).
    int rook_moves = 0;
    for (const Move& m : ml) {
        if (m.from_sq == A1) ++rook_moves;
    }
    EXPECT_EQ(rook_moves, 10);
}

TEST_F(MoveGenTest, QueenMoves) {
    // Queen on d4, only kings present.
    auto pos = Position::from_fen("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1");
    MoveList ml = movegen::legal(pos);
    int queen_moves = 0;
    for (const Move& m : ml) {
        if (m.from_sq == D4) ++queen_moves;
    }
    // Queen on d4 in an open board: 27 squares.
    EXPECT_EQ(queen_moves, 27);
}

// ── Captures-only generation ────────────────────────────────────────────────

TEST_F(MoveGenTest, CapturesOnlyBasic) {
    auto pos = Position::initial();
    MoveList ml = movegen::captures(pos);
    // Starting position: no captures or promotions possible.
    EXPECT_EQ(ml.size(), 0);
}

TEST_F(MoveGenTest, CapturesIncludesPawnCaptures) {
    auto pos = Position::from_fen("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2");
    MoveList ml = movegen::captures(pos);
    bool found_exd5 = false;
    for (const Move& m : ml) {
        if (m.uci() == "e4d5") found_exd5 = true;
    }
    EXPECT_TRUE(found_exd5);
}

// ── Pin handling ────────────────────────────────────────────────────────────

TEST_F(MoveGenTest, PinnedPieceCantMove) {
    // White knight on e2 pinned by black bishop on h5 (pin line h5-e2-king on e1).
    // Wait, that's not a valid pin. Let me make a proper one.
    // King on e1, knight on e2, rook on e8 — knight is pinned along the e-file.
    auto pos = Position::from_fen("4r1k1/8/8/8/8/8/4N3/4K3 w - - 0 1");
    // Knight on e2 is pinned by rook on e8 (through e-file).
    // Knight can't move without exposing king.
    bool knight_moves = false;
    MoveList ml = movegen::legal(pos);
    for (const Move& m : ml) {
        if (m.from_sq == E2) knight_moves = true;
    }
    EXPECT_FALSE(knight_moves);
}
