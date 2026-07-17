#include <chessie/models/chessie_application.hpp>
#include <chessie/models/board_theme.hpp>
#include <chessie/models/settings_store.hpp>

namespace chessie::models {

ChessieApplication::ChessieApplication(QObject* parent) : QObject(parent) {
    applyTheme(QStringLiteral("Classic"));
}

ChessieApplication* ChessieApplication::create(QQmlEngine* /*engine*/,
                                               QJSEngine* /*scriptEngine*/) {
    return new ChessieApplication();
}

void ChessieApplication::bindSettings(SettingsStore* settings) {
    if (settings_ == settings) {
        return;
    }
    if (settings_ != nullptr) {
        disconnect(settings_, nullptr, this, nullptr);
    }
    settings_ = settings;
    if (settings_ != nullptr) {
        applyTheme(settings_->boardTheme());
        connect(settings_, &SettingsStore::boardThemeChanged, this, [this]() {
            applyTheme(settings_->boardTheme());
        });
    }
}

void ChessieApplication::applyTheme(const QString& themeName) {
    const BoardThemeColors theme = board_theme_for_name(themeName);
    lightSquare_ = theme.lightSquare;
    darkSquare_ = theme.darkSquare;
    highlightFrom_ = theme.highlightFrom;
    highlightTo_ = theme.highlightTo;
    highlightCheck_ = theme.highlightCheck;
    lastMoveFrom_ = theme.lastMoveFrom;
    lastMoveTo_ = theme.lastMoveTo;
    coordLight_ = theme.coordLight;
    coordDark_ = theme.coordDark;
    emit themeChanged();
}

}  // namespace chessie::models
