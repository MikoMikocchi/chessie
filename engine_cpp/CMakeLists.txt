cmake_minimum_required(VERSION 3.20)
project(chessie_engine CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Options ──────────────────────────────────────────────────────────────────
option(BUILD_TESTS  "Build C++ unit tests"   ON)
option(BUILD_BENCH  "Build benchmarks"        OFF)
option(BUILD_PYBIND "Build pybind11 module"   OFF)
option(USE_ASAN     "Enable AddressSanitizer" OFF)

# ── Compiler flags ───────────────────────────────────────────────────────────
add_compile_options(
    -Wall -Wextra -Wpedantic -Werror
    $<$<CONFIG:Release>:-march=native>
    $<$<BOOL:${USE_ASAN}>:-fsanitize=address>
)
add_link_options($<$<BOOL:${USE_ASAN}>:-fsanitize=address>)

# ── Engine library ───────────────────────────────────────────────────────────
file(GLOB_RECURSE ENGINE_SOURCES src/*.cpp)

if(ENGINE_SOURCES)
    add_library(chessie_engine STATIC ${ENGINE_SOURCES})
    target_include_directories(chessie_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
else()
    # Header-only phase: no .cpp files yet
    add_library(chessie_engine INTERFACE)
    target_include_directories(chessie_engine INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)
endif()

# ── Tests (Google Test) ─────────────────────────────────────────────────────
if(BUILD_TESTS)
    enable_testing()
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG        v1.15.2
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
    add_subdirectory(tests)
endif()

# ── Benchmarks (Google Benchmark) ───────────────────────────────────────────
if(BUILD_BENCH)
    include(FetchContent)
    FetchContent_Declare(
        benchmark
        GIT_REPOSITORY https://github.com/google/benchmark.git
        GIT_TAG        v1.9.1
    )
    set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(benchmark)
    add_subdirectory(bench)
endif()

# ── pybind11 module ──────────────────────────────────────────────────────────
if(BUILD_PYBIND)
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.13.6
    )
    FetchContent_MakeAvailable(pybind11)
    pybind11_add_module(_chessie_engine bindings/pybind_module.cpp)
    target_link_libraries(_chessie_engine PRIVATE chessie_engine)
    # Install the extension alongside the Python package
    install(TARGETS _chessie_engine DESTINATION chessie COMPONENT python)
    # Install bundled assets so the wheel is self-contained
    install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../assets/
            DESTINATION chessie/assets
            COMPONENT python)
endif()

# ── Formatting (clang-format) ─────────────────────────────────────────────────
find_program(CLANG_FORMAT clang-format)
if(CLANG_FORMAT)
    file(GLOB_RECURSE ALL_CXX_SOURCES
        ${CMAKE_CURRENT_SOURCE_DIR}/include/*.hpp
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/bindings/*.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp)
    add_custom_target(format
        COMMAND ${CLANG_FORMAT} -i ${ALL_CXX_SOURCES}
        COMMENT "Running clang-format (in-place)")
    add_custom_target(format-check
        COMMAND ${CLANG_FORMAT} --dry-run --Werror ${ALL_CXX_SOURCES}
        COMMENT "Checking clang-format compliance")
endif()

# ── Linting (clang-tidy via compile_commands.json) ────────────────────────────
find_program(CLANG_TIDY clang-tidy)
if(CLANG_TIDY)
    set(CMAKE_CXX_CLANG_TIDY
        ${CLANG_TIDY}
        --config-file=${CMAKE_CURRENT_SOURCE_DIR}/.clang-tidy)
endif()
