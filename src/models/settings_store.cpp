#include <chessie/models/settings_store.hpp>

#include <QSettings>
#include <QtGlobal>

namespace chessie::models {

namespace {

constexpr const char* kOrg = "Chessie";
constexpr const char* kApp = "Chessie";

}  // namespace

SettingsStore::SettingsStore(QObject* parent) : QObject(parent) {
    QSettings settings(kOrg, kApp);
    language_ = settings.value(QStringLiteral("general/language"), language_).toString();
    boardTheme_ = settings.value(QStringLiteral("board/theme"), boardTheme_).toString();
    showCoordinates_ =
        settings.value(QStringLiteral("board/showCoordinates"), showCoordinates_).toBool();
    showLegalMoves_ =
        settings.value(QStringLiteral("board/showLegalMoves"), showLegalMoves_).toBool();
    animateMoves_ = settings.value(QStringLiteral("board/animateMoves"), animateMoves_).toBool();
    useFigurineNotation_ = settings
                               .value(QStringLiteral("board/useFigurineNotation"),
                                      useFigurineNotation_)
                               .toBool();
    soundEnabled_ = settings.value(QStringLiteral("sound/enabled"), soundEnabled_).toBool();
    soundVolume_ = settings.value(QStringLiteral("sound/volume"), soundVolume_).toInt();
    engineDepth_ = settings.value(QStringLiteral("engine/depth"), engineDepth_).toInt();
    engineTimeMs_ = settings.value(QStringLiteral("engine/timeMs"), engineTimeMs_).toInt();
    analysisDepth_ = settings.value(QStringLiteral("analysis/depth"), analysisDepth_).toInt();
    analysisTimeMs_ = settings.value(QStringLiteral("analysis/timeMs"), analysisTimeMs_).toInt();
}

SettingsStore* SettingsStore::create(QQmlEngine* /*engine*/, QJSEngine* /*scriptEngine*/) {
    return new SettingsStore();
}

void SettingsStore::persist() const {
    QSettings settings(kOrg, kApp);
    settings.setValue(QStringLiteral("general/language"), language_);
    settings.setValue(QStringLiteral("board/theme"), boardTheme_);
    settings.setValue(QStringLiteral("board/showCoordinates"), showCoordinates_);
    settings.setValue(QStringLiteral("board/showLegalMoves"), showLegalMoves_);
    settings.setValue(QStringLiteral("board/animateMoves"), animateMoves_);
    settings.setValue(QStringLiteral("board/useFigurineNotation"), useFigurineNotation_);
    settings.setValue(QStringLiteral("sound/enabled"), soundEnabled_);
    settings.setValue(QStringLiteral("sound/volume"), soundVolume_);
    settings.setValue(QStringLiteral("engine/depth"), engineDepth_);
    settings.setValue(QStringLiteral("engine/timeMs"), engineTimeMs_);
    settings.setValue(QStringLiteral("analysis/depth"), analysisDepth_);
    settings.setValue(QStringLiteral("analysis/timeMs"), analysisTimeMs_);
    settings.sync();
}

void SettingsStore::setLanguage(const QString& value) {
    if (language_ == value) {
        return;
    }
    language_ = value;
    emit languageChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setBoardTheme(const QString& value) {
    if (boardTheme_ == value) {
        return;
    }
    boardTheme_ = value;
    emit boardThemeChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setShowCoordinates(bool value) {
    if (showCoordinates_ == value) {
        return;
    }
    showCoordinates_ = value;
    emit showCoordinatesChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setShowLegalMoves(bool value) {
    if (showLegalMoves_ == value) {
        return;
    }
    showLegalMoves_ = value;
    emit showLegalMovesChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setAnimateMoves(bool value) {
    if (animateMoves_ == value) {
        return;
    }
    animateMoves_ = value;
    emit animateMovesChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setUseFigurineNotation(bool value) {
    if (useFigurineNotation_ == value) {
        return;
    }
    useFigurineNotation_ = value;
    emit useFigurineNotationChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setSoundEnabled(bool value) {
    if (soundEnabled_ == value) {
        return;
    }
    soundEnabled_ = value;
    emit soundEnabledChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setSoundVolume(int value) {
    const int clamped = qBound(0, value, 100);
    if (soundVolume_ == clamped) {
        return;
    }
    soundVolume_ = clamped;
    emit soundVolumeChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setEngineDepth(int value) {
    const int clamped = qBound(1, value, 20);
    if (engineDepth_ == clamped) {
        return;
    }
    engineDepth_ = clamped;
    emit engineDepthChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setEngineTimeMs(int value) {
    const int clamped = qBound(100, value, 60'000);
    if (engineTimeMs_ == clamped) {
        return;
    }
    engineTimeMs_ = clamped;
    emit engineTimeMsChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setAnalysisDepth(int value) {
    const int clamped = qBound(1, value, 20);
    if (analysisDepth_ == clamped) {
        return;
    }
    analysisDepth_ = clamped;
    emit analysisDepthChanged();
    emit settingsChanged();
    persist();
}

void SettingsStore::setAnalysisTimeMs(int value) {
    const int clamped = qBound(50, value, 10'000);
    if (analysisTimeMs_ == clamped) {
        return;
    }
    analysisTimeMs_ = clamped;
    emit analysisTimeMsChanged();
    emit settingsChanged();
    persist();
}

}  // namespace chessie::models
