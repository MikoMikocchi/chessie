#include <chessie/game/state.hpp>

#include <chessie/movegen.hpp>
#include <chessie/notation/san.hpp>

namespace chessie {

GameState::GameState() {
    position_ = Position::initial();
    start_fen = std::string(kStartingFen);
}

void GameState::setup(std::optional<std::string_view> fen) {
    start_fen = fen.has_value() ? std::string(*fen) : std::string(kStartingFen);
    position_ = fen.has_value() ? Position::from_fen(*fen) : Position::initial();
    phase = GamePhase::AwaitingMove;
    result = GameResult::InProgress;
    end_reason = GameEndReason::None;
    draw_offer = DrawOffer::None;
    draw_offer_by.reset();
    move_history.clear();
}

MoveRecord GameState::apply_move(Move move) {
    const Board& board = position_.board();
    const bool was_capture = board.piece_at(move.to_sq).type != PieceType::None ||
                             move.flag == MoveFlag::EnPassant;

    const std::string san = move_to_san(position_, move);
    position_.make_move(move);

    const std::string fen_after = position_.to_fen();
    const bool was_check = position_.is_in_check(position_.side_to_move());

    MoveRecord record{
        move,
        san,
        fen_after,
        was_check,
        was_capture,
    };
    move_history.push_back(record);

    check_game_over();
    draw_offer = DrawOffer::None;
    draw_offer_by.reset();

    return record;
}

std::optional<Move> GameState::undo_last_move() {
    if (move_history.empty()) {
        return std::nullopt;
    }

    const MoveRecord record = move_history.back();
    move_history.pop_back();
    position_.unmake_move(record.move);

    if (result != GameResult::InProgress) {
        result = GameResult::InProgress;
        end_reason = GameEndReason::None;
        phase = GamePhase::AwaitingMove;
    }

    return record.move;
}

void GameState::resign(Color color) {
    result = color == Color::White ? GameResult::BlackWins : GameResult::WhiteWins;
    end_reason = GameEndReason::Resign;
    phase = GamePhase::GameOver;
}

void GameState::set_draw(GameEndReason reason) {
    result = GameResult::Draw;
    end_reason = reason;
    phase = GamePhase::GameOver;
}

void GameState::flag_fall(Color color) {
    result = color == Color::White ? GameResult::BlackWins : GameResult::WhiteWins;
    end_reason = GameEndReason::FlagFall;
    phase = GamePhase::GameOver;
}

bool GameState::can_claim_draw_by_rule() const {
    return Rules::is_claimable_draw(position_);
}

bool GameState::claim_draw_by_rule() {
    if (is_game_over() || !can_claim_draw_by_rule()) {
        return false;
    }
    set_draw(GameEndReason::DrawRule);
    return true;
}

MoveList GameState::legal_moves() {
    return movegen::legal(position_);
}

void GameState::check_game_over() {
    const MoveList legal = movegen::legal(position_);

    if (legal.empty()) {
        if (position_.is_in_check(position_.side_to_move())) {
            result = position_.side_to_move() == Color::White ? GameResult::BlackWins
                                                                : GameResult::WhiteWins;
            end_reason = GameEndReason::Checkmate;
        } else {
            result = GameResult::Draw;
            end_reason = GameEndReason::Stalemate;
        }
        phase = GamePhase::GameOver;
        return;
    }

    if (Rules::is_automatic_draw(position_)) {
        result = GameResult::Draw;
        end_reason = GameEndReason::DrawRule;
        phase = GamePhase::GameOver;
    }
}

}  // namespace chessie
