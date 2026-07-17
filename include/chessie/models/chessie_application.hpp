#pragma once

#include <QColor>
#include <QObject>
#include <QQmlEngine>

#include <chessie/models/settings_store.hpp>

namespace chessie::models {

class ChessieApplication : public QObject {
    Q_OBJECT

    Q_PROPERTY(QColor lightSquare READ lightSquare NOTIFY themeChanged)
    Q_PROPERTY(QColor darkSquare READ darkSquare NOTIFY themeChanged)
    Q_PROPERTY(QColor highlightFrom READ highlightFrom NOTIFY themeChanged)
    Q_PROPERTY(QColor highlightTo READ highlightTo NOTIFY themeChanged)
    Q_PROPERTY(QColor highlightCheck READ highlightCheck NOTIFY themeChanged)
    Q_PROPERTY(QColor lastMoveFrom READ lastMoveFrom NOTIFY themeChanged)
    Q_PROPERTY(QColor lastMoveTo READ lastMoveTo NOTIFY themeChanged)
    Q_PROPERTY(QColor coordLight READ coordLight NOTIFY themeChanged)
    Q_PROPERTY(QColor coordDark READ coordDark NOTIFY themeChanged)
    Q_PROPERTY(QColor windowBackground READ windowBackground CONSTANT)
    Q_PROPERTY(QColor panelBackground READ panelBackground CONSTANT)
    Q_PROPERTY(QColor textPrimary READ textPrimary CONSTANT)
    Q_PROPERTY(QColor textMuted READ textMuted CONSTANT)
    Q_PROPERTY(QColor buttonBackground READ buttonBackground CONSTANT)
    Q_PROPERTY(QColor buttonHover READ buttonHover CONSTANT)
    Q_PROPERTY(QColor buttonPressed READ buttonPressed CONSTANT)
    Q_PROPERTY(QColor buttonDisabled READ buttonDisabled CONSTANT)
    Q_PROPERTY(QColor buttonDanger READ buttonDanger CONSTANT)
    Q_PROPERTY(QColor statusBarBackground READ statusBarBackground CONSTANT)
    Q_PROPERTY(QColor borderColor READ borderColor CONSTANT)

   public:
    explicit ChessieApplication(QObject* parent = nullptr);

    static ChessieApplication* create(QQmlEngine* engine, QJSEngine* scriptEngine);

    [[nodiscard]] QColor lightSquare() const { return lightSquare_; }
    [[nodiscard]] QColor darkSquare() const { return darkSquare_; }
    [[nodiscard]] QColor highlightFrom() const { return highlightFrom_; }
    [[nodiscard]] QColor highlightTo() const { return highlightTo_; }
    [[nodiscard]] QColor highlightCheck() const { return highlightCheck_; }
    [[nodiscard]] QColor lastMoveFrom() const { return lastMoveFrom_; }
    [[nodiscard]] QColor lastMoveTo() const { return lastMoveTo_; }
    [[nodiscard]] QColor coordLight() const { return coordLight_; }
    [[nodiscard]] QColor coordDark() const { return coordDark_; }
    [[nodiscard]] QColor windowBackground() const { return QColor(43, 43, 43); }
    [[nodiscard]] QColor panelBackground() const { return QColor(30, 30, 30); }
    [[nodiscard]] QColor textPrimary() const { return QColor(224, 224, 224); }
    [[nodiscard]] QColor textMuted() const { return QColor(170, 170, 170); }
    [[nodiscard]] QColor buttonBackground() const { return QColor(60, 60, 60); }
    [[nodiscard]] QColor buttonHover() const { return QColor(80, 80, 80); }
    [[nodiscard]] QColor buttonPressed() const { return QColor(38, 79, 120); }
    [[nodiscard]] QColor buttonDisabled() const { return QColor(43, 43, 43); }
    [[nodiscard]] QColor buttonDanger() const { return QColor(107, 32, 32); }
    [[nodiscard]] QColor statusBarBackground() const { return QColor(37, 37, 37); }
    [[nodiscard]] QColor borderColor() const { return QColor(60, 60, 60); }

    Q_INVOKABLE void bindSettings(SettingsStore* settings);

   signals:
    void themeChanged();

   private:
    void applyTheme(const QString& themeName);

    SettingsStore* settings_ = nullptr;
    QColor lightSquare_;
    QColor darkSquare_;
    QColor highlightFrom_;
    QColor highlightTo_;
    QColor highlightCheck_;
    QColor lastMoveFrom_;
    QColor lastMoveTo_;
    QColor coordLight_;
    QColor coordDark_;
};

}  // namespace chessie::models
