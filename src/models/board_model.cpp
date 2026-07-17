#include <chessie/models/board_model.hpp>

#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>

namespace chessie::models {
namespace {

[[nodiscard]] QString pieceImageIdFor(const chessie::Piece& piece) {
    if (piece.type == chessie::PieceType::None) {
        return {};
    }

    static constexpr const char* kNames[] = {"",   "pawn",   "knight", "bishop",
                                             "rook", "queen",  "king"};
    const char* type_name = kNames[static_cast<int>(piece.type)];
    const char* color_suffix = piece.color == chessie::Color::White ? "w" : "b";
    return QString::fromLatin1("%1-%2").arg(QString::fromLatin1(type_name), color_suffix);
}

}  // namespace

BoardModel::BoardModel(QObject* parent) : QObject(parent) {
    chessie::magic::init();
    position_ = chessie::Position::initial();
    updateDerivedState();
    rebuildLegalMoves();
}

void BoardModel::setFlipped(bool value) {
    if (flipped_ == value) {
        return;
    }
    flipped_ = value;
    emit boardChanged();
}

QStringList BoardModel::legalMoveSquares() const {
    if (selected_square_ == chessie::kNoSquare) {
        return {};
    }

    QStringList targets;
    for (const chessie::Move& move : legal_moves_) {
        if (move.from_sq != selected_square_) {
            continue;
        }
        targets.append(QString::fromLatin1(chessie::square_name(move.to_sq).c_str()));
    }
    return targets;
}

QString BoardModel::pieceAt(int square) const {
    if (!chessie::is_valid_square(square)) {
        return {};
    }
    const chessie::Piece piece = position_.board().piece_at(static_cast<chessie::Square>(square));
    if (piece.type == chessie::PieceType::None) {
        return {};
    }
    return QString(QChar::fromLatin1(piece.fen_char()));
}

QString BoardModel::pieceImageId(int square) const {
    if (!chessie::is_valid_square(square)) {
        return {};
    }
    return pieceImageIdFor(position_.board().piece_at(static_cast<chessie::Square>(square)));
}

void BoardModel::clearSelection() {
    if (selected_square_ == chessie::kNoSquare) {
        return;
    }
    selected_square_ = chessie::kNoSquare;
    emit boardChanged();
}

bool BoardModel::selectSquare(int square) {
    if (!chessie::is_valid_square(square)) {
        clearSelection();
        return false;
    }

    const chessie::Piece piece = position_.board().piece_at(static_cast<chessie::Square>(square));
    if (piece.type == chessie::PieceType::None ||
        piece.color != position_.side_to_move()) {
        clearSelection();
        return false;
    }

    selected_square_ = static_cast<chessie::Square>(square);
    emit boardChanged();
    return true;
}

bool BoardModel::tryMoveFromTo(int from_square, int to_square, const QString& promotion) {
    if (!chessie::is_valid_square(from_square) || !chessie::is_valid_square(to_square)) {
        return false;
    }

    for (const chessie::Move& move : legal_moves_) {
        if (move.from_sq != static_cast<chessie::Square>(from_square) ||
            move.to_sq != static_cast<chessie::Square>(to_square)) {
            continue;
        }

        if (move.flag == chessie::MoveFlag::Promotion) {
            if (promotion.isEmpty()) {
                continue;
            }
            const QChar promo = promotion.at(0).toLower();
            chessie::PieceType promo_type = chessie::PieceType::None;
            switch (promo.toLatin1()) {
                case 'n':
                    promo_type = chessie::PieceType::Knight;
                    break;
                case 'b':
                    promo_type = chessie::PieceType::Bishop;
                    break;
                case 'r':
                    promo_type = chessie::PieceType::Rook;
                    break;
                case 'q':
                    promo_type = chessie::PieceType::Queen;
                    break;
                default:
                    continue;
            }
            if (move.promotion != promo_type) {
                continue;
            }
        }

        emit moveRequested(move);
        selected_square_ = chessie::kNoSquare;
        emit boardChanged();
        return true;
    }

    return false;
}

bool BoardModel::tryMoveUci(const QString& uci) {
    const chessie::Move candidate = chessie::Move::from_uci(uci.toStdString());
    if (candidate.is_null()) {
        return false;
    }

    for (const chessie::Move& move : legal_moves_) {
        if (move == candidate) {
            emit moveRequested(move);
            selected_square_ = chessie::kNoSquare;
            emit boardChanged();
            return true;
        }
    }
    return false;
}

void BoardModel::setPosition(const chessie::Position& position) {
    position_ = position;
    selected_square_ = chessie::kNoSquare;
    updateDerivedState();
    rebuildLegalMoves();
    emit boardChanged();
}

void BoardModel::rebuildLegalMoves() {
    legal_moves_ = chessie::movegen::legal(position_);
}

void BoardModel::updateDerivedState() {
    fen_ = QString::fromStdString(position_.to_fen());
    in_check_ = position_.is_in_check();
}

}  // namespace chessie::models
