#pragma once

#include <QColor>
#include <QString>

namespace chessie::models {

struct BoardThemeColors {
    QColor lightSquare;
    QColor darkSquare;
    QColor highlightFrom;
    QColor highlightTo;
    QColor highlightCheck;
    QColor lastMoveFrom;
    QColor lastMoveTo;
    QColor coordLight;
    QColor coordDark;
};

[[nodiscard]] BoardThemeColors board_theme_for_name(const QString& name);

}  // namespace chessie::models
