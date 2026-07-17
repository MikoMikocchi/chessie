#include <chessie/models/game_controller_model.hpp>
#include <chessie/models/settings_store.hpp>

#include <chessie/evaluation.hpp>
#include <chessie/game/rules.hpp>
#include <chessie/magic.hpp>
#include <chessie/notation/pgn.hpp>
#include <chessie/notation/san.hpp>

#include <QFile>
#include <QTextStream>
#include <QUrl>

#include <algorithm>
#include <fstream>
#include <sstream>

namespace chessie::models {

namespace {

QString pieceToCode(const Piece& piece) {
    if (piece.type == PieceType::None) {
        return {};
    }
    const QChar color = piece.color == Color::White ? QLatin1Char('w') : QLatin1Char('b');
    const char type = piece.fen_char();
    return QString(color) + QChar::fromLatin1(type);
}

PieceType pieceTypeFromInt(int value) {
    switch (value) {
        case 1:
            return PieceType::Pawn;
        case 2:
            return PieceType::Knight;
        case 3:
            return PieceType::Bishop;
        case 4:
            return PieceType::Rook;
        case 5:
            return PieceType::Queen;
        case 6:
            return PieceType::King;
        default:
            return PieceType::None;
    }
}

QString resultMessage(GameResult result, GameEndReason reason) {
    switch (result) {
        case GameResult::WhiteWins:
            return QObject::tr("White wins.");
        case GameResult::BlackWins:
            return QObject::tr("Black wins.");
        case GameResult::Draw:
            switch (reason) {
                case GameEndReason::Stalemate:
                    return QObject::tr("Draw by stalemate.");
                case GameEndReason::DrawAgreed:
                    return QObject::tr("Draw agreed.");
                case GameEndReason::DrawRule:
                    return QObject::tr("Draw by rule.");
                default:
                    return QObject::tr("Draw.");
            }
        default:
            return {};
    }
}

}  // namespace

GameControllerModel::GameControllerModel(QObject* parent) : QObject(parent) {
    clockTimer_.setInterval(100);
    connect(&clockTimer_, &QTimer::timeout, this, &GameControllerModel::refreshClock);

    aiApplyTimer_.setSingleShot(true);
    aiApplyTimer_.setInterval(200);
    connect(&aiApplyTimer_, &QTimer::timeout, this, &GameControllerModel::applyPendingAiMove);

    connect(&engineController_, &EngineController::bestMoveReady, this,
            &GameControllerModel::onEngineBestMove);
    connect(&engineController_, &EngineController::evalUpdated, this,
            &GameControllerModel::onEngineEvalUpdated);
    connect(&analysisController_, &AnalysisController::finished, this,
            &GameControllerModel::onAnalysisFinished);
    connect(&analysisController_, &AnalysisController::failed, this,
            &GameControllerModel::onAnalysisFailed);
    connect(&analysisController_, &AnalysisController::cancelled, this,
            &GameControllerModel::onAnalysisCancelled);
    connect(&analysisController_, &AnalysisController::progress, this,
            [this](int /*requestId*/, int done, int total) {
                statusText_ = tr("Analyzing game… %1/%2").arg(done).arg(total);
                emit statusChanged();
            });

    engineController_.start();
    analysisController_.start();

    wireController();
}

GameControllerModel* GameControllerModel::create(QQmlEngine* /*engine*/,
                                                 QJSEngine* /*scriptEngine*/) {
    auto* model = new GameControllerModel();
    return model;
}

void GameControllerModel::wireController() {
    controller_.events.on_move.push_back(
        [this](Move /*move*/, const std::string& /*san*/, const GameState& state) {
            historyViewPly_ = -1;
            if (!state.move_history.empty()) {
                const MoveRecord& record = state.move_history.back();
                soundPlayer_.playMoveSound(record, state.end_reason);
            }
            refreshBoard();
            refreshMoves();
            refreshStatus();
            refreshEval();
            updateInteractive();
            if (!controller_.state().is_game_over()) {
                requestAiMove();
            }
        });

    controller_.events.on_game_over.push_back([this](GameResult result) {
        clockTimer_.stop();
        interactive_ = false;
        emit interactiveChanged();
        refreshStatus();
        const QString message =
            resultMessage(result, controller_.state().end_reason);
        if (!message.isEmpty()) {
            emit gameOverDialogRequested(message);
        }
    });

    controller_.events.on_phase_changed.push_back([this](GamePhase phase) {
        if (phase == GamePhase::Thinking) {
            statusText_ = tr("Engine thinking…");
            emit statusChanged();
        } else {
            refreshStatus();
        }
        updateInteractive();
    });
}

bool GameControllerModel::gameActive() const {
    return !controller_.state().is_game_over();
}

QVariantList GameControllerModel::boardPieces() const {
    QVariantList pieces;
    Position viewPos = controller_.state().position();
    if (historyViewPly_ >= 0) {
        viewPos = Position::from_fen(controller_.state().move_history.at(
                                         static_cast<std::size_t>(historyViewPly_))
                                         .fen_after);
    }

    for (int sq = 0; sq < 64; ++sq) {
        const Piece piece = viewPos.board().piece_at(static_cast<Square>(sq));
        if (piece.type != PieceType::None) {
            QVariantMap entry;
            entry.insert(QStringLiteral("square"), sq);
            entry.insert(QStringLiteral("code"), pieceToCode(piece));
            pieces.push_back(entry);
        }
    }
    return pieces;
}

QVariantList GameControllerModel::legalTargetSquares() const {
    QVariantList targets;
    if (selectedSquare_ < 0 || selectedSquare_ >= 64) {
        return targets;
    }
    if (settings_ && !settings_->showLegalMoves()) {
        return targets;
    }
    for (const Move& move : cachedLegalMoves_) {
        if (static_cast<int>(move.from_sq) == selectedSquare_) {
            targets.push_back(static_cast<int>(move.to_sq));
        }
    }
    return targets;
}

void GameControllerModel::setFlipped(bool value) {
    if (flipped_ == value) {
        return;
    }
    flipped_ = value;
    emit flippedChanged();
}

void GameControllerModel::bindSettings(SettingsStore* settings) {
    if (settings_ == settings) {
        return;
    }
    if (settings_ != nullptr) {
        disconnect(settings_, nullptr, this, nullptr);
    }
    settings_ = settings;
    if (settings_ != nullptr) {
        engineController_.setMaxDepth(settings_->engineDepth());
        engineController_.setTimeLimitMs(settings_->engineTimeMs());
        analysisController_.setMaxDepth(settings_->analysisDepth());
        analysisController_.setTimeLimitMs(settings_->analysisTimeMs());
        soundPlayer_.setEnabled(settings_->soundEnabled());
        soundPlayer_.setVolume(settings_->soundVolume());
        connect(settings_, &SettingsStore::settingsChanged, this, [this]() {
            if (settings_ == nullptr) {
                return;
            }
            engineController_.setMaxDepth(settings_->engineDepth());
            engineController_.setTimeLimitMs(settings_->engineTimeMs());
            analysisController_.setMaxDepth(settings_->analysisDepth());
            analysisController_.setTimeLimitMs(settings_->analysisTimeMs());
            soundPlayer_.setEnabled(settings_->soundEnabled());
            soundPlayer_.setVolume(settings_->soundVolume());
        });
    }
    refreshBoard();
}

void GameControllerModel::startDefaultGame() {
    startNewGame(QStringLiteral("human"), static_cast<int>(Color::White), 2);
}

TimeControl GameControllerModel::timeControlForPreset(int index) const {
    switch (index) {
        case 0:
            return TimeControl::bullet_1m();
        case 1:
            return TimeControl::blitz_3m2s();
        case 2:
            return TimeControl::rapid_10m();
        case 3:
            return TimeControl::rapid_15m10s();
        case 4:
            return TimeControl::classical_30m();
        default:
            return TimeControl::unlimited();
    }
}

void GameControllerModel::startNewGame(const QString& opponent,
                                       int playerColor,
                                       int timePresetIndex) {
    clearAnalysis();
    historyViewPly_ = -1;
    emit historyViewChanged();

    const Color humanColor =
        playerColor == static_cast<int>(Color::Black) ? Color::Black : Color::White;
    const bool vsAi = opponent == QLatin1String("ai");

    whiteHuman_.reset();
    blackHuman_.reset();
    whiteAi_.reset();
    blackAi_.reset();

    IPlayer* white = nullptr;
    IPlayer* black = nullptr;

    if (vsAi) {
        if (humanColor == Color::White) {
            whiteHuman_ = std::make_unique<HumanPlayer>(Color::White);
            blackAi_ = std::make_unique<AIPlayer>(
                Color::Black, "Engine",
                [this](const Position& position) { engineController_.requestMove(position); },
                [this]() {
                    engineController_.cancelSearch();
                    aiApplyTimer_.stop();
                    hasPendingAiMove_ = false;
                });
            white = whiteHuman_.get();
            black = blackAi_.get();
        } else {
            whiteAi_ = std::make_unique<AIPlayer>(
                Color::White, "Engine",
                [this](const Position& position) { engineController_.requestMove(position); },
                [this]() {
                    engineController_.cancelSearch();
                    aiApplyTimer_.stop();
                    hasPendingAiMove_ = false;
                });
            blackHuman_ = std::make_unique<HumanPlayer>(Color::Black);
            white = whiteAi_.get();
            black = blackHuman_.get();
        }
    } else {
        whiteHuman_ = std::make_unique<HumanPlayer>(Color::White);
        blackHuman_ = std::make_unique<HumanPlayer>(Color::Black);
        white = whiteHuman_.get();
        black = blackHuman_.get();
    }

    controller_.new_game(*white, *black, timeControlForPreset(timePresetIndex));
    selectedSquare_ = -1;
    cachedLegalMoves_.clear();
    lastMoveFrom_ = -1;
    lastMoveTo_ = -1;
    promotionPending_ = false;

    refreshBoard();
    refreshMoves();
    refreshStatus();
    refreshEval();
    updateInteractive();

    if (controller_.clock() && !controller_.clock()->is_unlimited()) {
        clockTimer_.start();
        refreshClock();
    } else {
        clockTimer_.stop();
        whiteClockSeconds_ = -1.0;
        blackClockSeconds_ = -1.0;
        activeClockColor_ = static_cast<int>(controller_.state().side_to_move());
        emit clockChanged();
    }

    requestAiMove();
}

void GameControllerModel::openPgn(const QUrl& url) {
    const QString path = url.isLocalFile() ? url.toLocalFile() : url.toString();
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        statusText_ = tr("Failed to open PGN.");
        emit statusChanged();
        return;
    }

