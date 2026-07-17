add_executable(chessie_notation_tests test_notation.cpp)
target_link_libraries(chessie_notation_tests PRIVATE chessie_engine GTest::gtest_main)
target_sources(chessie_notation_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src/notation/san.cpp
    ${CMAKE_SOURCE_DIR}/src/notation/pgn.cpp)
include(GoogleTest)
gtest_discover_tests(chessie_notation_tests)
