#include <chessie/models/runtime_assets.hpp>

#include <QCoreApplication>
#include <QDir>

namespace chessie::models {

QString assetsRoot() {
    const QDir app_dir(QCoreApplication::applicationDirPath());
    const QStringList candidates = {
        app_dir.filePath(QStringLiteral("assets")),
        app_dir.filePath(QStringLiteral("../assets")),
        app_dir.filePath(QStringLiteral("../../assets")),
        app_dir.filePath(QStringLiteral("../../../assets")),
        QDir::currentPath() + QStringLiteral("/assets"),
    };
    for (const QString& candidate : candidates) {
        if (QDir(candidate).exists()) {
            return candidate;
        }
    }
    return app_dir.filePath(QStringLiteral("assets"));
}

}  // namespace chessie::models
