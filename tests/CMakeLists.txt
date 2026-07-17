include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.15.2)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

if(TARGET gtest)
    target_compile_options(gtest PRIVATE -Wno-error=character-conversion)
endif()

add_subdirectory(engine)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/game/CMakeLists.txt")
    add_subdirectory(game)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/notation/CMakeLists.txt")
    add_subdirectory(notation)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/analysis/CMakeLists.txt")
    add_subdirectory(analysis)
endif()
