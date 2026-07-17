#include <chessie/models/move_list_model.hpp>

namespace chessie::models {

MoveListModel::MoveListModel(QObject* parent) : QAbstractListModel(parent) {}

int MoveListModel::rowCount(const QModelIndex& parent) const {
    if (parent.isValid()) {
        return 0;
    }
    return rows_.size();
}

QVariant MoveListModel::data(const QModelIndex& index, int role) const {
    if (!index.isValid() || index.row() < 0 || index.row() >= rows_.size()) {
        return {};
    }
    const Row& row = rows_.at(index.row());
    switch (role) {
        case MoveNumberRole:
            return row.moveNumber;
        case WhiteSanRole:
            return row.whiteSan;
        case BlackSanRole:
            return row.blackSan;
        case WhitePlyRole:
            return row.whitePly;
        case BlackPlyRole:
            return row.blackPly;
        case WhiteNagRole:
            return row.whiteNag;
        case BlackNagRole:
            return row.blackNag;
        case WhiteNagColorRole:
            return row.whiteNagColor;
        case BlackNagColorRole:
            return row.blackNagColor;
        case ActivePlyRole:
            return activePly_;
        default:
            return {};
    }
}

QHash<int, QByteArray> MoveListModel::roleNames() const {
    return {{MoveNumberRole, "moveNumber"},
            {WhiteSanRole, "whiteSan"},
            {BlackSanRole, "blackSan"},
            {WhitePlyRole, "whitePly"},
            {BlackPlyRole, "blackPly"},
            {WhiteNagRole, "whiteNag"},
            {BlackNagRole, "blackNag"},
            {WhiteNagColorRole, "whiteNagColor"},
            {BlackNagColorRole, "blackNagColor"},
            {ActivePlyRole, "activePly"}};
}

void MoveListModel::clear() {
    beginResetModel();
    rows_.clear();
    activePly_ = -1;
    endResetModel();
}

void MoveListModel::setMoves(const QStringList& sans,
                             const QHash<int, QString>& nags,
                             const QHash<int, QString>& nagColors) {
    beginResetModel();
    rows_.clear();
    for (int i = 0; i < sans.size(); i += 2) {
        Row row;
        row.moveNumber = i / 2 + 1;
        row.whiteSan = sans.at(i);
        row.whitePly = i;
        if (nags.contains(i)) {
            row.whiteNag = nags.value(i);
            row.whiteNagColor = nagColors.value(i, QStringLiteral("#cccccc"));
        }
        if (i + 1 < sans.size()) {
            row.blackSan = sans.at(i + 1);
            row.blackPly = i + 1;
            if (nags.contains(i + 1)) {
                row.blackNag = nags.value(i + 1);
                row.blackNagColor = nagColors.value(i + 1, QStringLiteral("#cccccc"));
            }
        }
        rows_.push_back(row);
    }
    if (!sans.isEmpty()) {
        activePly_ = sans.size() - 1;
    } else {
        activePly_ = -1;
    }
    endResetModel();
}

void MoveListModel::setActivePly(int ply) {
    if (activePly_ == ply) {
        return;
    }
    activePly_ = ply;
    if (!rows_.isEmpty()) {
        emit dataChanged(index(0), index(rows_.size() - 1), {ActivePlyRole});
    }
}

}  // namespace chessie::models
