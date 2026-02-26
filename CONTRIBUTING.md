# Contributing to Chessie

Thanks for helping improve Chessie.

## Development Setup

1. Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository and enter it:

```bash
git clone https://github.com/MikoMikocchi/chessie.git
cd chessie
```

3. Create a virtual environment and install dependencies:

```bash
uv sync --all-groups
```

4. (Recommended) Install pre-commit hooks:

```bash
uv run pre-commit install
```

## Running the App

```bash
uv run chessie
```

## Running Tests

Run the full test suite:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

Run only fast tests:

```bash
uv run pytest -m "not slow"
```

On Linux, GUI tests may require an X server. If needed, run tests with `xvfb`:

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1024x768x24" uv run pytest --cov=src --cov-report=term-missing
```

## Quality Checks

Before opening a PR, run the same checks used in CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run bandit -c pyproject.toml -r src
uv build
```

You can also run all pre-commit hooks manually:

```bash
uv run pre-commit run --all-files
```

## Project Layout

- `src/chessie/core`: chess rules, board state, move generation, and notation
- `src/chessie/game`: game flow, clock, and controller logic
- `src/chessie/engine`: engine/search integration
- `src/chessie/ui`: PyQt6 UI and related components
- `tests`: unit and integration tests mirroring source modules

## Pull Requests

1. Keep changes focused and small when possible.
2. Add or update tests for behavioral changes.
3. Update documentation when behavior or developer workflow changes.
4. Ensure all checks pass locally before opening the PR.
5. In your PR description, explain what changed, why it changed, and how it was tested.

## Code of Conduct

By participating, you agree to follow the
[Code of Conduct](./CODE_OF_CONDUCT.md).