    const QString text = QTextStream(&file).readAll();
    const ParsedPgn parsed = parse_pgn_game(text.toStdString());

    startNewGame(QStringLiteral("human"), static_cast<int>(Color::White), 5);

    Position pos = Position::initial();
    QStringList sans;
    for (const PgnMove& pgnMove : parsed.moves) {
        MoveList legal = movegen::legal(pos);
        const std::string targetSan = pgnMove.san;
        auto it = std::find_if(legal.begin(), legal.end(), [&](const Move& candidate) {
            return move_to_san(pos, candidate) == targetSan;
        });
        if (it == legal.end()) {
            break;
        }
        pos.make_move(*it);
        sans.push_back(QString::fromStdString(targetSan));
        static_cast<void>(controller_.submit_move(*it));
    }

    moveSans_ = sans;
    moves_.setMoves(moveSans_, moveNags_, moveNagColors_);
    refreshBoard();
    refreshStatus();
}

void GameControllerModel::savePgn(const QUrl& url) {
    const QString path = url.isLocalFile() ? url.toLocalFile() : url.toString();
    std::map<std::string, std::string> headers{
        {"Event", "Chessie Game"}, {"Site", "Chessie"}, {"Date", "????.??.??"}};

    std::vector<std::string> sans;
    sans.reserve(static_cast<std::size_t>(moveSans_.size()));
    for (const QString& sanText : moveSans_) {
        sans.push_back(sanText.toStdString());
    }

    const std::string pgn = build_pgn(headers, sans, pgn_result_token(controller_.state().result));
    std::ofstream out(path.toStdString());
    if (!out) {
        statusText_ = tr("Failed to save PGN.");
        emit statusChanged();
        return;
    }
    out << pgn;
    statusText_ = tr("PGN saved.");
    emit statusChanged();
}

