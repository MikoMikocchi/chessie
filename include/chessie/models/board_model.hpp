#pragma once

#include <chessie/move.hpp>
#include <chessie/position.hpp>

#include <QObject>
#include <QStringList>

namespace chessie::models {

class BoardModel : public QObject {
    Q_OBJECT

    Q_PROPERTY(bool flipped READ flipped WRITE setFlipped NOTIFY boardChanged)
    Q_PROPERTY(int selectedSquare READ selectedSquare NOTIFY boardChanged)
    Q_PROPERTY(QStringList legalMoveSquares READ legalMoveSquares NOTIFY boardChanged)
    Q_PROPERTY(QString fen READ fen NOTIFY boardChanged)
    Q_PROPERTY(bool inCheck READ inCheck NOTIFY boardChanged)

   public:
    explicit BoardModel(QObject* parent = nullptr);

    [[nodiscard]] bool flipped() const { return flipped_; }
    void setFlipped(bool value);

    [[nodiscard]] int selectedSquare() const { return selected_square_; }
    [[nodiscard]] QStringList legalMoveSquares() const;
    [[nodiscard]] QString fen() const { return fen_; }
    [[nodiscard]] bool inCheck() const { return in_check_; }

    Q_INVOKABLE QString pieceAt(int square) const;
    Q_INVOKABLE QString pieceImageId(int square) const;
    Q_INVOKABLE void clearSelection();
    Q_INVOKABLE bool selectSquare(int square);
    Q_INVOKABLE bool tryMoveFromTo(int from_square, int to_square, const QString& promotion = {});
    Q_INVOKABLE bool tryMoveUci(const QString& uci);

    void setPosition(const chessie::Position& position);
    [[nodiscard]] chessie::Position position() const { return position_; }
    [[nodiscard]] chessie::MoveList legalMoves() const { return legal_moves_; }

   signals:
    void boardChanged();
    void moveRequested(chessie::Move move);

   private:
    void rebuildLegalMoves();
    void updateDerivedState();

    chessie::Position position_;
    chessie::MoveList legal_moves_;
    QString fen_;
    bool flipped_ = false;
    int selected_square_ = chessie::kNoSquare;
    bool in_check_ = false;
};

}  // namespace chessie::models
