#include <chessie/analysis/analyzer.hpp>

#include <chessie/magic.hpp>
#include <chessie/notation/san.hpp>
#include <chessie/position.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <span>
#include <string>

namespace chessie {
namespace {

constexpr int kBrilliantMaxCpLoss = 0;
constexpr int kGreatMaxCpLoss = 10;
constexpr int kBestMaxCpLoss = 20;
constexpr int kGoodMaxCpLoss = 60;
constexpr int kInaccuracyMaxCpLoss = 120;
constexpr int kMistakeMaxCpLoss = 250;
constexpr int kCriticalMoveCount = 3;
constexpr int kCpCap = 1500;

struct SideAcc {
    int moves = 0;
    int cp_loss_sum = 0;
    int brilliant = 0;
    int great = 0;
    int best = 0;
    int good = 0;
    int inaccuracies = 0;
    int mistakes = 0;
    int blunders = 0;
};

[[nodiscard]] int toWhiteCp(int score_cp, Color side_to_move) {
    return side_to_move == Color::White ? score_cp : -score_cp;
}

[[nodiscard]] int clampCp(int cp) {
    return std::max(-kCpCap, std::min(kCpCap, cp));
}

[[nodiscard]] MoveJudgment classifyCpLoss(int cp_loss, bool is_sacrifice = false) {
    if (cp_loss <= kBestMaxCpLoss) {
        if (cp_loss <= kBrilliantMaxCpLoss && is_sacrifice) {
            return MoveJudgment::Brilliant;
        }
        if (cp_loss <= kGreatMaxCpLoss) {
            return MoveJudgment::Best;
        }
        return MoveJudgment::Great;
    }
    if (cp_loss <= kGoodMaxCpLoss) {
        return MoveJudgment::Good;
    }
    if (cp_loss <= kInaccuracyMaxCpLoss) {
        return MoveJudgment::Inaccuracy;
    }
    if (cp_loss <= kMistakeMaxCpLoss) {
        return MoveJudgment::Mistake;
    }
    return MoveJudgment::Blunder;
}

[[nodiscard]] double accuracyFromAvgCpLoss(double avg_cp_loss) {
    if (avg_cp_loss <= 0.0) {
        return 100.0;
    }
    const double raw = 103.1668 * std::exp(-0.04354 * avg_cp_loss) - 3.1669;
    return std::max(0.0, std::min(100.0, raw));
}

[[nodiscard]] SideAnalysisSummary buildSideSummary(const std::vector<MoveAnalysis>& analyses,
                                                   Color color) {
    SideAcc acc;
    for (const MoveAnalysis& move : analyses) {
        if (move.color != color) {
            continue;
        }
        ++acc.moves;
        acc.cp_loss_sum += move.cp_loss;
        switch (move.judgment) {
            case MoveJudgment::Brilliant:
                ++acc.brilliant;
                break;
            case MoveJudgment::Great:
                ++acc.great;
                break;
            case MoveJudgment::Best:
                ++acc.best;
                break;
            case MoveJudgment::Good:
                ++acc.good;
                break;
            case MoveJudgment::Inaccuracy:
                ++acc.inaccuracies;
                break;
            case MoveJudgment::Mistake:
                ++acc.mistakes;
                break;
            case MoveJudgment::Blunder:
                ++acc.blunders;
                break;
        }
    }

    SideAnalysisSummary summary;
    summary.moves = acc.moves;
    summary.avg_cp_loss = acc.moves > 0 ? static_cast<double>(acc.cp_loss_sum) / acc.moves : 0.0;
    summary.inaccuracies = acc.inaccuracies;
    summary.mistakes = acc.mistakes;
    summary.blunders = acc.blunders;
    summary.brilliant = acc.brilliant;
    summary.great = acc.great;
    summary.best = acc.best;
    summary.good = acc.good;
    summary.accuracy = acc.moves > 0 ? accuracyFromAvgCpLoss(summary.avg_cp_loss) : 100.0;
    return summary;
}

[[nodiscard]] SearchLimits analysisLimitsForPosition(const SearchLimits& base_limits,
                                                     const MoveRecord* previous_move) {
    if (base_limits.time_limit_ms < 0) {
        return base_limits;
    }

    double factor = previous_move == nullptr ? 0.8 : 0.65;
    if (previous_move != nullptr) {
        if (previous_move->was_capture) {
            factor += 0.35;
        }
        if (previous_move->was_check) {
            factor += 0.35;
        }
        const MoveFlag flag = previous_move->move.flag;
        if (flag == MoveFlag::Promotion || flag == MoveFlag::EnPassant) {
            factor += 0.25;
        } else if (flag == MoveFlag::CastleKingside || flag == MoveFlag::CastleQueenside) {
            factor += 0.1;
        }
    }

    factor = std::max(0.5, std::min(1.8, factor));
    const auto base_time_ms = base_limits.time_limit_ms;
    const auto scaled_time_ms = std::max<std::int64_t>(25, static_cast<std::int64_t>(
                                                               std::llround(base_time_ms * factor)));
    if (scaled_time_ms == base_time_ms) {
        return base_limits;
    }

    SearchLimits scaled = base_limits;
    scaled.time_limit_ms = scaled_time_ms;
    return scaled;
}

[[nodiscard]] bool cancelled(const AnalysisCancelCallback& is_cancelled) {
    return static_cast<bool>(is_cancelled) && is_cancelled();
}

// ── SHA-256 (minimal implementation for move fingerprints) ───────────────────

struct Sha256Context {
    std::array<std::uint32_t, 8> state{};
    std::array<std::uint8_t, 64> buffer{};
    std::uint64_t bit_count = 0;
    std::size_t buffer_len = 0;
};

[[nodiscard]] constexpr std::uint32_t rotr(std::uint32_t value, unsigned bits) {
    return (value >> bits) | (value << (32U - bits));
}

void sha256Transform(Sha256Context& ctx, const std::uint8_t block[64]) {
    static constexpr std::array<std::uint32_t, 64> k = {
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U,
        0x923f82a4U, 0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
        0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U,
        0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
        0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U,
        0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
        0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
        0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
        0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU,
        0x5b9cca4fU, 0x682e6ff3U, 0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
        0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U};

    std::array<std::uint32_t, 64> words{};
    for (std::size_t i = 0; i < 16; ++i) {
        words[i] = (static_cast<std::uint32_t>(block[i * 4]) << 24U) |
                   (static_cast<std::uint32_t>(block[i * 4 + 1]) << 16U) |
                   (static_cast<std::uint32_t>(block[i * 4 + 2]) << 8U) |
                   static_cast<std::uint32_t>(block[i * 4 + 3]);
    }
    for (std::size_t i = 16; i < 64; ++i) {
        const std::uint32_t s0 = rotr(words[i - 15], 7U) ^ rotr(words[i - 15], 18U) ^
                                 (words[i - 15] >> 3U);
        const std::uint32_t s1 = rotr(words[i - 2], 17U) ^ rotr(words[i - 2], 19U) ^
                                 (words[i - 2] >> 10U);
        words[i] = words[i - 16] + s0 + words[i - 7] + s1;
    }

    std::uint32_t a = ctx.state[0];
    std::uint32_t b = ctx.state[1];
    std::uint32_t c = ctx.state[2];
    std::uint32_t d = ctx.state[3];
    std::uint32_t e = ctx.state[4];
    std::uint32_t f = ctx.state[5];
    std::uint32_t g = ctx.state[6];
    std::uint32_t h = ctx.state[7];

    for (std::size_t i = 0; i < 64; ++i) {
        const std::uint32_t s1 = rotr(e, 6U) ^ rotr(e, 11U) ^ rotr(e, 25U);
        const std::uint32_t ch = (e & f) ^ ((~e) & g);
        const std::uint32_t temp1 = h + s1 + ch + k[i] + words[i];
        const std::uint32_t s0 = rotr(a, 2U) ^ rotr(a, 13U) ^ rotr(a, 22U);
        const std::uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        const std::uint32_t temp2 = s0 + maj;

        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }

    ctx.state[0] += a;
    ctx.state[1] += b;
    ctx.state[2] += c;
    ctx.state[3] += d;
    ctx.state[4] += e;
    ctx.state[5] += f;
    ctx.state[6] += g;
    ctx.state[7] += h;
}

void sha256Init(Sha256Context& ctx) {
    ctx.state = {0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
                 0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U};
    ctx.bit_count = 0;
    ctx.buffer_len = 0;
}

void sha256Update(Sha256Context& ctx, std::span<const std::uint8_t> data) {
    for (std::uint8_t byte : data) {
        ctx.buffer[ctx.buffer_len++] = byte;
        if (ctx.buffer_len == 64) {
            sha256Transform(ctx, ctx.buffer.data());
            ctx.bit_count += 512;
            ctx.buffer_len = 0;
        }
    }
}

void sha256Update(Sha256Context& ctx, std::string_view data) {
    sha256Update(ctx, std::span<const std::uint8_t>(
                          reinterpret_cast<const std::uint8_t*>(data.data()), data.size()));
}

[[nodiscard]] std::string sha256Final(Sha256Context& ctx) {
    const std::uint64_t total_bits = ctx.bit_count + ctx.buffer_len * 8U;

    ctx.buffer[ctx.buffer_len++] = 0x80;
    if (ctx.buffer_len > 56) {
        while (ctx.buffer_len < 64) {
            ctx.buffer[ctx.buffer_len++] = 0;
        }
        sha256Transform(ctx, ctx.buffer.data());
        ctx.buffer_len = 0;
    }

    while (ctx.buffer_len < 56) {
        ctx.buffer[ctx.buffer_len++] = 0;
    }

    for (int i = 7; i >= 0; --i) {
        ctx.buffer[ctx.buffer_len++] =
            static_cast<std::uint8_t>((total_bits >> (i * 8)) & 0xFFU);
    }
    sha256Transform(ctx, ctx.buffer.data());

    static constexpr char kHex[] = "0123456789abcdef";
    std::string out(64, '\0');
    std::size_t out_index = 0;
    for (const std::uint32_t word : ctx.state) {
        for (int byte_index = 3; byte_index >= 0; --byte_index) {
            const std::uint8_t byte =
                static_cast<std::uint8_t>((word >> (byte_index * 8)) & 0xFFU);
            out[out_index++] = kHex[(byte >> 4U) & 0xFU];
            out[out_index++] = kHex[byte & 0xFU];
        }
    }
    return out;
}

[[nodiscard]] std::string computeFingerprint(std::string_view start_fen,
                                               const std::vector<MoveRecord>& history) {
    Sha256Context ctx;
    sha256Init(ctx);
    sha256Update(ctx, start_fen);
    for (const MoveRecord& record : history) {
        sha256Update(ctx, record.fen_after);
    }
    return sha256Final(ctx);
}

}  // namespace

GameAnalyzer::GameAnalyzer(Engine* engine)
    : owned_engine_(64), engine_(engine != nullptr ? engine : &owned_engine_) {}

GameAnalysisReport GameAnalyzer::analyzeGame(std::string_view start_fen,
                                             const std::vector<MoveRecord>& move_history,
                                             const SearchLimits& limits,
                                             const AnalysisCancelCallback& is_cancelled,
                                             const AnalysisProgressCallback& on_progress) {
    magic::init();

    Position position = Position::from_fen(start_fen);
    const int total = static_cast<int>(move_history.size());

    std::vector<MoveAnalysis> analyses;
    analyses.reserve(move_history.size());

    SearchResult before_result{};
    bool has_before_result = false;

    if (total > 0) {
        if (cancelled(is_cancelled)) {
            throw AnalysisCancelled{};
        }

        Position before_pos = Position::from_fen(start_fen);
        SearchLimits before_limits = analysisLimitsForPosition(limits, nullptr);

        SearchLimits wrapped = before_limits;
        wrapped.info_callback = [&](const SearchInfo& info) {
            if (before_limits.info_callback) {
                before_limits.info_callback(info);
            }
            if (cancelled(is_cancelled)) {
                engine_->cancel();
            }
        };

        before_result = engine_->search(before_pos, wrapped);
        has_before_result = true;

        if (cancelled(is_cancelled)) {
            throw AnalysisCancelled{};
        }
    }

    for (int ply = 0; ply < total; ++ply) {
        if (cancelled(is_cancelled)) {
            throw AnalysisCancelled{};
        }

        const MoveRecord& record = move_history[static_cast<std::size_t>(ply)];
        const Color mover = position.side_to_move();
        if (!has_before_result) {
            throw std::logic_error("Missing pre-move engine evaluation");
        }

        const int best_white_cp = toWhiteCp(before_result.score_cp, mover);
        const Move best_move = before_result.best_move;
        std::optional<std::string> best_san;
        if (!best_move.is_null()) {
            Position san_pos = position;
            best_san = move_to_san(san_pos, best_move);
        }

        position.make_move(record.move);
        if (cancelled(is_cancelled)) {
            throw AnalysisCancelled{};
        }

        SearchLimits after_limits = analysisLimitsForPosition(limits, &record);
        SearchLimits wrapped_after = after_limits;
        wrapped_after.info_callback = [&](const SearchInfo& info) {
            if (after_limits.info_callback) {
                after_limits.info_callback(info);
            }
            if (cancelled(is_cancelled)) {
                engine_->cancel();
            }
        };

        const SearchResult after_result = engine_->search(position, wrapped_after);
        const int after_white_cp = toWhiteCp(after_result.score_cp, position.side_to_move());

        const int best_for_mover =
            mover == Color::White ? best_white_cp : -best_white_cp;
        const int after_for_mover =
            mover == Color::White ? after_white_cp : -after_white_cp;

        int cp_loss = 0;
        if (!best_move.is_null() && record.move == best_move) {
            cp_loss = 0;
        } else {
            const int raw_loss = clampCp(best_for_mover) - clampCp(after_for_mover);
            cp_loss = std::max(0, raw_loss);
        }

        MoveAnalysis analysis;
        analysis.ply = ply;
        analysis.color = mover;
        analysis.played_move = record.move;
        analysis.played_san = record.san;
        analysis.best_move = best_move.is_null() ? std::nullopt : std::optional<Move>{best_move};
        analysis.best_san = best_san;
        analysis.eval_before_white_cp = best_white_cp;
        analysis.eval_after_white_cp = after_white_cp;
        analysis.cp_loss = cp_loss;
        analysis.judgment = classifyCpLoss(cp_loss);
        analyses.push_back(analysis);

        if (on_progress) {
            on_progress(ply + 1, total);
        }

        before_result = after_result;
        has_before_result = true;
    }

    GameAnalysisReport report;
    report.start_fen = std::string(start_fen);
    report.total_plies = total;
    report.moves = std::move(analyses);
    report.white = buildSideSummary(report.moves, Color::White);
    report.black = buildSideSummary(report.moves, Color::Black);

    std::vector<MoveAnalysis> sorted = report.moves;
    std::sort(sorted.begin(), sorted.end(),
              [](const MoveAnalysis& a, const MoveAnalysis& b) { return a.cp_loss > b.cp_loss; });

    for (const MoveAnalysis& move : sorted) {
        if (move.cp_loss <= 0) {
            continue;
        }
        report.critical_plies.push_back(move.ply);
        if (static_cast<int>(report.critical_plies.size()) >= kCriticalMoveCount) {
            break;
        }
    }

    report.move_fingerprint = computeFingerprint(start_fen, move_history);
    return report;
}

std::string computeMoveFingerprint(std::string_view start_fen,
                                     const std::vector<MoveRecord>& history) {
    return computeFingerprint(start_fen, history);
}

}  // namespace chessie
