file(GLOB TEST_SOURCES test_*.cpp)

add_executable(chessie_engine_tests ${TEST_SOURCES})
target_link_libraries(chessie_engine_tests PRIVATE chessie_engine GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(chessie_engine_tests)
