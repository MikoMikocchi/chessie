# Chessie

<div align="center">

[![CI](https://github.com/MikoMikocchi/chessie/actions/workflows/ci.yml/badge.svg)](https://github.com/MikoMikocchi/chessie/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg?logo=c%2B%2B)](https://en.cppreference.com/w/cpp/20)
[![PyQt6](https://img.shields.io/badge/PyQt-6.8-green.svg?logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![CMake](https://img.shields.io/badge/CMake-3.20%2B-red.svg?logo=cmake)](https://cmake.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)

</div>

Desktop chess application with a high-performance C++ AI engine backend and a game analyzer. Built with Python, PyQt6, and C++20.

## Overview

Chessie offers a playable chess board along with an integrated AI engine. It uses a modern architecture, splitting the computationally heavy engine logic into a C++ module exposed via `pybind11`, and keeping the UI and high-level game logic in Python.

### Gameplay

![Gameplay](https://github.com/user-attachments/assets/5b5d9dca-40a9-4e7d-8688-551b983bdb14)

## Features

- **Playable Interface**: A responsive graphical chess board built with PyQt6.
- **Fast C++ Engine**: Move generation, search algorithms, and evaluations are computed in a fast C++20 engine.
- **Game Analysis Engine**: Evaluate lines, find best moves, and generate a post-game analysis report.
- **PGN Parsing & Exporting**: Load your favorite games, or save played matches.

### Game Analyzer

![Game Analyzer](https://github.com/user-attachments/assets/67373a0b-a8a6-4001-bf3e-53bf71d6b7b5)

## Installation & Setup

You will need **Python 3.13+**, **CMake 3.20+**, and a **C++20 compliant compiler** (e.g., GCC, Clang, or MSVC).

We recommend using [`uv`](https://docs.astral.sh/uv/) for Python dependency management.

1. Clone the repository:

    ```bash
    git clone https://github.com/MikoMikocchi/chessie.git
    cd chessie
    ```

2. Sync dependencies and build the C++ engine:
    ```bash
    uv sync --all-groups
    ```
    _This automatically builds the C++ module via `scikit-build-core` and installs it in the environment._

## Running the App

Once installed, you can launch the application by running:

```bash
uv run chessie
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions on the development setup, running tests (both Python and C++), and our code of conduct.

## Support & Reporting Issues

If you encounter bugs or have feature requests, please open an issue on
GitHub: https://github.com/MikoMikocchi/chessie/issues. For quick questions,
join the discussions tab.

## License

Chessie is released under the [Apache License 2.0](LICENSE).
