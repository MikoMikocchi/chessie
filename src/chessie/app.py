"""Application entry point."""

from __future__ import annotations

from chessie.ui.bootstrap import run_application


def main(argv: list[str] | None = None) -> int:
    """Launch the Chessie application and return the Qt exit code."""
    return run_application(argv)


if __name__ == "__main__":
    raise SystemExit(main())
