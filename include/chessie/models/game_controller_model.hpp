#pragma once

#include <chessie/analysis/models.hpp>
#include <chessie/game/controller.hpp>
#include <chessie/models/analysis_controller.hpp>
#include <chessie/models/engine_controller.hpp>
#include <chessie/models/move_list_model.hpp>
#include <chessie/models/settings_store.hpp>
#include <chessie/models/sound_player.hpp>

#include <QObject>
#include <QQmlEngine>
#include <QTimer>
#include <QtQml/qqmlregistration.h>

#include <memory>
#include <optional>
#include <vector>

namespace chessie::models {

class GameControllerModel : public QObject {
    Q_OBJECT

    Q_PROPERTY(QString statusText READ statusText NOTIFY statusChanged)
    Q_PROPERTY(bool flipped READ flipped WRITE setFlipped NOTIFY flippedChanged)
    Q_PROPERTY(bool analysisMode READ analysisMode NOTIFY analysisModeChanged)
    Q_PROPERTY(bool gameActive READ gameActive NOTIFY statusChanged)
    Q_PROPERTY(bool interactive READ interactive NOTIFY interactiveChanged)
    Q_PROPERTY(QVariantList boardPieces READ boardPieces NOTIFY boardChanged)
    Q_PROPERTY(int selectedSquare READ selectedSquare NOTIFY selectionChanged)
    Q_PROPERTY(QVariantList legalTargetSquares READ legalTargetSquares NOTIFY selectionChanged)
    Q_PROPERTY(int lastMoveFrom READ lastMoveFrom NOTIFY boardChanged)
    Q_PROPERTY(int lastMoveTo READ lastMoveTo NOTIFY boardChanged)
    Q_PROPERTY(int checkSquare READ checkSquare NOTIFY boardChanged)
    Q_PROPERTY(double evalCp READ evalCp NOTIFY evalChanged)
    Q_PROPERTY(int evalMate READ evalMate NOTIFY evalChanged)
    Q_PROPERTY(double whiteClockSeconds READ whiteClockSeconds NOTIFY clockChanged)
    Q_PROPERTY(double blackClockSeconds READ blackClockSeconds NOTIFY clockChanged)
    Q_PROPERTY(int activeClockColor READ activeClockColor NOTIFY clockChanged)
    Q_PROPERTY(MoveListModel* moves READ moves CONSTANT)
    Q_PROPERTY(QVariantList evalGraphData READ evalGraphData NOTIFY analysisChanged)
    Q_PROPERTY(QVariantList evalGraphColors READ evalGraphColors NOTIFY analysisChanged)
    Q_PROPERTY(double whiteAccuracy READ whiteAccuracy NOTIFY analysisChanged)
    Q_PROPERTY(double blackAccuracy READ blackAccuracy NOTIFY analysisChanged)
    Q_PROPERTY(QVariantMap whiteJudgments READ whiteJudgments NOTIFY analysisChanged)
    Q_PROPERTY(QVariantMap blackJudgments READ blackJudgments NOTIFY analysisChanged)
    Q_PROPERTY(QString analysisMoveTitle READ analysisMoveTitle NOTIFY analysisSelectionChanged)
    Q_PROPERTY(QString analysisMovePlayed READ analysisMovePlayed NOTIFY analysisSelectionChanged)
    Q_PROPERTY(QString analysisMoveBest READ analysisMoveBest NOTIFY analysisSelectionChanged)
    Q_PROPERTY(QString analysisMoveEval READ analysisMoveEval NOTIFY analysisSelectionChanged)
    Q_PROPERTY(bool analysisMoveVisible READ analysisMoveVisible NOTIFY analysisSelectionChanged)
    Q_PROPERTY(int historyViewPly READ historyViewPly NOTIFY historyViewChanged)
    Q_PROPERTY(int promotionColor READ promotionColor NOTIFY promotionRequired)
    Q_PROPERTY(bool promotionPending READ promotionPending NOTIFY promotionRequired)

