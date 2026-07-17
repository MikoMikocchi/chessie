#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>
#include <chessie/notation/pgn.hpp>
#include <chessie/notation/san.hpp>
#include <chessie/position.hpp>

#include <gtest/gtest.h>

using namespace chessie;

class NotationTest : public ::testing::Test {
   protected:
    void SetUp() override { magic::init(); }
};

TEST_F(NotationTest, SanE4) {
    Position pos = Position::initial();
    MoveList legal = movegen::legal(pos);
    ASSERT_GT(legal.size(), 0);
    Move e4 = legal[0];
    for (int i = 0; i < legal.size(); ++i) {
        if (legal[i].to_sq == E4) {
            e4 = legal[i];
            break;
        }
    }
    EXPECT_EQ(move_to_san(pos, e4), "e4");
}

TEST_F(NotationTest, PgnRoundTrip) {
    const std::string pgn = R"([Event "Test"]
[Site "Chessie"]
[Result "1-0"]

1. e4 e5 2. Nf3 {good move} 1-0
)";
    const ParsedPgn parsed = parse_pgn_game(pgn);
    EXPECT_EQ(parsed.headers.at("Event"), "Test");
    ASSERT_EQ(parsed.moves.size(), 3U);
    EXPECT_EQ(parsed.moves[0].san, "e4");
    EXPECT_EQ(parsed.moves[2].comment, "good move");
    EXPECT_EQ(parsed.result_token, "1-0");
}

TEST_F(NotationTest, BuildPgn) {
    const std::string out =
        build_pgn({{"Event", "Chessie"}}, {"e4", "e5"}, "1/2-1/2");
    EXPECT_NE(out.find("[Event \"Chessie\"]"), std::string::npos);
    EXPECT_NE(out.find("e4"), std::string::npos);
    EXPECT_NE(out.find("1/2-1/2"), std::string::npos);
}
