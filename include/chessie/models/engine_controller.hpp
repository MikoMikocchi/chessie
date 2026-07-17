#pragma once

#include <chessie/engine.hpp>
#include <chessie/search.hpp>

#include <QObject>
#include <QThread>
#include <atomic>

namespace chessie::models {

class EngineWorker : public QObject {
    Q_OBJECT

   public:
    explicit EngineWorker(QObject* parent = nullptr);

   public slots:
    void requestSearch(const QString& fen, int request_id);
    void cancel();
    void setLimits(int max_depth, int time_limit_ms);

   signals:
    void bestMoveReady(int request_id, const QString& moveUci, int score_cp, int depth,
                       quint64 nodes);
    void evalUpdated(int request_id, int score_cp, int depth, quint64 nodes);
    void searchProgress(int request_id, int depth, int score_cp, quint64 nodes);
    void searchCancelled(int request_id);
    void searchNoMove(int request_id, int score_cp, int depth, quint64 nodes);
    void searchError(int request_id, const QString& message);

   private:
    chessie::Engine engine_;
    chessie::SearchLimits limits_;
    std::atomic<bool> cancel_requested_{false};
};

class EngineController : public QObject {
    Q_OBJECT

   public:
    explicit EngineController(QObject* parent = nullptr);
    ~EngineController() override;

    void setMaxDepth(int value);
    void setTimeLimitMs(int value);

    void start();
    void shutdown();
    void requestMove(const chessie::Position& position);
    void cancelSearch();

   signals:
    void bestMoveReady(int requestId, const QString& moveUci, int scoreCp, int depth,
                       quint64 nodes);
    void evalUpdated(int requestId, int scoreCp, int depth, quint64 nodes);
    void searchProgress(int requestId, int depth, int scoreCp, quint64 nodes);
    void searchCancelled(int requestId);
    void searchNoMove(int requestId, int scoreCp, int depth, quint64 nodes);
    void searchError(int requestId, const QString& message);

   private slots:
    void onWorkerBestMove(int request_id, const QString& move_uci, int score_cp, int depth,
                          quint64 nodes);
    void onWorkerEvalUpdated(int request_id, int score_cp, int depth, quint64 nodes);
    void onWorkerSearchProgress(int request_id, int depth, int score_cp, quint64 nodes);

   private:
    QThread worker_thread_;
    EngineWorker* worker_ = nullptr;
    int max_depth_ = 4;
    int time_limit_ms_ = 900;
    int next_request_id_ = 0;
    int pending_request_id_ = -1;
    bool started_ = false;
};

}  // namespace chessie::models
