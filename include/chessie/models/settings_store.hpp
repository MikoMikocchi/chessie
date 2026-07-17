#pragma once

#include <QObject>
#include <QQmlEngine>

namespace chessie::models {

class SettingsStore : public QObject {
    Q_OBJECT

    Q_PROPERTY(QString language READ language WRITE setLanguage NOTIFY languageChanged)
    Q_PROPERTY(QString boardTheme READ boardTheme WRITE setBoardTheme NOTIFY boardThemeChanged)
    Q_PROPERTY(bool showCoordinates READ showCoordinates WRITE setShowCoordinates NOTIFY
                   showCoordinatesChanged)
    Q_PROPERTY(bool showLegalMoves READ showLegalMoves WRITE setShowLegalMoves NOTIFY
                   showLegalMovesChanged)
    Q_PROPERTY(bool animateMoves READ animateMoves WRITE setAnimateMoves NOTIFY animateMovesChanged)
    Q_PROPERTY(bool useFigurineNotation READ useFigurineNotation WRITE setUseFigurineNotation NOTIFY
                   useFigurineNotationChanged)
    Q_PROPERTY(bool soundEnabled READ soundEnabled WRITE setSoundEnabled NOTIFY soundEnabledChanged)
    Q_PROPERTY(int soundVolume READ soundVolume WRITE setSoundVolume NOTIFY soundVolumeChanged)
    Q_PROPERTY(int engineDepth READ engineDepth WRITE setEngineDepth NOTIFY engineDepthChanged)
    Q_PROPERTY(int engineTimeMs READ engineTimeMs WRITE setEngineTimeMs NOTIFY engineTimeMsChanged)
    Q_PROPERTY(int analysisDepth READ analysisDepth WRITE setAnalysisDepth NOTIFY
                   analysisDepthChanged)
    Q_PROPERTY(int analysisTimeMs READ analysisTimeMs WRITE setAnalysisTimeMs NOTIFY
                   analysisTimeMsChanged)

   public:
    explicit SettingsStore(QObject* parent = nullptr);

    static SettingsStore* create(QQmlEngine* engine, QJSEngine* scriptEngine);

    [[nodiscard]] QString language() const { return language_; }
    [[nodiscard]] QString boardTheme() const { return boardTheme_; }
    [[nodiscard]] bool showCoordinates() const { return showCoordinates_; }
    [[nodiscard]] bool showLegalMoves() const { return showLegalMoves_; }
    [[nodiscard]] bool animateMoves() const { return animateMoves_; }
    [[nodiscard]] bool useFigurineNotation() const { return useFigurineNotation_; }
    [[nodiscard]] bool soundEnabled() const { return soundEnabled_; }
    [[nodiscard]] int soundVolume() const { return soundVolume_; }
    [[nodiscard]] int engineDepth() const { return engineDepth_; }
    [[nodiscard]] int engineTimeMs() const { return engineTimeMs_; }
    [[nodiscard]] int analysisDepth() const { return analysisDepth_; }
    [[nodiscard]] int analysisTimeMs() const { return analysisTimeMs_; }

    void setLanguage(const QString& value);
    void setBoardTheme(const QString& value);
    void setShowCoordinates(bool value);
    void setShowLegalMoves(bool value);
    void setAnimateMoves(bool value);
    void setUseFigurineNotation(bool value);
    void setSoundEnabled(bool value);
    void setSoundVolume(int value);
    void setEngineDepth(int value);
    void setEngineTimeMs(int value);
    void setAnalysisDepth(int value);
    void setAnalysisTimeMs(int value);

   signals:
    void languageChanged();
    void boardThemeChanged();
    void showCoordinatesChanged();
    void showLegalMovesChanged();
    void animateMovesChanged();
    void useFigurineNotationChanged();
    void soundEnabledChanged();
    void soundVolumeChanged();
    void engineDepthChanged();
    void engineTimeMsChanged();
    void analysisDepthChanged();
    void analysisTimeMsChanged();
    void settingsChanged();

   private:
    void persist() const;

    QString language_ = QStringLiteral("English");
    QString boardTheme_ = QStringLiteral("Classic");
    bool showCoordinates_ = true;
    bool showLegalMoves_ = true;
    bool animateMoves_ = true;
    bool useFigurineNotation_ = true;
    bool soundEnabled_ = true;
    int soundVolume_ = 80;
    int engineDepth_ = 4;
    int engineTimeMs_ = 900;
    int analysisDepth_ = 4;
    int analysisTimeMs_ = 200;
};

}  // namespace chessie::models
