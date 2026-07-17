#include <chessie/models/sound_player.hpp>
#include <chessie/models/runtime_assets.hpp>

#include <QDir>
#include <QFileInfo>
#include <QUrl>

namespace chessie::models {

SoundPlayer::SoundPlayer(QObject* parent) : QObject(parent) {
    const QString sounds_dir = QDir(assetsRoot()).filePath(QStringLiteral("sounds"));
    const std::unordered_map<QString, QString> names = {
        {QStringLiteral("move"), QStringLiteral("move.wav")},
        {QStringLiteral("capture"), QStringLiteral("capture.wav")},
        {QStringLiteral("check"), QStringLiteral("check.wav")},
        {QStringLiteral("checkmate"), QStringLiteral("chekmate.wav")},
    };

    for (const auto& [name, filename] : names) {
        const QString path = QDir(sounds_dir).filePath(filename);
        if (!QFileInfo::exists(path)) {
            continue;
        }
        auto effect = std::make_unique<QSoundEffect>(this);
        effect->setSource(QUrl::fromLocalFile(path));
        effect->setVolume(volume_);
        effects_.emplace(name, std::move(effect));
    }
}

void SoundPlayer::setEnabled(bool enabled) {
    enabled_ = enabled;
}

void SoundPlayer::setVolume(int volume) {
    volume_percent_ = std::max(0, std::min(100, volume));
    volume_ = static_cast<float>(volume_percent_) / 100.0F;
    for (const auto& [_, effect] : effects_) {
        effect->setVolume(volume_);
    }
}

void SoundPlayer::playMoveSound(const chessie::MoveRecord& record,
                                chessie::GameEndReason end_reason) {
    if (end_reason == chessie::GameEndReason::Checkmate) {
        play(QStringLiteral("checkmate"));
    } else if (record.was_check) {
        play(QStringLiteral("check"));
    } else if (record.was_capture) {
        play(QStringLiteral("capture"));
    } else {
        play(QStringLiteral("move"));
    }
}

void SoundPlayer::playNamed(const QString& name) {
    play(name);
}

void SoundPlayer::play(const QString& name) {
    if (!enabled_) {
        return;
    }
    const auto it = effects_.find(name);
    if (it == effects_.end() || it->second == nullptr) {
        return;
    }
    QSoundEffect* effect = it->second.get();
    if (current_ != nullptr && current_->isPlaying()) {
        current_->stop();
    }
    current_ = effect;
    effect->play();
}

}  // namespace chessie::models
