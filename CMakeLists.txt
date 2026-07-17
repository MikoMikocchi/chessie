cmake_minimum_required(VERSION 3.20)
project(chessie CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Options ──────────────────────────────────────────────────────────────────
option(BUILD_TESTS "Build C++ unit tests" ON)
option(BUILD_BENCH "Build benchmarks" OFF)
option(USE_ASAN "Enable AddressSanitizer" OFF)

# ── Compiler flags ───────────────────────────────────────────────────────────
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
    add_compile_options($<$<CONFIG:Release>:-march=native>)
endif()

if(USE_ASAN)
    if(MSVC)
        add_compile_options(/fsanitize=address)
        add_link_options(/fsanitize=address)
    else()
        add_compile_options(-fsanitize=address)
        add_link_options(-fsanitize=address)
    endif()
endif()

# ── Engine library ───────────────────────────────────────────────────────────
file(GLOB ENGINE_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/engine/*.cpp)

add_library(chessie_engine STATIC ${ENGINE_SOURCES})
target_include_directories(chessie_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# ── Application (Qt 6 / QML) ─────────────────────────────────────────────────
find_package(Qt6 6.5 COMPONENTS Quick QuickControls2 Multimedia Svg LinguistTools Widgets REQUIRED)
qt_standard_project_setup()
qt_policy(SET QTP0001 NEW)
qt_policy(SET QTP0004 NEW)

file(GLOB CHESSIE_GAME_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/game/*.cpp)
file(GLOB CHESSIE_NOTATION_SOURCES CONFIGURE_DEPENDS
     ${CMAKE_CURRENT_SOURCE_DIR}/src/notation/*.cpp)
file(GLOB CHESSIE_ANALYSIS_SOURCES CONFIGURE_DEPENDS
     ${CMAKE_CURRENT_SOURCE_DIR}/src/analysis/*.cpp)
file(GLOB CHESSIE_MODEL_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/models/*.cpp)
file(GLOB CHESSIE_MODEL_HEADERS CONFIGURE_DEPENDS
     ${CMAKE_CURRENT_SOURCE_DIR}/include/chessie/models/*.hpp)

set(CHESSIE_APP_SOURCES
    ${CHESSIE_GAME_SOURCES}
    ${CHESSIE_NOTATION_SOURCES}
    ${CHESSIE_ANALYSIS_SOURCES}
    ${CHESSIE_MODEL_SOURCES}
    ${CHESSIE_MODEL_HEADERS})

set(CHESSIE_QML_FILES
    qml/Main.qml
    qml/components/AnalysisPanel.qml
    qml/components/ChessButton.qml
    qml/components/ChessBoard.qml
    qml/components/ClockWidget.qml
    qml/components/ControlPanel.qml
    qml/components/EvalBar.qml
    qml/components/EvalGraph.qml
    qml/components/MoveList.qml
    qml/components/Piece.qml
    qml/components/Square.qml
    qml/dialogs/AnalysisDialog.qml
    qml/dialogs/ConfirmDialog.qml
    qml/dialogs/ManualDialog.qml
    qml/dialogs/NewGameDialog.qml
    qml/dialogs/PromotionDialog.qml
    qml/dialogs/SettingsDialog.qml)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/main.cpp")
    qt_add_executable(chessie src/main.cpp ${CHESSIE_APP_SOURCES})

    qt_add_qml_module(
        chessie
        URI Chessie
        VERSION 1.0
        QML_FILES ${CHESSIE_QML_FILES})

    target_link_libraries(
        chessie
        PRIVATE chessie_engine Qt6::Quick Qt6::QuickControls2 Qt6::Multimedia Qt6::Svg Qt6::Widgets)
    target_include_directories(chessie PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    set_target_properties(chessie PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

    add_custom_command(
        TARGET chessie
        POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/assets
                $<TARGET_FILE_DIR:chessie>/assets
        COMMENT "Copying runtime assets next to chessie executable")

    qt_add_translations(
        chessie
        TS_FILES
        i18n/chessie_en.ts
        i18n/chessie_ru.ts)
else()
    add_library(chessie_app STATIC ${CHESSIE_APP_SOURCES})
    target_link_libraries(
        chessie_app
        PUBLIC chessie_engine Qt6::Quick Qt6::QuickControls2 Qt6::Multimedia Qt6::Svg)
    target_include_directories(chessie_app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
    message(STATUS "Building chessie_app static library: src/main.cpp not found")
endif()

# ── Tests (Google Test) ─────────────────────────────────────────────────────
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# ── Formatting (clang-format) ─────────────────────────────────────────────────
find_program(CLANG_FORMAT clang-format)
if(CLANG_FORMAT)
    file(GLOB_RECURSE ALL_CXX_SOURCES
         ${CMAKE_CURRENT_SOURCE_DIR}/include/*.hpp
         ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
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