void GameControllerModel::selectSquare(int square) {
    if (!interactive_ || square < 0 || square >= 64) {
        return;
    }

    Position& pos = controller_.state().position();
    const Piece piece = pos.board().piece_at(static_cast<Square>(square));

    if (selectedSquare_ >= 0 && selectedSquare_ != square) {
        if (tryMove(selectedSquare_, square)) {
            return;
        }
    }

    if (piece.type != PieceType::None && piece.color == pos.side_to_move()) {
        selectedSquare_ = square;
        const MoveList legal = movegen::legal(pos);
        cachedLegalMoves_.assign(legal.begin(), legal.end());
        emit selectionChanged();
        return;
    }

    clearSelection();
}

void GameControllerModel::clearSelection() {
    if (selectedSquare_ < 0 && cachedLegalMoves_.empty()) {
        return;
    }
    selectedSquare_ = -1;
    cachedLegalMoves_.clear();
    emit selectionChanged();
}

Move GameControllerModel::findLegalMove(int fromSquare,
                                        int toSquare,
                                        PieceType promotion) const {
    Position pos = controller_.state().position();
    const MoveList legal = movegen::legal(pos);
    for (const Move& move : legal) {
        if (static_cast<int>(move.from_sq) == fromSquare &&
            static_cast<int>(move.to_sq) == toSquare) {
            if (move.flag == MoveFlag::Promotion) {
                if (promotion != PieceType::None && move.promotion == promotion) {
                    return move;
                }
                continue;
            }
            return move;
        }
    }
    return {};
}

