# Contributing to Chessie

Thanks for helping improve Chessie.

## Development Setup

### Requirements

- CMake 3.20+
- C++20 compiler (GCC, Clang, or MSVC)
- Qt 6.5+ (Quick, QuickControls2, Multimedia, Svg)
- clang-format (optional, for lint CI)

### Build

```bash
git clone https://github.com/MikoMikocchi/chessie.git
cd chessie

cmake --preset debug -DCMAKE_PREFIX_PATH=/path/to/Qt/6.x/macos
cmake --build --preset debug
```

## Running the App

Run from the repository root so bundled assets resolve:

```bash
./build/debug/bin/chessie
```

## Running Tests

```bash
cmake --preset ci -DCMAKE_PREFIX_PATH=/path/to/Qt/6.x/macos
cmake --build --preset ci
ctest --preset ci --output-on-failure
```

Test suites:

- `tests/engine/` — engine unit tests (movegen, search, perft, …)
- `tests/notation/` — SAN/PGN
- `tests/game/` — game controller, clock

## Code Style

Format C++ sources:

```bash
cmake --build build/debug --target format
```

Check formatting (matches CI):

```bash
cmake --build build/debug --target format-check
```

## Pull Requests

1. Fork and create a feature branch
2. Keep changes focused
3. Ensure `ctest --preset ci` passes locally
4. Open a PR with a clear description

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
