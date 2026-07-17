#pragma once

#include <chessie/analysis/analyzer.hpp>
#include <chessie/game/state.hpp>

#include <QObject>
#include <QThread>
#include <QVariantMap>
#include <atomic>
#include <memory>
#include <vector>

namespace chessie::models {

class AnalysisWorker : public QObject {
    Q_OBJECT

   public:
    explicit AnalysisWorker(QObject* parent = nullptr);

   public slots:
    void analyze(int request_id,
                 const QString& start_fen,
                 const QStringList& move_sans,
                 int max_depth,
                 int time_limit_ms);
    void cancel();

   signals:
    void progress(int request_id, int done, int total);
    void finished(int request_id, const QVariantMap& report);
    void cancelled(int request_id);
    void failed(int request_id, const QString& message);

   private:
    std::unique_ptr<chessie::GameAnalyzer> analyzer_;
    std::atomic<bool> cancel_requested_{false};
};

class AnalysisController : public QObject {
    Q_OBJECT

   public:
    explicit AnalysisController(QObject* parent = nullptr);
    ~AnalysisController() override;

    void setMaxDepth(int value);
    void setTimeLimitMs(int value);

    void start();
    void shutdown();
    bool analyzeGame(const QString& start_fen,
                     const std::vector<chessie::MoveRecord>& move_history);
    void cancelAnalysis();

   signals:
    void progress(int requestId, int done, int total);
    void finished(int requestId, const QVariantMap& report);
    void cancelled(int requestId);
    void failed(int requestId, const QString& message);

   private slots:
    void onWorkerProgress(int request_id, int done, int total);
    void onWorkerFinished(int request_id, const QVariantMap& report);
    void onWorkerCancelled(int request_id);
    void onWorkerFailed(int request_id, const QString& message);

   private:
    QThread worker_thread_;
    AnalysisWorker* worker_ = nullptr;
    int max_depth_ = 4;
    int time_limit_ms_ = 200;
    int next_request_id_ = 0;
    int pending_request_id_ = -1;
    bool started_ = false;
};

QVariantMap analysisReportToVariant(const chessie::GameAnalysisReport& report);

}  // namespace chessie::models