   public:
    explicit GameControllerModel(QObject* parent = nullptr);

    static GameControllerModel* create(QQmlEngine* engine, QJSEngine* scriptEngine);

    [[nodiscard]] QString statusText() const { return statusText_; }
    [[nodiscard]] bool flipped() const { return flipped_; }
    [[nodiscard]] bool analysisMode() const { return analysisMode_; }
    [[nodiscard]] bool gameActive() const;
    [[nodiscard]] bool interactive() const { return interactive_; }
    [[nodiscard]] QVariantList boardPieces() const;
    [[nodiscard]] int selectedSquare() const { return selectedSquare_; }
    [[nodiscard]] QVariantList legalTargetSquares() const;
    [[nodiscard]] int lastMoveFrom() const { return lastMoveFrom_; }
    [[nodiscard]] int lastMoveTo() const { return lastMoveTo_; }
    [[nodiscard]] int checkSquare() const { return checkSquare_; }
    [[nodiscard]] double evalCp() const { return evalCp_; }
    [[nodiscard]] int evalMate() const { return evalMate_; }
    [[nodiscard]] double whiteClockSeconds() const { return whiteClockSeconds_; }
    [[nodiscard]] double blackClockSeconds() const { return blackClockSeconds_; }
    [[nodiscard]] int activeClockColor() const { return activeClockColor_; }
    [[nodiscard]] MoveListModel* moves() { return &moves_; }
    [[nodiscard]] QVariantList evalGraphData() const { return evalGraphData_; }
    [[nodiscard]] QVariantList evalGraphColors() const { return evalGraphColors_; }
    [[nodiscard]] double whiteAccuracy() const { return whiteAccuracy_; }
    [[nodiscard]] double blackAccuracy() const { return blackAccuracy_; }
    [[nodiscard]] QVariantMap whiteJudgments() const { return whiteJudgments_; }
    [[nodiscard]] QVariantMap blackJudgments() const { return blackJudgments_; }
    [[nodiscard]] QString analysisMoveTitle() const { return analysisMoveTitle_; }
    [[nodiscard]] QString analysisMovePlayed() const { return analysisMovePlayed_; }
    [[nodiscard]] QString analysisMoveBest() const { return analysisMoveBest_; }
    [[nodiscard]] QString analysisMoveEval() const { return analysisMoveEval_; }
    [[nodiscard]] bool analysisMoveVisible() const { return analysisMoveVisible_; }
    [[nodiscard]] int historyViewPly() const { return historyViewPly_; }
    [[nodiscard]] int promotionColor() const { return promotionColor_; }
    [[nodiscard]] bool promotionPending() const { return promotionPending_; }

    void setFlipped(bool value);

    Q_INVOKABLE void startDefaultGame();
    Q_INVOKABLE void startNewGame(const QString& opponent,
                                  int playerColor,
                                  int timePresetIndex);
    Q_INVOKABLE void openPgn(const QUrl& url);
    Q_INVOKABLE void savePgn(const QUrl& url);
    Q_INVOKABLE void selectSquare(int square);
    Q_INVOKABLE void clearSelection();
    Q_INVOKABLE bool tryMove(int fromSquare, int toSquare, int promotionType = 0);
    Q_INVOKABLE void completePromotion(int promotionType);
    Q_INVOKABLE void cancelPromotion();
    Q_INVOKABLE void undo();
    Q_INVOKABLE void resign();
    Q_INVOKABLE void confirmResign();
    Q_INVOKABLE void offerDraw();
    Q_INVOKABLE void acceptDraw();
    Q_INVOKABLE void declineDraw();
    Q_INVOKABLE void flipBoard();
    Q_INVOKABLE void startAnalysis();
    Q_INVOKABLE void exitAnalysis();
    Q_INVOKABLE void selectPly(int ply);
    Q_INVOKABLE void showAnalysisPly(int ply);
    Q_INVOKABLE QString pieceCodeAt(int square) const;
    Q_INVOKABLE void bindSettings(SettingsStore* settings);

