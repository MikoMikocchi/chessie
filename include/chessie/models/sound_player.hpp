#pragma once

#include <chessie/game/state.hpp>
#include <chessie/game/types.hpp>

#include <QObject>
#include <QSoundEffect>
#include <memory>
#include <unordered_map>

namespace chessie::models {

class SoundPlayer : public QObject {
    Q_OBJECT

   public:
    explicit SoundPlayer(QObject* parent = nullptr);

    void setEnabled(bool enabled);
    void setVolume(int volume);

    void playMoveSound(const chessie::MoveRecord& record, chessie::GameEndReason end_reason);
    void playNamed(const QString& name);

   private:
    void play(const QString& name);

    bool enabled_ = true;
    int volume_percent_ = 80;
    float volume_ = 0.8F;
    std::unordered_map<QString, std::unique_ptr<QSoundEffect>> effects_;
    QSoundEffect* current_ = nullptr;
};

}  // namespace chessie::models
