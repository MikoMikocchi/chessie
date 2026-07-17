#include <chessie/models/board_theme.hpp>

namespace chessie::models {

BoardThemeColors board_theme_for_name(const QString& name) {
    if (name == QLatin1String("Blue")) {
        return {QColor(222, 227, 230), QColor(140, 162, 173), QColor(255, 255, 0, 100),
                QColor(0, 0, 0, 40),       QColor(255, 0, 0, 120),   QColor(155, 199, 0, 105),
                QColor(155, 199, 0, 105),  QColor(140, 162, 173),    QColor(222, 227, 230)};
    }
    if (name == QLatin1String("Green")) {
        return {QColor(236, 238, 220), QColor(112, 149, 120), QColor(255, 255, 0, 100),
                QColor(0, 0, 0, 40),       QColor(255, 0, 0, 120),   QColor(155, 199, 0, 105),
                QColor(155, 199, 0, 105),  QColor(112, 149, 120),    QColor(236, 238, 220)};
    }
    if (name == QLatin1String("Walnut")) {
        return {QColor(228, 210, 184), QColor(118, 74, 47), QColor(255, 255, 0, 100),
                QColor(0, 0, 0, 40),       QColor(255, 0, 0, 120),   QColor(155, 199, 0, 105),
                QColor(155, 199, 0, 105),  QColor(118, 74, 47),      QColor(228, 210, 184)};
    }
    if (name == QLatin1String("Slate")) {
        return {QColor(224, 226, 231), QColor(101, 110, 122), QColor(255, 255, 0, 100),
                QColor(0, 0, 0, 40),       QColor(255, 0, 0, 120),   QColor(155, 199, 0, 105),
                QColor(155, 199, 0, 105),  QColor(101, 110, 122),    QColor(224, 226, 231)};
    }
    return {QColor(240, 217, 181), QColor(181, 136, 99), QColor(255, 255, 0, 100),
            QColor(0, 0, 0, 40),       QColor(255, 0, 0, 120),   QColor(155, 199, 0, 105),
            QColor(155, 199, 0, 105),  QColor(181, 136, 99),     QColor(240, 217, 181)};
}

}  // namespace chessie::models