std::vector<Move> GameControllerModel::promotionCandidates(int fromSquare, int toSquare) const {
    Position pos = controller_.state().position();
    const MoveList legal = movegen::legal(pos);
    std::vector<Move> candidates;
    for (const Move& move : legal) {
        if (static_cast<int>(move.from_sq) == fromSquare &&
            static_cast<int>(move.to_sq) == toSquare &&
            move.flag == MoveFlag::Promotion) {
            candidates.push_back(move);
        }
    }
    return candidates;
}

bool GameControllerModel::tryMove(int fromSquare, int toSquare, int promotionType) {
    if (!interactive_) {
        return false;
    }

    const auto candidates = promotionCandidates(fromSquare, toSquare);
    if (candidates.size() > 1 && promotionType == 0) {
        pendingFrom_ = fromSquare;
        pendingTo_ = toSquare;
        promotionPending_ = true;
        promotionColor_ = static_cast<int>(controller_.state().side_to_move());
        emit promotionRequired();
        return false;
    }

    PieceType promo = pieceTypeFromInt(promotionType);
    if (candidates.size() == 1) {
        promo = candidates.front().promotion;
    }

    const Move move = findLegalMove(fromSquare, toSquare, promo);
    MoveList legalCheck = movegen::legal(controller_.state().position());
    if (std::find(legalCheck.begin(), legalCheck.end(), move) == legalCheck.end()) {
        return false;
    }

    clearSelection();
    promotionPending_ = false;
    pendingFrom_ = -1;
    pendingTo_ = -1;

    if (!controller_.submit_move(move)) {
        return false;
    }
    return true;
}

void GameControllerModel::completePromotion(int promotionType) {
    if (!promotionPending_) {
        return;
    }
    tryMove(pendingFrom_, pendingTo_, promotionType);
}

void GameControllerModel::cancelPromotion() {
    promotionPending_ = false;
    pendingFrom_ = -1;
    pendingTo_ = -1;
    emit promotionRequired();
}

void GameControllerModel::undo() {
    if (!controller_.undo_move()) {
        return;
    }
    historyViewPly_ = -1;
    emit historyViewChanged();
    clearSelection();
    refreshBoard();
    refreshMoves();
    refreshStatus();
    refreshEval();
    updateInteractive();
}

