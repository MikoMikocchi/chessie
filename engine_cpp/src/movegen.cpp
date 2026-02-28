/// @file movegen.cpp
/// Move generation implementation using bitboard techniques.

#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>

namespace chessie::movegen {

namespace {

// ── Helpers ─────────────────────────────────────────────────────────────────

constexpr PieceType kPromotions[] = {PieceType::Queen, PieceType::Rook, PieceType::Bishop,
                                     PieceType::Knight};

void add_promotions(MoveList& ml, Square from, Square to) {
    for (PieceType pt : kPromotions) {
        ml.push({from, to, MoveFlag::Promotion, pt});
    }
}

// ── Pawn move generation ────────────────────────────────────────────────────

void gen_pawn_moves(const Position& pos, MoveList& ml) {
    const Color us = pos.side_to_move();
    const Color them = opposite(us);
    const Board& board = pos.board();
    const Bitboard pawns = board.pieces(us, PieceType::Pawn);
    const Bitboard empty = ~board.occupied_all();
    const Bitboard enemy = board.occupied(them);
    const Bitboard promo_rank = (us == Color::White) ? kRank8 : kRank1;

    // --- Single pushes ---
    Bitboard single =
        (us == Color::White) ? shift_north(pawns) & empty : shift_south(pawns) & empty;

    // Non-promotion pushes
    Bitboard np = single & ~promo_rank;
    while (np) {
        Square to = pop_lsb(np);
        auto from = static_cast<Square>((us == Color::White) ? to - 8 : to + 8);
        ml.push({from, to});
    }

    // Promotion pushes
    Bitboard pp = single & promo_rank;
    while (pp) {
        Square to = pop_lsb(pp);
        auto from = static_cast<Square>((us == Color::White) ? to - 8 : to + 8);
        add_promotions(ml, from, to);
    }

    // --- Double pushes ---
    // White: pawn on rank 2 pushes to rank 3 (single), then rank 4.
    // Black: pawn on rank 7 pushes to rank 6 (single), then rank 5.
    Bitboard mid_rank = (us == Color::White) ? kRank3 : kRank6;
    Bitboard dbl = (us == Color::White) ? shift_north(single & mid_rank) & empty
                                        : shift_south(single & mid_rank) & empty;
    while (dbl) {
        Square to = pop_lsb(dbl);
        auto from = static_cast<Square>((us == Color::White) ? to - 16 : to + 16);
        ml.push({from, to, MoveFlag::DoublePawn});
    }

    // --- Left captures (NW for White, SW for Black) ---
    Bitboard cap_l = ((us == Color::White) ? shift_nw(pawns) : shift_sw(pawns)) & enemy;

    Bitboard nc_l = cap_l & ~promo_rank;
    while (nc_l) {
        Square to = pop_lsb(nc_l);
        auto from = static_cast<Square>((us == Color::White) ? to - 7 : to + 9);
        ml.push({from, to});
    }
    Bitboard pc_l = cap_l & promo_rank;
    while (pc_l) {
        Square to = pop_lsb(pc_l);
        auto from = static_cast<Square>((us == Color::White) ? to - 7 : to + 9);
        add_promotions(ml, from, to);
    }

    // --- Right captures (NE for White, SE for Black) ---
    Bitboard cap_r = ((us == Color::White) ? shift_ne(pawns) : shift_se(pawns)) & enemy;

    Bitboard nc_r = cap_r & ~promo_rank;
    while (nc_r) {
        Square to = pop_lsb(nc_r);
        auto from = static_cast<Square>((us == Color::White) ? to - 9 : to + 7);
        ml.push({from, to});
    }
    Bitboard pc_r = cap_r & promo_rank;
    while (pc_r) {
        Square to = pop_lsb(pc_r);
        auto from = static_cast<Square>((us == Color::White) ? to - 9 : to + 7);
        add_promotions(ml, from, to);
    }

    // --- En passant ---
    if (pos.en_passant() != kNoSquare) {
        Square ep = pos.en_passant();
        // Squares from which our pawns attack the EP target.
        Bitboard ep_attackers = pawn_attacks(them, ep) & pawns;
        while (ep_attackers) {
            Square from = pop_lsb(ep_attackers);
            ml.push({from, ep, MoveFlag::EnPassant});
        }
    }
}

// ── Piece (non-pawn) move generation ────────────────────────────────────────

void gen_piece_moves(const Position& pos, MoveList& ml, PieceType pt) {
    const Color us = pos.side_to_move();
    const Board& board = pos.board();
    const Bitboard friendly = board.occupied(us);
    const Bitboard occ = board.occupied_all();
    Bitboard pieces = board.pieces(us, pt);

    while (pieces) {
        Square from = pop_lsb(pieces);
        Bitboard attacks = kEmptyBB;
        switch (pt) {
            case PieceType::Knight:
                attacks = knight_attacks(from);
                break;
            case PieceType::Bishop:
                attacks = magic::bishop_attacks(from, occ);
                break;
            case PieceType::Rook:
                attacks = magic::rook_attacks(from, occ);
                break;
            case PieceType::Queen:
                attacks = magic::queen_attacks(from, occ);
                break;
            case PieceType::King:
                attacks = king_attacks(from);
                break;
            default:
                break;
        }
        attacks &= ~friendly;
        while (attacks) {
            Square to = pop_lsb(attacks);
            ml.push({from, to});
        }
    }
}

// ── Castling generation ─────────────────────────────────────────────────────

void gen_castling(const Position& pos, MoveList& ml) {
    const Color us = pos.side_to_move();
    const Color them = opposite(us);
    const Board& board = pos.board();
    const Square king_sq = board.king_square(us);
    const int rank = (us == Color::White) ? 0 : 7;

    // Can't castle while in check
    if (pos.is_square_attacked(king_sq, them))
        return;

    // Kingside
    CastlingRights ks = (us == Color::White) ? kWhiteKingside : kBlackKingside;
    if (pos.castling() & ks) {
        Square f_sq = make_square(5, rank);
        Square g_sq = make_square(6, rank);
        if (board.is_empty(f_sq) && board.is_empty(g_sq) && !pos.is_square_attacked(f_sq, them) &&
            !pos.is_square_attacked(g_sq, them)) {
            ml.push({king_sq, g_sq, MoveFlag::CastleKingside});
        }
    }

    // Queenside
    CastlingRights qs = (us == Color::White) ? kWhiteQueenside : kBlackQueenside;
    if (pos.castling() & qs) {
        Square b_sq = make_square(1, rank);
        Square c_sq = make_square(2, rank);
        Square d_sq = make_square(3, rank);
        if (board.is_empty(b_sq) && board.is_empty(c_sq) && board.is_empty(d_sq) &&
            !pos.is_square_attacked(c_sq, them) && !pos.is_square_attacked(d_sq, them)) {
            ml.push({king_sq, c_sq, MoveFlag::CastleQueenside});
        }
    }
}

// ── Pawn captures + promotions only ─────────────────────────────────────────

void gen_pawn_captures(const Position& pos, MoveList& ml) {
    const Color us = pos.side_to_move();
    const Color them = opposite(us);
    const Board& board = pos.board();
    const Bitboard pawns = board.pieces(us, PieceType::Pawn);
    const Bitboard empty = ~board.occupied_all();
    const Bitboard enemy = board.occupied(them);
    const Bitboard promo_rank = (us == Color::White) ? kRank8 : kRank1;

    // Left captures
    Bitboard cap_l = ((us == Color::White) ? shift_nw(pawns) : shift_sw(pawns)) & enemy;
    while (cap_l) {
        Square to = pop_lsb(cap_l);
        auto from = static_cast<Square>((us == Color::White) ? to - 7 : to + 9);
        if (square_bb(to) & promo_rank) {
            add_promotions(ml, from, to);
        } else {
            ml.push({from, to});
        }
    }

    // Right captures
    Bitboard cap_r = ((us == Color::White) ? shift_ne(pawns) : shift_se(pawns)) & enemy;
    while (cap_r) {
        Square to = pop_lsb(cap_r);
        auto from = static_cast<Square>((us == Color::White) ? to - 9 : to + 7);
        if (square_bb(to) & promo_rank) {
            add_promotions(ml, from, to);
        } else {
            ml.push({from, to});
        }
    }

    // Non-capture promotions (important tactically)
    Bitboard single =
        (us == Color::White) ? shift_north(pawns) & empty : shift_south(pawns) & empty;
    Bitboard promo_push = single & promo_rank;
    while (promo_push) {
        Square to = pop_lsb(promo_push);
        auto from = static_cast<Square>((us == Color::White) ? to - 8 : to + 8);
        add_promotions(ml, from, to);
    }

    // En passant
    if (pos.en_passant() != kNoSquare) {
        Square ep = pos.en_passant();
        Bitboard ep_attackers = pawn_attacks(them, ep) & pawns;
        while (ep_attackers) {
            Square from = pop_lsb(ep_attackers);
            ml.push({from, ep, MoveFlag::EnPassant});
        }
    }
}

}  // anonymous namespace

// ── Public API ──────────────────────────────────────────────────────────────

MoveList pseudo_legal(const Position& pos) {
    MoveList ml;
    gen_pawn_moves(pos, ml);
    gen_piece_moves(pos, ml, PieceType::Knight);
    gen_piece_moves(pos, ml, PieceType::Bishop);
    gen_piece_moves(pos, ml, PieceType::Rook);
    gen_piece_moves(pos, ml, PieceType::Queen);
    gen_piece_moves(pos, ml, PieceType::King);
    gen_castling(pos, ml);
    return ml;
}

MoveList legal(Position& pos) {
    MoveList pseudo = pseudo_legal(pos);
    MoveList result;
    Color us = pos.side_to_move();

    for (const Move& m : pseudo) {
        pos.make_move(m);
        if (!pos.is_in_check(us)) {
            result.push(m);
        }
        pos.unmake_move(m);
    }
    return result;
}

MoveList captures(const Position& pos) {
    MoveList ml;
    const Color us = pos.side_to_move();
    const Board& board = pos.board();
    const Bitboard enemy = board.occupied(opposite(us));
    const Bitboard occ = board.occupied_all();

    // Pawn captures + promotions
    gen_pawn_captures(pos, ml);

    // Piece captures (only to enemy-occupied squares)
    for (PieceType pt : {PieceType::Knight, PieceType::Bishop, PieceType::Rook, PieceType::Queen,
                         PieceType::King}) {
        Bitboard pieces = board.pieces(us, pt);
        while (pieces) {
            Square from = pop_lsb(pieces);
            Bitboard attacks = kEmptyBB;
            switch (pt) {
                case PieceType::Knight:
                    attacks = knight_attacks(from);
                    break;
                case PieceType::Bishop:
                    attacks = magic::bishop_attacks(from, occ);
                    break;
                case PieceType::Rook:
                    attacks = magic::rook_attacks(from, occ);
                    break;
                case PieceType::Queen:
                    attacks = magic::queen_attacks(from, occ);
                    break;
                case PieceType::King:
                    attacks = king_attacks(from);
                    break;
                default:
                    break;
            }
            attacks &= enemy;
            while (attacks) {
                Square to = pop_lsb(attacks);
                ml.push({from, to});
            }
        }
    }

    return ml;
}

std::uint64_t perft(Position& pos, int depth) {
    if (depth == 0)
        return 1;

    MoveList moves = legal(pos);

    // Bulk counting optimisation: at depth 1, just return number of legal moves.
    if (depth == 1)
        return static_cast<std::uint64_t>(moves.size());

    std::uint64_t nodes = 0;
    for (const Move& m : moves) {
        pos.make_move(m);
        nodes += perft(pos, depth - 1);
        pos.unmake_move(m);
    }
    return nodes;
}

}  // namespace chessie::movegen
