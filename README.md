# Chessie

<div align="center">

[![CI](https://github.com/MikoMikocchi/chessie/actions/workflows/ci.yml/badge.svg)](https://github.com/MikoMikocchi/chessie/actions/workflows/ci.yml)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg?logo=c%2B%2B)](https://en.cppreference.com/w/cpp/20)
[![Qt 6](https://img.shields.io/badge/Qt-6.8-green.svg?logo=qt)](https://www.qt.io/)
[![CMake](https://img.shields.io/badge/CMake-3.20%2B-red.svg?logo=cmake)](https://cmake.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

</div>

Native desktop chess application with an integrated C++20 AI engine, post-game analysis, and a Qt Quick/QML interface.

## Overview

Chessie is a fully native C++ application:

- **Engine** — alpha-beta search, evaluation, transposition table (`src/engine/`, `include/chessie/`)
- **Game layer** — rules, clocks, PGN/SAN, analysis (`src/game/`, `src/notation/`, `src/analysis/`)
- **UI** — Qt 6 Quick/QML (`qml/`, `src/models/`)

### Gameplay

![Gameplay](https://github.com/user-attachments/assets/5b5d9dca-40a9-4e7d-8688-551b983bdb14)

## Features

- Human vs Human and Human vs AI with configurable time controls
- Interactive board with legal-move hints, promotion, flip, undo
- Eval bar, chess clocks, PGN import/export
- Post-game analysis with move judgments and eval graph
- Settings (language, board themes, sound, engine depth)
- Built-in chess manual (7 chapters)

## Requirements

- **CMake** 3.20+
- **C++20** compiler (GCC, Clang, or MSVC)
- **Qt** 6.5+ (Quick, QuickControls2, Multimedia, Svg)

## Build

```bash
git clone https://github.com/MikoMikocchi/chessie.git
cd chessie

cmake --preset release -DCMAKE_PREFIX_PATH=/path/to/Qt/6.x/macos
cmake --build --preset release
```

## Run

From the repository root (so `assets/` resolves correctly):

```bash
./build/release/bin/chessie
```

## Tests

```bash
cmake --preset ci -DCMAKE_PREFIX_PATH=/path/to/Qt/6.x/macos
cmake --build --preset ci
ctest --preset ci --output-on-failure
```

## Project layout

```
include/chessie/   # Engine & app headers
src/engine/        # Chess engine
src/game/          # Game controller, clock, rules
src/notation/      # SAN, PGN
src/analysis/      # Game analyzer
src/models/        # Qt/QML bridge
qml/               # Qt Quick UI
assets/            # Pieces, sounds, fonts
tests/             # Google Test suites
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and testing instructions.

## License

Chessie is released under the [Apache License 2.0](LICENSE).
