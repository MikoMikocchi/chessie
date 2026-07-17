#include <chessie/magic.hpp>
#include <chessie/models/chessie_application.hpp>
#include <chessie/models/game_controller_model.hpp>
#include <chessie/models/settings_store.hpp>
#include <chessie/models/svg_image_provider.hpp>

#include <QApplication>
#include <QQmlApplicationEngine>
#include <QQuickStyle>
#include <QTranslator>
#include <QtQml/qqml.h>

using namespace Qt::StringLiterals;

int main(int argc, char* argv[]) {
#if defined(Q_OS_MACOS)
    // In-window menu bar — native macOS menu integration breaks popup menus in Qt Quick.
    qputenv("QT_MAC_DISABLE_NATIVE_MENUBAR", "1");
#endif

    QApplication app(argc, argv);
    QCoreApplication::setApplicationName(QStringLiteral("Chessie"));
    QCoreApplication::setOrganizationName(QStringLiteral("Chessie"));
    QQuickStyle::setStyle(QStringLiteral("Fusion"));

    QTranslator translator;
    if (translator.load(QStringLiteral(":/i18n/chessie_en.qm"))) {
        app.installTranslator(&translator);
    }

    chessie::magic::init();

    qmlRegisterSingletonType<chessie::models::SettingsStore>(
        "Chessie", 1, 0, "SettingsStore",
        &chessie::models::SettingsStore::create);
    qmlRegisterSingletonType<chessie::models::GameControllerModel>(
        "Chessie", 1, 0, "GameControllerModel",
        &chessie::models::GameControllerModel::create);
    qmlRegisterSingletonType<chessie::models::ChessieApplication>(
        "Chessie", 1, 0, "Application",
        &chessie::models::ChessieApplication::create);

    QQmlApplicationEngine engine;
    engine.addImageProvider(QStringLiteral("svg"),
                            new chessie::models::SvgImageProvider());

    const QUrl url(u"qrc:/qt/qml/Chessie/qml/Main.qml"_s);
    QObject::connect(
        &engine, &QQmlApplicationEngine::objectCreationFailed, &app,
        []() { QCoreApplication::exit(-1); }, Qt::QueuedConnection);
    engine.load(url);

    if (engine.rootObjects().isEmpty()) {
        return -1;
    }

    return app.exec();
}
