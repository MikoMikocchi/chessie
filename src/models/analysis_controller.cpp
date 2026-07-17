#include <chessie/models/analysis_controller.hpp>

#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>
#include <chessie/notation/san.hpp>

namespace chessie::models {

namespace {

QString judgmentKey(MoveJudgment judgment) {
    switch (judgment) {
        case MoveJudgment::Brilliant:
            return QStringLiteral("brilliant");
        case MoveJudgment::Great:
            return QStringLiteral("great");
        case MoveJudgment::Best:
            return QStringLiteral("best");
        case MoveJudgment::Good:
            return QStringLiteral("good");
        case MoveJudgment::Inaccuracy:
            return QStringLiteral("inaccuracy");
        case MoveJudgment::Mistake:
            return QStringLiteral("mistake");
        case MoveJudgment::Blunder:
            return QStringLiteral("blunder");
    }
    return QStringLiteral("good");
}

QVariantMap sideSummaryToVariant(const SideAnalysisSummary& summary) {
    return QVariantMap{{QStringLiteral("moves"), summary.moves},
                       {QStringLiteral("avgCpLoss"), summary.avg_cp_loss},
                       {QStringLiteral("accuracy"), summary.accuracy},
                       {QStringLiteral("brilliant"), summary.brilliant},
                       {QStringLiteral("great"), summary.great},
                       {QStringLiteral("best"), summary.best},
                       {QStringLiteral("good"), summary.good},
                       {QStringLiteral("inaccuracy"), summary.inaccuracies},
                       {QStringLiteral("mistake"), summary.mistakes},
                       {QStringLiteral("blunder"), summary.blunders}};
}

}  // namespace

QVariantMap analysisReportToVariant(const GameAnalysisReport& report) {
    QVariantList evals;
    evals.push_back(0);
    QVariantList evalColors;
    QVariantList moveRows;

    for (const MoveAnalysis& move : report.moves) {
        evals.push_back(move.eval_after_white_cp);
        evalColors.push_back(
            QString::fromUtf8(judgment_color_hex(move.judgment).data()));
        moveRows.push_back(QVariantMap{
            {QStringLiteral("ply"), move.ply},
            {QStringLiteral("nag"), QString::fromUtf8(judgment_nag(move.judgment).data())},
            {QStringLiteral("nagColor"),
             QString::fromUtf8(judgment_color_hex(move.judgment).data())},
            {QStringLiteral("playedSan"), QString::fromStdString(move.played_san)},
            {QStringLiteral("bestSan"),
             move.best_san ? QString::fromStdString(*move.best_san) : QString()},
            {QStringLiteral("cpLoss"), move.cp_loss},
            {QStringLiteral("judgment"), judgmentKey(move.judgment)},
        });
    }

    QVariantList critical;
    for (int ply : report.critical_plies) {
        critical.push_back(ply);
    }

    return QVariantMap{{QStringLiteral("startFen"), QString::fromStdString(report.start_fen)},
                       {QStringLiteral("totalPlies"), report.total_plies},
                       {QStringLiteral("white"), sideSummaryToVariant(report.white)},
                       {QStringLiteral("black"), sideSummaryToVariant(report.black)},
                       {QStringLiteral("evals"), evals},
                       {QStringLiteral("evalColors"), evalColors},
                       {QStringLiteral("moves"), moveRows},
                       {QStringLiteral("critical"), critical},
                       {QStringLiteral("fingerprint"),
                        QString::fromStdString(report.move_fingerprint)}};
}

AnalysisWorker::AnalysisWorker(QObject* parent) : QObject(parent) {
    analyzer_ = std::make_unique<GameAnalyzer>();
}

void AnalysisWorker::analyze(int request_id,
                             const QString& start_fen,
                             const QStringList& move_sans,
                             int max_depth,
                             int time_limit_ms) {
    cancel_requested_.store(false, std::memory_order_relaxed);

    if (start_fen.isEmpty()) {
        emit failed(request_id, QStringLiteral("Invalid start FEN for analysis"));
        return;
    }
    if (move_sans.isEmpty()) {
        emit failed(request_id, QStringLiteral("Move history is empty"));
        return;
    }
    if (max_depth <= 0) {
        emit failed(request_id, QStringLiteral("Analysis depth must be >= 1"));
        return;
    }

    std::vector<MoveRecord> history;
    history.reserve(static_cast<std::size_t>(move_sans.size()));

    try {
        magic::init();
        Position pos = Position::from_fen(start_fen.toStdString());
        for (const QString& sanText : move_sans) {
            const Move move = parse_san(pos, sanText.toStdString());
            MoveRecord record;
            record.move = move;
            record.san = sanText.toStdString();
            pos.make_move(move);
            record.fen_after = pos.to_fen();
            record.was_capture = false;
            record.was_check = pos.is_in_check();
            history.push_back(std::move(record));
        }
    } catch (const std::exception& ex) {
        emit failed(request_id, QString::fromUtf8(ex.what()));
        return;
    }

    SearchLimits limits;
    limits.max_depth = max_depth;
    limits.time_limit_ms = time_limit_ms;

    try {
        const GameAnalysisReport report = analyzer_->analyzeGame(
            start_fen.toStdString(), history, limits,
            [this]() { return cancel_requested_.load(std::memory_order_relaxed); },
            [this, request_id](int done, int total) { emit progress(request_id, done, total); });

        if (cancel_requested_.load(std::memory_order_relaxed)) {
            emit cancelled(request_id);
            return;
        }

        emit finished(request_id, analysisReportToVariant(report));
    } catch (const AnalysisCancelled&) {
        emit cancelled(request_id);
    } catch (const std::exception& ex) {
        emit failed(request_id, QString::fromUtf8(ex.what()));
    } catch (...) {
        emit failed(request_id, QStringLiteral("Unknown analysis error"));
    }
}

void AnalysisWorker::cancel() {
    cancel_requested_.store(true, std::memory_order_relaxed);
}

AnalysisController::AnalysisController(QObject* parent) : QObject(parent) {
    worker_ = new AnalysisWorker();
    worker_->moveToThread(&worker_thread_);

    connect(&worker_thread_, &QThread::finished, worker_, &QObject::deleteLater);
    connect(worker_, &AnalysisWorker::progress, this, &AnalysisController::onWorkerProgress);
    connect(worker_, &AnalysisWorker::finished, this, &AnalysisController::onWorkerFinished);
    connect(worker_, &AnalysisWorker::cancelled, this, &AnalysisController::onWorkerCancelled);
    connect(worker_, &AnalysisWorker::failed, this, &AnalysisController::onWorkerFailed);
}

AnalysisController::~AnalysisController() {
    shutdown();
}

void AnalysisController::setMaxDepth(int value) {
    max_depth_ = value;
}

void AnalysisController::setTimeLimitMs(int value) {
    time_limit_ms_ = value;
}

void AnalysisController::start() {
    if (started_) {
        return;
    }
    worker_thread_.start();
    started_ = true;
}

void AnalysisController::shutdown() {
    if (!started_) {
        return;
    }
    cancelAnalysis();
    worker_thread_.quit();
    worker_thread_.wait(2000);
    started_ = false;
}

bool AnalysisController::analyzeGame(const QString& start_fen,
                                     const std::vector<MoveRecord>& move_history) {
    if (move_history.empty()) {
        return false;
    }
    if (!started_) {
        start();
    }

    cancelAnalysis();
    next_request_id_ += 1;
    pending_request_id_ = next_request_id_;
    const int request_id = pending_request_id_;

    QStringList sans;
    sans.reserve(static_cast<int>(move_history.size()));
    for (const MoveRecord& record : move_history) {
        sans.push_back(QString::fromStdString(record.san));
    }

    QMetaObject::invokeMethod(worker_, "analyze", Qt::QueuedConnection, Q_ARG(int, request_id),
                              Q_ARG(QString, start_fen), Q_ARG(QStringList, sans),
                              Q_ARG(int, max_depth_), Q_ARG(int, time_limit_ms_));
    return true;
}

void AnalysisController::cancelAnalysis() {
    pending_request_id_ = -1;
    if (started_) {
        QMetaObject::invokeMethod(worker_, "cancel", Qt::QueuedConnection);
    }
}

void AnalysisController::onWorkerProgress(int request_id, int done, int total) {
    if (request_id != pending_request_id_) {
        return;
    }
    emit progress(request_id, done, total);
}

void AnalysisController::onWorkerFinished(int request_id, const QVariantMap& report) {
    if (request_id != pending_request_id_) {
        return;
    }
    pending_request_id_ = -1;
    emit finished(request_id, report);
}

void AnalysisController::onWorkerCancelled(int request_id) {
    if (request_id != pending_request_id_) {
        return;
    }
    pending_request_id_ = -1;
    emit cancelled(request_id);
}

void AnalysisController::onWorkerFailed(int request_id, const QString& message) {
    if (request_id != pending_request_id_) {
        return;
    }
    pending_request_id_ = -1;
    emit failed(request_id, message);
}

}  // namespace chessie::models
