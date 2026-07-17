#pragma once

#include <QAbstractListModel>

namespace chessie::models {

class MoveListModel : public QAbstractListModel {
    Q_OBJECT

   public:
    enum MoveRoles {
        MoveNumberRole = Qt::UserRole + 1,
        WhiteSanRole,
        BlackSanRole,
        WhitePlyRole,
        BlackPlyRole,
        WhiteNagRole,
        BlackNagRole,
        WhiteNagColorRole,
        BlackNagColorRole,
        ActivePlyRole,
    };
    Q_ENUM(MoveRoles)

    explicit MoveListModel(QObject* parent = nullptr);

    [[nodiscard]] int rowCount(const QModelIndex& parent = {}) const override;
    [[nodiscard]] QVariant data(const QModelIndex& index, int role) const override;
    [[nodiscard]] QHash<int, QByteArray> roleNames() const override;

    void clear();
    void setMoves(const QStringList& sans,
                  const QHash<int, QString>& nags = {},
                  const QHash<int, QString>& nagColors = {});
    void setActivePly(int ply);
    [[nodiscard]] int activePly() const { return activePly_; }

   private:
    struct Row {
        int moveNumber = 0;
        QString whiteSan;
        QString blackSan;
        int whitePly = -1;
        int blackPly = -1;
        QString whiteNag;
        QString blackNag;
        QString whiteNagColor;
        QString blackNagColor;
    };

    QVector<Row> rows_;
    int activePly_ = -1;
};

}  // namespace chessie::models
