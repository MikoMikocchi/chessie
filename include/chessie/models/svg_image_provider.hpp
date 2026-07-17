#pragma once

#include <QQuickImageProvider>
#include <QSvgRenderer>

namespace chessie::models {

class SvgImageProvider final : public QQuickImageProvider {
   public:
    SvgImageProvider();

    [[nodiscard]] QImage requestImage(const QString& id,
                                       QSize* size,
                                       const QSize& requestedSize) override;

   private:
    [[nodiscard]] QString resolveAssetPath(const QString& id) const;
};

}  // namespace chessie::models