void GameControllerModel::resign() {
    emit confirmDialogRequested(tr("Resign"), tr("Are you sure you want to resign?"),
                                QStringLiteral("resign"));
}

void GameControllerModel::confirmResign() {
    const Color color = controller_.state().side_to_move();
    controller_.resign(color);
}

void GameControllerModel::offerDraw() {
    const Color color = controller_.state().side_to_move();
    controller_.offer_draw(color);
    statusText_ = tr("Draw offer sent.");
    emit statusChanged();
}

void GameControllerModel::acceptDraw() {
    const Color color = controller_.state().side_to_move();
    controller_.accept_draw(color);
}

void GameControllerModel::declineDraw() {
    controller_.decline_draw();
    refreshStatus();
}

void GameControllerModel::flipBoard() {
    setFlipped(!flipped_);
}

void GameControllerModel::startAnalysis() {
    if (controller_.state().move_history.empty()) {
        statusText_ = tr("No moves to analyze.");
        emit statusChanged();
        return;
    }
    analysisMode_ = true;
    emit analysisModeChanged();
    statusText_ = tr("Analyzing game…");
    emit statusChanged();
    updateInteractive();

    if (settings_ != nullptr) {
        analysisController_.setMaxDepth(settings_->analysisDepth());
        analysisController_.setTimeLimitMs(settings_->analysisTimeMs());
    }

    analysisController_.analyzeGame(QString::fromStdString(controller_.state().start_fen),
                                    controller_.state().move_history);
}

void GameControllerModel::exitAnalysis() {
    analysisController_.cancelAnalysis();
    clearAnalysis();
    historyViewPly_ = -1;
    emit historyViewChanged();
    refreshBoard();
    refreshStatus();
}

void GameControllerModel::clearAnalysis() {
    analysisController_.cancelAnalysis();
    analysisMode_ = false;
    evalGraphData_.clear();
    evalGraphColors_.clear();
    whiteAccuracy_ = 0.0;
    blackAccuracy_ = 0.0;
    whiteJudgments_.clear();
    blackJudgments_.clear();
    analysisMoveVisible_ = false;
    moveNags_.clear();
    moveNagColors_.clear();
    emit analysisModeChanged();
    emit analysisChanged();
    emit analysisSelectionChanged();
    moves_.setMoves(moveSans_, moveNags_, moveNagColors_);
}

void GameControllerModel::applyAnalysisReport(const QVariantMap& report) {
    evalGraphData_.clear();
    evalGraphColors_.clear();
    moveNags_.clear();
    moveNagColors_.clear();

    const QVariantList evals = report.value(QStringLiteral("evals")).toList();
    for (const QVariant& value : evals) {
        evalGraphData_.push_back(value.toDouble());
    }

    const QVariantList colors = report.value(QStringLiteral("evalColors")).toList();
    for (const QVariant& value : colors) {
        evalGraphColors_.push_back(value.toString());
    }

    const QVariantMap white = report.value(QStringLiteral("white")).toMap();
    const QVariantMap black = report.value(QStringLiteral("black")).toMap();
    whiteJudgments_ = white;
    blackJudgments_ = black;
    whiteAccuracy_ = white.value(QStringLiteral("accuracy")).toDouble();
    blackAccuracy_ = black.value(QStringLiteral("accuracy")).toDouble();

    const QVariantList moves = report.value(QStringLiteral("moves")).toList();
    for (const QVariant& rowValue : moves) {
        const QVariantMap row = rowValue.toMap();
        const int ply = row.value(QStringLiteral("ply")).toInt();
        moveNags_.insert(ply, row.value(QStringLiteral("nag")).toString());
        moveNagColors_.insert(ply, row.value(QStringLiteral("nagColor")).toString());
    }

    moves_.setMoves(moveSans_, moveNags_, moveNagColors_);
    emit analysisChanged();

    const QString summary =
        tr("Analysis complete.\nWhite accuracy: %1%\nBlack accuracy: %2%")
            .arg(whiteAccuracy_, 0, 'f', 1)
            .arg(blackAccuracy_, 0, 'f', 1);
    emit analysisReportReady(summary);
    statusText_ = tr("Analysis complete.");
    emit statusChanged();
}

