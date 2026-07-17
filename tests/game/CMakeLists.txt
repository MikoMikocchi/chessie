add_executable(chessie_game_tests test_game.cpp)
target_link_libraries(chessie_game_tests PRIVATE chessie_engine GTest::gtest_main)
target_sources(chessie_game_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src/game/state.cpp
    ${CMAKE_SOURCE_DIR}/src/game/controller.cpp
    ${CMAKE_SOURCE_DIR}/src/game/clock.cpp
    ${CMAKE_SOURCE_DIR}/src/game/player.cpp
    ${CMAKE_SOURCE_DIR}/src/game/rules.cpp
    ${CMAKE_SOURCE_DIR}/src/notation/san.cpp
    ${CMAKE_SOURCE_DIR}/src/notation/pgn.cpp)
include(GoogleTest)
gtest_discover_tests(chessie_game_tests)