   signals:
    void statusChanged();
    void flippedChanged();
    void analysisModeChanged();
    void interactiveChanged();
    void boardChanged();
    void selectionChanged();
    void evalChanged();
    void clockChanged();
    void analysisChanged();
    void analysisSelectionChanged();
    void historyViewChanged();
    void promotionRequired();
    void gameOverDialogRequested(const QString& message);
    void confirmDialogRequested(const QString& title,
                                const QString& message,
                                const QString& acceptAction);
    void analysisReportReady(const QString& summary);
    void drawOfferReceived();

   private:
    void wireController();
    void refreshBoard();
    void refreshMoves();
    void refreshStatus();
    void refreshClock();
    void refreshEval();
    void updateInteractive();
    void requestAiMove();
    void onEngineBestMove(int requestId, const QString& moveUci, int scoreCp, int depth,
                          quint64 nodes);
    void onEngineEvalUpdated(int requestId, int scoreCp, int depth, quint64 nodes);
    void applyPendingAiMove();
    void onAnalysisFinished(int requestId, const QVariantMap& report);
    void onAnalysisFailed(int requestId, const QString& message);
    void onAnalysisCancelled(int requestId);
    void applyAnalysisReport(const QVariantMap& report);
    chessie::TimeControl timeControlForPreset(int index) const;
    [[nodiscard]] chessie::Move findLegalMove(int fromSquare,
                                              int toSquare,
                                              chessie::PieceType promotion) const;
    [[nodiscard]] std::vector<chessie::Move> promotionCandidates(int fromSquare,
                                                                 int toSquare) const;
    void applyViewPly(int ply);
    void clearAnalysis();

    chessie::GameController controller_;
    std::unique_ptr<chessie::HumanPlayer> whiteHuman_;
    std::unique_ptr<chessie::HumanPlayer> blackHuman_;
    std::unique_ptr<chessie::AIPlayer> whiteAi_;
    std::unique_ptr<chessie::AIPlayer> blackAi_;
    MoveListModel moves_;
    EngineController engineController_;
    AnalysisController analysisController_;
    SoundPlayer soundPlayer_;
    SettingsStore* settings_ = nullptr;

    QTimer clockTimer_;
    QTimer aiApplyTimer_;

    QString statusText_;
    bool flipped_ = false;
    bool analysisMode_ = false;
    bool interactive_ = true;
    int selectedSquare_ = -1;
    int lastMoveFrom_ = -1;
    int lastMoveTo_ = -1;
    int checkSquare_ = -1;
    double evalCp_ = 0.0;
    int evalMate_ = 0;
    double whiteClockSeconds_ = 0.0;
    double blackClockSeconds_ = 0.0;
    int activeClockColor_ = -1;
    int historyViewPly_ = -1;
    int promotionColor_ = 0;
    bool promotionPending_ = false;
    int pendingFrom_ = -1;
    int pendingTo_ = -1;

    QVariantList evalGraphData_;
    QVariantList evalGraphColors_;
    double whiteAccuracy_ = 0.0;
    double blackAccuracy_ = 0.0;
    QVariantMap whiteJudgments_;
    QVariantMap blackJudgments_;
    QString analysisMoveTitle_;
    QString analysisMovePlayed_;
    QString analysisMoveBest_;
    QString analysisMoveEval_;
    bool analysisMoveVisible_ = false;

    std::vector<chessie::Move> cachedLegalMoves_;
    QStringList moveSans_;
    QHash<int, QString> moveNags_;
    QHash<int, QString> moveNagColors_;
    chessie::Move pendingAiMove_{};
    bool hasPendingAiMove_ = false;
    int pendingAiScoreCp_ = 0;
};

}  // namespace chessie::models