void GameControllerModel::onAnalysisFinished(int /*requestId*/, const QVariantMap& report) {
    applyAnalysisReport(report);
}

void GameControllerModel::onAnalysisFailed(int /*requestId*/, const QString& message) {
    statusText_ = message;
    emit statusChanged();
    analysisMode_ = false;
    emit analysisModeChanged();
    updateInteractive();
}

void GameControllerModel::onAnalysisCancelled(int /*requestId*/) {
    if (!analysisMode_) {
        return;
    }
    statusText_ = tr("Analysis cancelled.");
    emit statusChanged();
    analysisMode_ = false;
    emit analysisModeChanged();
    updateInteractive();
}

void GameControllerModel::selectPly(int ply) {
    if (ply < -1 || ply >= moveSans_.size()) {
        return;
    }
    historyViewPly_ = ply;
    emit historyViewChanged();
    moves_.setActivePly(ply);
    clearSelection();
    refreshBoard();
    if (analysisMode_) {
        showAnalysisPly(ply);
    }
}

void GameControllerModel::showAnalysisPly(int ply) {
    if (ply < 0 || ply >= moveSans_.size()) {
        analysisMoveVisible_ = false;
        emit analysisSelectionChanged();
        return;
    }
    const int moveNumber = ply / 2 + 1;
    const QString prefix = (ply % 2 == 0) ? QStringLiteral(".") : QStringLiteral("...");
    analysisMoveTitle_ =
        tr("Move %1%2 %3").arg(moveNumber).arg(prefix).arg(moveSans_.at(ply));
    analysisMovePlayed_ = tr("Played: %1").arg(moveSans_.at(ply));
    analysisMoveBest_ = tr("Best: —");
    if (ply < evalGraphData_.size() - 1) {
        const double before = evalGraphData_.at(ply).toDouble();
        const double after = evalGraphData_.at(ply + 1).toDouble();
        analysisMoveEval_ =
            tr("Eval: %1 → %2").arg(before / 100.0, 0, 'f', 2).arg(after / 100.0, 0, 'f', 2);
    } else {
        analysisMoveEval_.clear();
    }
    analysisMoveVisible_ = true;
    emit analysisSelectionChanged();
}

void GameControllerModel::applyViewPly(int ply) {
    selectPly(ply);
}

QString GameControllerModel::pieceCodeAt(int square) const {
    if (square < 0 || square >= 64) {
        return {};
    }
    Position viewPos = controller_.state().position();
    if (historyViewPly_ >= 0 &&
        historyViewPly_ < static_cast<int>(controller_.state().move_history.size())) {
        viewPos = Position::from_fen(
            controller_.state().move_history.at(static_cast<std::size_t>(historyViewPly_)).fen_after);
    }
    return pieceToCode(viewPos.board().piece_at(static_cast<Square>(square)));
}

void GameControllerModel::refreshBoard() {
    Position viewPos = controller_.state().position();
    if (historyViewPly_ >= 0 &&
        historyViewPly_ < static_cast<int>(controller_.state().move_history.size())) {
        viewPos = Position::from_fen(
            controller_.state().move_history.at(static_cast<std::size_t>(historyViewPly_)).fen_after);
        lastMoveFrom_ = static_cast<int>(
            controller_.state().move_history.at(static_cast<std::size_t>(historyViewPly_)).move.from_sq);
        lastMoveTo_ = static_cast<int>(
            controller_.state().move_history.at(static_cast<std::size_t>(historyViewPly_)).move.to_sq);
    } else if (!controller_.state().move_history.empty()) {
        const MoveRecord& last = controller_.state().move_history.back();
        lastMoveFrom_ = static_cast<int>(last.move.from_sq);
        lastMoveTo_ = static_cast<int>(last.move.to_sq);
    } else {
        lastMoveFrom_ = -1;
        lastMoveTo_ = -1;
    }

    checkSquare_ = -1;
    if (Rules::is_in_check(viewPos)) {
        checkSquare_ = static_cast<int>(viewPos.board().king_square(viewPos.side_to_move()));
    }

    emit boardChanged();
}

