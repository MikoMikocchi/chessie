#include <chessie/models/svg_image_provider.hpp>
#include <chessie/models/runtime_assets.hpp>

#include <QDir>
#include <QFile>
#include <QPainter>

namespace chessie::models {

namespace {

QString pieceIdToFileName(const QString& id) {
    if (id.size() == 2) {
        const QChar type = id.at(1).toLower();
        const QChar color = id.at(0).toLower();
        const QString suffix = color == QLatin1Char('w') ? QStringLiteral("-w")
                                                         : QStringLiteral("-b");
        switch (type.toLatin1()) {
            case 'p':
                return QStringLiteral("pawn") + suffix;
            case 'n':
                return QStringLiteral("knight") + suffix;
            case 'b':
                return QStringLiteral("bishop") + suffix;
            case 'r':
                return QStringLiteral("rook") + suffix;
            case 'q':
                return QStringLiteral("queen") + suffix;
            case 'k':
                return QStringLiteral("king") + suffix;
            default:
                break;
        }
    }
    if (id.endsWith(QStringLiteral(".svg"), Qt::CaseInsensitive)) {
        return id;
    }
    return id;
}

}  // namespace

SvgImageProvider::SvgImageProvider() : QQuickImageProvider(QQuickImageProvider::Image) {}

QString SvgImageProvider::resolveAssetPath(const QString& id) const {
    const QString baseName = pieceIdToFileName(id);
    const QString fileName = baseName.endsWith(QStringLiteral(".svg"), Qt::CaseInsensitive)
                                 ? baseName
                                 : baseName + QStringLiteral(".svg");

    const QString path =
        QDir(assetsRoot()).filePath(QStringLiteral("pieces/%1").arg(fileName));
    if (QFile::exists(path)) {
        return path;
    }
    return {};
}

QImage SvgImageProvider::requestImage(const QString& id, QSize* size, const QSize& requestedSize) {
    const QString path = resolveAssetPath(id);
    if (path.isEmpty()) {
        if (size) {
            *size = QSize(0, 0);
        }
        return {};
    }

    QSvgRenderer renderer(path);
    if (!renderer.isValid()) {
        if (size) {
            *size = QSize(0, 0);
        }
        return {};
    }

    const QSize target = requestedSize.isValid() ? requestedSize : renderer.defaultSize();
    QImage image(target, QImage::Format_ARGB32_Premultiplied);
    image.fill(Qt::transparent);
    QPainter painter(&image);
    renderer.render(&painter);
    painter.end();

    if (size) {
        *size = target;
    }
    return image;
}

}  // namespace chessie::models
