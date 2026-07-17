#include <chessie/models/engine_controller.hpp>

#include <chessie/magic.hpp>
#include <chessie/move.hpp>
#include <chessie/position.hpp>

namespace chessie::models {

EngineWorker::EngineWorker(QObject* parent) : QObject(parent) {
    limits_.max_depth = 4;
    limits_.time_limit_ms = 900;
}

void EngineWorker::requestSearch(const QString& fen, int request_id) {
    cancel_requested_.store(false, std::memory_order_relaxed);

    chessie::Position search_pos = chessie::Position::from_fen(fen.toStdString());
    chessie::SearchLimits limits = limits_;
    limits.info_callback = [this, request_id](const chessie::SearchInfo& info) {
        emit searchProgress(request_id, info.depth, info.score_cp, info.nodes);
        emit evalUpdated(request_id, info.score_cp, info.depth, info.nodes);
        if (cancel_requested_.load(std::memory_order_relaxed)) {
            engine_.cancel();
        }
    };

    try {
        chessie::magic::init();
        const chessie::SearchResult result = engine_.search(search_pos, limits);
        if (cancel_requested_.load(std::memory_order_relaxed)) {
            emit searchCancelled(request_id);
            return;
        }

        if (result.best_move.is_null()) {
            emit searchNoMove(request_id, result.score_cp, result.depth, result.nodes);
            return;
        }

        emit bestMoveReady(request_id, QString::fromStdString(result.best_move.uci()),
                           result.score_cp, result.depth, result.nodes);
    } catch (const std::exception& ex) {
        emit searchError(request_id, QString::fromUtf8(ex.what()));
    } catch (...) {
        emit searchError(request_id, QStringLiteral("Unknown engine error"));
    }
}

void EngineWorker::cancel() {
    cancel_requested_.store(true, std::memory_order_relaxed);
    engine_.cancel();
}

void EngineWorker::setLimits(int max_depth, int time_limit_ms) {
    limits_.max_depth = max_depth;
    limits_.time_limit_ms = time_limit_ms;
}

EngineController::EngineController(QObject* parent) : QObject(parent) {
    worker_ = new EngineWorker();
    worker_->moveToThread(&worker_thread_);

    connect(&worker_thread_, &QThread::finished, worker_, &QObject::deleteLater);
    connect(worker_, &EngineWorker::bestMoveReady, this, &EngineController::onWorkerBestMove);
    connect(worker_, &EngineWorker::evalUpdated, this, &EngineController::onWorkerEvalUpdated);
    connect(worker_, &EngineWorker::searchProgress, this,
            &EngineController::onWorkerSearchProgress);
    connect(worker_, &EngineWorker::searchCancelled, this, &EngineController::searchCancelled);
    connect(worker_, &EngineWorker::searchNoMove, this, &EngineController::searchNoMove);
    connect(worker_, &EngineWorker::searchError, this, &EngineController::searchError);
}

EngineController::~EngineController() {
    shutdown();
}

void EngineController::setMaxDepth(int value) {
    max_depth_ = value;
    if (started_) {
        QMetaObject::invokeMethod(worker_, "setLimits", Qt::QueuedConnection,
                                  Q_ARG(int, max_depth_), Q_ARG(int, time_limit_ms_));
    }
}

void EngineController::setTimeLimitMs(int value) {
    time_limit_ms_ = value;
    if (started_) {
        QMetaObject::invokeMethod(worker_, "setLimits", Qt::QueuedConnection,
                                  Q_ARG(int, max_depth_), Q_ARG(int, time_limit_ms_));
    }
}

void EngineController::start() {
    if (started_) {
        return;
    }
    worker_thread_.start();
    QMetaObject::invokeMethod(worker_, "setLimits", Qt::QueuedConnection, Q_ARG(int, max_depth_),
                              Q_ARG(int, time_limit_ms_));
    started_ = true;
}

void EngineController::shutdown() {
    if (!started_) {
        return;
    }
    cancelSearch();
    worker_thread_.quit();
    worker_thread_.wait(2000);
    started_ = false;
}

void EngineController::requestMove(const chessie::Position& position) {
    if (!started_) {
        start();
    }
    cancelSearch();
    next_request_id_ += 1;
    pending_request_id_ = next_request_id_;
    const int request_id = pending_request_id_;
    const QString fen = QString::fromStdString(position.to_fen());
    QMetaObject::invokeMethod(worker_, "requestSearch", Qt::QueuedConnection, Q_ARG(QString, fen),
                              Q_ARG(int, request_id));
}

void EngineController::cancelSearch() {
    pending_request_id_ = -1;
    if (started_) {
        QMetaObject::invokeMethod(worker_, "cancel", Qt::QueuedConnection);
    }
}

void EngineController::onWorkerBestMove(int request_id, const QString& move_uci, int score_cp,
                                        int depth, quint64 nodes) {
    if (request_id != pending_request_id_) {
        return;
    }
    pending_request_id_ = -1;
    emit bestMoveReady(request_id, move_uci, score_cp, depth, nodes);
}

void EngineController::onWorkerEvalUpdated(int request_id, int score_cp, int depth,
                                           quint64 nodes) {
    if (request_id != pending_request_id_) {
        return;
    }
    emit evalUpdated(request_id, score_cp, depth, nodes);
}

void EngineController::onWorkerSearchProgress(int request_id, int depth, int score_cp,
                                              quint64 nodes) {
    if (request_id != pending_request_id_) {
        return;
    }
    emit searchProgress(request_id, depth, score_cp, nodes);
}

}  // namespace chessie::models