void GameControllerModel::refreshMoves() {
    moveSans_.clear();
    for (const MoveRecord& record : controller_.state().move_history) {
        moveSans_.push_back(QString::fromStdString(record.san));
    }
    moves_.setMoves(moveSans_, moveNags_, moveNagColors_);
}

void GameControllerModel::refreshStatus() {
    if (controller_.state().is_game_over()) {
        statusText_ = resultMessage(controller_.state().result, controller_.state().end_reason);
    } else if (controller_.state().draw_offer == DrawOffer::Offered) {
        statusText_ = tr("Draw offered.");
        emit drawOfferReceived();
    } else {
        const Color side = controller_.state().side_to_move();
        statusText_ = side == Color::White ? tr("White to move.") : tr("Black to move.");
    }
    emit statusChanged();
}

void GameControllerModel::refreshClock() {
    if (!controller_.clock()) {
        return;
    }
    const double white = controller_.clock()->remaining(Color::White);
    const double black = controller_.clock()->remaining(Color::Black);
    int active = -1;
    if (const std::optional<Color> active_color = controller_.clock()->active_color()) {
        active = static_cast<int>(*active_color);
    }

    // Avoid re-layout jitter: only notify QML when displayed values change.
    const auto tenths = [](double seconds) { return static_cast<int>(seconds * 10.0); };
    if (tenths(white) == tenths(whiteClockSeconds_) &&
        tenths(black) == tenths(blackClockSeconds_) && active == activeClockColor_) {
        return;
    }

    whiteClockSeconds_ = white;
    blackClockSeconds_ = black;
    activeClockColor_ = active;
    emit clockChanged();
}

void GameControllerModel::refreshEval() {
    Position pos = controller_.state().position();
    evalCp_ = static_cast<double>(eval::evaluate(pos));
    evalMate_ = 0;
    emit evalChanged();
}

void GameControllerModel::updateInteractive() {
    const bool active = !controller_.state().is_game_over() && historyViewPly_ < 0 &&
                        !analysisMode_ && !promotionPending_;
    if (interactive_ == active) {
        return;
    }
    interactive_ = active;
    emit interactiveChanged();
}

void GameControllerModel::requestAiMove() {
    if (controller_.state().is_game_over() || historyViewPly_ >= 0) {
        return;
    }
    IPlayer* current = controller_.current_player();
    if (current != nullptr && !current->is_human()) {
        current->request_move(controller_.state().position());
    }
}

void GameControllerModel::onEngineBestMove(int /*requestId*/, const QString& moveUci, int scoreCp,
                                           int /*depth*/, quint64 /*nodes*/) {
    if (controller_.state().is_game_over() ||
        controller_.state().phase != GamePhase::Thinking) {
        return;
    }

    const Color side = controller_.state().side_to_move();
    pendingAiScoreCp_ = side == Color::White ? scoreCp : -scoreCp;
    evalCp_ = static_cast<double>(pendingAiScoreCp_);
    emit evalChanged();

    pendingAiMove_ = Move::from_uci(moveUci.toStdString());
    hasPendingAiMove_ = true;
    aiApplyTimer_.start();
}

void GameControllerModel::onEngineEvalUpdated(int /*requestId*/, int scoreCp, int /*depth*/,
                                              quint64 /*nodes*/) {
    if (controller_.state().phase != GamePhase::Thinking) {
        return;
    }
    const Color side = controller_.state().side_to_move();
    evalCp_ = static_cast<double>(side == Color::White ? scoreCp : -scoreCp);
    emit evalChanged();
}

void GameControllerModel::applyPendingAiMove() {
    if (!hasPendingAiMove_ || controller_.state().is_game_over()) {
        return;
    }

    const MoveList legal = movegen::legal(controller_.state().position());
    const auto it = std::find(legal.begin(), legal.end(), pendingAiMove_);
    if (it != legal.end()) {
        (void)controller_.submit_move(*it);
    }

    hasPendingAiMove_ = false;
    pendingAiMove_ = {};
}

}  // namespace chessie::models
