/// @file search.cpp
/// Alpha-beta search with iterative deepening and all pruning techniques.

#include <chessie/search.hpp>

#include <algorithm>
#include <cmath>
#include <cstring>

namespace chessie {

namespace {

// ── Search tuning constants ─────────────────────────────────────────────────

constexpr int kNullMoveMinDepth = 3;
constexpr int kNullMoveBaseReduction = 2;
constexpr int kLmrMinDepth = 4;
constexpr int kLmrMinMoveIndex = 3;
constexpr int kQuiescenceMaxDepth = 16;
constexpr int kFutilityMargin = 200;         // centipawns
constexpr int kReverseFutilityMargin = 300;  // centipawns

// Killer move bonuses
constexpr int kKillerPrimaryBonus = 9'000;
constexpr int kKillerSecondaryBonus = 8'000;

// History heuristic
constexpr int kHistoryMax = 8'000;

// Check for time every N nodes
constexpr std::uint64_t kTimeCheckInterval = 4096;

// ── MVV-LVA values ──────────────────────────────────────────────────────────
// Indexed by piece_index(): Pawn=0..King=5

constexpr int kMvvValues[] = {100, 320, 330, 500, 900, 0};

// ── LMR reduction table ─────────────────────────────────────────────────────

int lmr_reduction(int depth, int move_index) {
    int r = 1;
    if (depth >= 8 && move_index >= 8) {
        r += 1;
    }
    return r;
}

}  // namespace

// ── Search construction ─────────────────────────────────────────────────────

Search::Search(std::size_t tt_mb) : tt_(tt_mb) {}

// ── Reset heuristics ────────────────────────────────────────────────────────

void Search::reset_heuristics() {
    std::memset(killers_, 0, sizeof(killers_));
    std::memset(history_, 0, sizeof(history_));
}

// ── Main search entry point ─────────────────────────────────────────────────

SearchResult Search::search(Position& pos, const SearchLimits& limits) {
    cancelled_.store(false, std::memory_order_relaxed);
    nodes_ = 0;
    reset_heuristics();
    tt_.new_search();

    // Set deadline
    has_deadline_ = (limits.time_limit_ms > 0);
    if (has_deadline_) {
        deadline_ =
            std::chrono::steady_clock::now() + std::chrono::milliseconds(limits.time_limit_ms);
    }

    // Generate root legal moves
    MoveList root_moves = movegen::legal(pos);
    if (root_moves.empty()) {
        // Checkmate or stalemate
        if (pos.is_in_check()) {
            return {kNullMove, -kMateScore, 0, nodes_};
        }
        return {kNullMove, 0, 0, nodes_};
    }

    // Order root moves with current heuristics
    order_moves(pos, root_moves, kNullMove, 0);

    Move best_move = root_moves[0];
    int best_score = -kInfScore;
    int completed_depth = 0;

    // Iterative deepening
    for (int depth = 1; depth <= limits.max_depth; ++depth) {
        if (should_stop())
            break;

        int score = -kInfScore;
        Move iter_best = kNullMove;
        int alpha = -kInfScore;
        int beta = kInfScore;

        for (int i = 0; i < root_moves.size(); ++i) {
            if (should_stop())
                break;

            Move m = root_moves[i];
            pos.make_move(m);
            int s = -negamax(pos, depth - 1, -beta, -alpha, 1, true);
            pos.unmake_move(m);

            if (s > score) {
                score = s;
                iter_best = m;
            }
            if (s > alpha) {
                alpha = s;
            }
        }

        if (should_stop())
            break;
        if (iter_best.is_null())
            break;

        best_move = iter_best;
        best_score = score;
        completed_depth = depth;

        // Move best move to front for next iteration
        for (int i = 0; i < root_moves.size(); ++i) {
            if (root_moves[i] == best_move) {
                // Shift moves to make best_move first
                Move tmp = root_moves[i];
                for (int j = i; j > 0; --j) {
                    root_moves[j] = root_moves[j - 1];
                }
                root_moves[0] = tmp;
                break;
            }
        }
    }

    return {best_move, best_score, completed_depth, nodes_};
}

// ── Negamax with alpha-beta ─────────────────────────────────────────────────

int Search::negamax(Position& pos, int depth, int alpha, int beta, int ply, bool allow_null) {
    if (should_stop())
        return eval::evaluate(pos);

    ++nodes_;

    // ── Draw detection ──────────────────────────────────────────────────
    if (is_draw(pos))
        return 0;

    // ── Transposition table probe ───────────────────────────────────────
    int alpha_orig = alpha;
    TTEntry tt_entry{};
    Move tt_move = kNullMove;
    bool tt_hit = tt_.probe(pos.key(), tt_entry);

    if (tt_hit) {
        tt_move = tt_entry.best_move;
        if (tt_entry.depth >= depth) {
            int tt_score = tt_entry.score;

            // Mate score adjustment: convert from stored (relative to root) to current ply
            if (tt_score > kMateScore - kMaxPly) {
                // Don't use mate scores from TT at PV nodes to avoid instability
            } else if (tt_score < -kMateScore + kMaxPly) {
                // Same for negative mate scores
            } else {
                if (tt_entry.bound == Bound::Exact)
                    return tt_score;
                if (tt_entry.bound == Bound::Lower)
                    alpha = std::max(alpha, tt_score);
                if (tt_entry.bound == Bound::Upper)
                    beta = std::min(beta, tt_score);
                if (alpha >= beta)
                    return tt_score;
            }
        }
    }

    // ── Quiescence at horizon ───────────────────────────────────────────
    if (depth <= 0) {
        return quiescence(pos, alpha, beta, ply, 0);
    }

    bool in_check = pos.is_in_check();

    // ── Check extension ─────────────────────────────────────────────────
    if (in_check) {
        ++depth;
    }

    // ── Reverse futility pruning (static eval pruning) ──────────────────
    if (!in_check && depth <= 3 && ply > 0) {
        int static_eval = eval::evaluate(pos);
        if (static_eval - kReverseFutilityMargin * depth >= beta) {
            return static_eval;
        }
    }

    // ── Null move pruning ───────────────────────────────────────────────
    if (allow_null && !in_check && depth >= kNullMoveMinDepth && ply > 0 &&
        has_non_pawn_material(pos, pos.side_to_move())) {
        int reduction = kNullMoveBaseReduction + depth / 4;
        int null_depth = std::max(0, depth - 1 - reduction);

        pos.make_null_move();
        int null_score = -negamax(pos, null_depth, -beta, -beta + 1, ply + 1, false);
        pos.unmake_null_move();

        if (should_stop())
            return eval::evaluate(pos);
        if (null_score >= beta)
            return beta;
    }

    // ── Generate legal moves ────────────────────────────────────────────
    MoveList moves = movegen::legal(pos);

    if (moves.empty()) {
        if (in_check)
            return -kMateScore + ply;
        return 0;  // stalemate
    }

    // ── Move ordering ───────────────────────────────────────────────────
    order_moves(pos, moves, tt_move, ply);

    int best_score = -kInfScore;
    Move best_move = kNullMove;
    Color side_to_move = pos.side_to_move();

    // ── Futility pruning flag ───────────────────────────────────────────
    bool can_futility = false;
    int futility_base = 0;
    if (!in_check && depth <= 2 && ply > 0) {
        futility_base = eval::evaluate(pos) + kFutilityMargin * depth;
        can_futility = (futility_base <= alpha);
    }

    for (int i = 0; i < moves.size(); ++i) {
        Move m = moves[i];

        // Is this a quiet (non-capture, non-promotion) move?
        bool is_capture = (pos.board().piece_at(m.to_sq).type != PieceType::None);
        bool is_ep = (m.flag == MoveFlag::EnPassant);
        bool is_promo = (m.flag == MoveFlag::Promotion);
        bool is_quiet = !is_capture && !is_ep && !is_promo;

        // ── Futility pruning: skip quiet moves that won't beat alpha ────
        if (can_futility && is_quiet && i > 0 && best_score > -kMateScore + kMaxPly) {
            continue;
        }

        // ── LMR conditions ──────────────────────────────────────────────
        bool can_lmr = is_quiet && !in_check && depth >= kLmrMinDepth && i >= kLmrMinMoveIndex &&
                       (tt_move.is_null() || m != tt_move);

        pos.make_move(m);

        int score;
        if (can_lmr && !pos.is_in_check()) {
            // Late Move Reduction: search with reduced depth
            int r = lmr_reduction(depth, i);
            int reduced_depth = std::max(0, depth - 1 - r);
            score = -negamax(pos, reduced_depth, -alpha - 1, -alpha, ply + 1, true);

            // Re-search at full depth if LMR failed high
            if (score > alpha) {
                score = -negamax(pos, depth - 1, -beta, -alpha, ply + 1, true);
            }
        } else {
            score = -negamax(pos, depth - 1, -beta, -alpha, ply + 1, true);
        }

        pos.unmake_move(m);

        if (score > best_score) {
            best_score = score;
            best_move = m;
        }
        if (score > alpha) {
            alpha = score;
        }
        if (alpha >= beta) {
            // Beta cutoff — record killer and history for quiet moves
            if (is_quiet) {
                record_killer(m, ply);
                update_history(side_to_move, m, depth);
            }
            break;
        }
        if (should_stop())
            break;
    }

    if (best_score == -kInfScore) {
        return eval::evaluate(pos);
    }

    // ── Store in TT ─────────────────────────────────────────────────────
    Bound bound = Bound::Exact;
    if (best_score <= alpha_orig) {
        bound = Bound::Upper;
    } else if (best_score >= beta) {
        bound = Bound::Lower;
    }
    int static_eval_for_tt = eval::evaluate(pos);
    tt_.store(pos.key(), depth, best_score, bound, best_move, static_eval_for_tt);

    return best_score;
}

// ── Quiescence search ───────────────────────────────────────────────────────

int Search::quiescence(Position& pos, int alpha, int beta, int ply, int q_depth) {
    if (should_stop())
        return eval::evaluate(pos);

    ++nodes_;

    if (is_draw(pos))
        return 0;

    bool in_check = pos.is_in_check();

    // In check: search all legal moves (no stand-pat)
    if (in_check) {
        MoveList moves = movegen::legal(pos);
        if (moves.empty())
            return -kMateScore + ply;

        if (q_depth >= kQuiescenceMaxDepth) {
            return eval::evaluate(pos);
        }

        order_moves(pos, moves, kNullMove, ply);

        int best_score = -kInfScore;
        for (int i = 0; i < moves.size(); ++i) {
            pos.make_move(moves[i]);
            int score = -quiescence(pos, -beta, -alpha, ply + 1, q_depth + 1);
            pos.unmake_move(moves[i]);

            if (score > best_score)
                best_score = score;
            if (score > alpha)
                alpha = score;
            if (alpha >= beta)
                break;
            if (should_stop())
                break;
        }
        return best_score;
    }

    // Stand-pat
    int stand_pat = eval::evaluate(pos);

    if (q_depth >= kQuiescenceMaxDepth) {
        return stand_pat;
    }

    if (stand_pat >= beta)
        return beta;
    if (stand_pat > alpha)
        alpha = stand_pat;

    // Generate captures + promotions only
    MoveList noisy = movegen::captures(pos);

    // Filter to legal moves
    MoveList legal_noisy;
    Color us = pos.side_to_move();
    for (int i = 0; i < noisy.size(); ++i) {
        pos.make_move(noisy[i]);
        if (!pos.is_in_check(us)) {
            legal_noisy.push(noisy[i]);
        }
        pos.unmake_move(noisy[i]);
    }

    if (legal_noisy.empty())
        return alpha;

    order_moves(pos, legal_noisy, kNullMove, ply);

    for (int i = 0; i < legal_noisy.size(); ++i) {
        pos.make_move(legal_noisy[i]);
        int score = -quiescence(pos, -beta, -alpha, ply + 1, q_depth + 1);
        pos.unmake_move(legal_noisy[i]);

        if (score >= beta)
            return beta;
        if (score > alpha)
            alpha = score;
        if (should_stop())
            break;
    }

    return alpha;
}

// ── Move ordering ───────────────────────────────────────────────────────────

void Search::order_moves(const Position& pos, MoveList& ml, Move tt_move, int ply) {
    // Simple selection sort by score (adequate for ~30-40 moves)
    for (int i = 0; i < ml.size(); ++i) {
        int best_idx = i;
        int best_score = move_score(pos, ml[i], tt_move, ply);
        for (int j = i + 1; j < ml.size(); ++j) {
            int s = move_score(pos, ml[j], tt_move, ply);
            if (s > best_score) {
                best_score = s;
                best_idx = j;
            }
        }
        if (best_idx != i) {
            std::swap(ml[i], ml[best_idx]);
        }
    }
}

int Search::move_score(const Position& pos, Move m, Move tt_move, int ply) const {
    int score = 0;

    // TT move gets highest priority
    if (!tt_move.is_null() && m == tt_move) {
        return 100'000;
    }

    const Board& board = pos.board();
    Piece moving = board.piece_at(m.from_sq);
    Piece target = board.piece_at(m.to_sq);

    // Promotions
    if (m.flag == MoveFlag::Promotion && m.promotion != PieceType::None) {
        score += 20'000 + kMvvValues[piece_index(m.promotion)];
    }

    // Captures: MVV-LVA
    if (target.type != PieceType::None) {
        score += 10'000;
        score += 10 * kMvvValues[piece_index(target.type)];
        if (moving.type != PieceType::None) {
            score -= kMvvValues[piece_index(moving.type)];
        }
    } else if (m.flag == MoveFlag::EnPassant) {
        score += 10'000;
        score += 10 * kMvvValues[0];  // Pawn capture
        score -= kMvvValues[0];       // by Pawn
    } else {
        // Quiet move: killer + history
        if (ply < kMaxPly) {
            if (killers_[ply][0] == m) {
                score += kKillerPrimaryBonus;
            } else if (killers_[ply][1] == m) {
                score += kKillerSecondaryBonus;
            }
        }
        if (moving.type != PieceType::None) {
            score += history_[color_index(pos.side_to_move())][m.from_sq][m.to_sq];
        }
    }

    // Castling bonus
    if (m.flag == MoveFlag::CastleKingside || m.flag == MoveFlag::CastleQueenside) {
        score += 120;
    }

    return score;
}

// ── Killer moves ────────────────────────────────────────────────────────────

void Search::record_killer(Move m, int ply) {
    if (ply < 0 || ply >= kMaxPly)
        return;
    if (killers_[ply][0] == m)
        return;
    killers_[ply][1] = killers_[ply][0];
    killers_[ply][0] = m;
}

// ── History heuristic ───────────────────────────────────────────────────────

void Search::update_history(Color side, Move m, int depth) {
    int& h = history_[color_index(side)][m.from_sq][m.to_sq];
    h += depth * depth;
    if (h > kHistoryMax)
        h = kHistoryMax;
}

// ── Time / cancellation check ───────────────────────────────────────────────

bool Search::should_stop() const {
    if (cancelled_.load(std::memory_order_relaxed))
        return true;

    if (has_deadline_ && (nodes_ & (kTimeCheckInterval - 1)) == 0) {
        return std::chrono::steady_clock::now() >= deadline_;
    }
    return false;
}

// ── Draw detection ──────────────────────────────────────────────────────────

bool Search::is_draw(const Position& pos) const {
    // 50-move rule
    if (pos.halfmove_clock() >= 100)
        return true;

    // Repetition: if current position has occurred before, it's a draw
    if (pos.repetition_count() >= 2)
        return true;

    // Insufficient material:
    // K vs K, K+N vs K, K+B vs K
    const Board& board = pos.board();
    Bitboard all = board.occupied_all();
    int total_pieces = popcount(all);

    if (total_pieces == 2)
        return true;  // K vs K

    if (total_pieces == 3) {
        // K+minor vs K
        for (int c = 0; c < 2; ++c) {
            auto color = static_cast<Color>(c);
            if (board.pieces(color, PieceType::Knight) || board.pieces(color, PieceType::Bishop)) {
                return true;
            }
        }
    }

    // K+B vs K+B on same color diagonals
    if (total_pieces == 4) {
        Bitboard wb = board.pieces(Color::White, PieceType::Bishop);
        Bitboard bb = board.pieces(Color::Black, PieceType::Bishop);
        if (wb && bb) {
            // Light squares: (file + rank) even; dark squares: odd
            constexpr Bitboard kLightSquares = 0x55AA55AA55AA55AAULL;
            bool w_light = (wb & kLightSquares) != 0;
            bool b_light = (bb & kLightSquares) != 0;
            if (w_light == b_light)
                return true;
        }
    }

    return false;
}

// ── Non-pawn material check ─────────────────────────────────────────────────

bool Search::has_non_pawn_material(const Position& pos, Color side) const {
    const Board& board = pos.board();
    return board.pieces(side, PieceType::Knight) != 0 ||
           board.pieces(side, PieceType::Bishop) != 0 || board.pieces(side, PieceType::Rook) != 0 ||
           board.pieces(side, PieceType::Queen) != 0;
}

}  // namespace chessie
