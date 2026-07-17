#include <chessie/game/clock.hpp>
#include <chessie/game/controller.hpp>
#include <chessie/game/player.hpp>
#include <chessie/magic.hpp>
#include <chessie/movegen.hpp>

#include <gtest/gtest.h>

using namespace chessie;

class GameTest : public ::testing::Test {
   protected:
    void SetUp() override { magic::init(); }
};

TEST_F(GameTest, HumanVsHumanMove) {
    GameController controller;
    HumanPlayer white(Color::White);
    HumanPlayer black(Color::Black);
    controller.new_game(white, black);

    MoveList legal = movegen::legal(controller.state().position());
    ASSERT_FALSE(legal.empty());
    EXPECT_TRUE(controller.submit_move(legal[0]));
    EXPECT_EQ(controller.state().ply_count(), 1);
}

TEST_F(GameTest, UndoMove) {
    GameController controller;
    HumanPlayer white(Color::White);
    HumanPlayer black(Color::Black);
    controller.new_game(white, black);

    MoveList legal = movegen::legal(controller.state().position());
    static_cast<void>(controller.submit_move(legal[0]));
    EXPECT_TRUE(controller.undo_move());
    EXPECT_EQ(controller.state().ply_count(), 0);
}

TEST_F(GameTest, ClockIncrement) {
    Clock clock(TimeControl::blitz_5m3s());
    clock.start(Color::White);
    clock.stop();
    clock.add_increment(Color::White);
    EXPECT_GT(clock.remaining(Color::White), 300.0);
}
