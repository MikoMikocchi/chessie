"""MainWindow PGN actions and termination conversion helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chessie.game.interfaces import GameEndReason
from chessie.ui.i18n import t
from chessie.ui.pgn_io import load_pgn_file, save_pgn_file


def on_open_pgn(
    host: Any,
    *,
    file_dialog_cls: type[Any],
    message_box_cls: type[Any],
) -> None:
    file_path, _ = file_dialog_cls.getOpenFileName(
        host,
        t().open_pgn_title,
        "",
        f"{t().pgn_filter};;{t().pgn_all_files}",
    )
    if not file_path:
        return

    try:
        load_pgn_file(host, Path(file_path))
        host._status_label.setText(
            t().status_loaded_pgn.format(name=Path(file_path).name)
        )
    except Exception as exc:
        host._is_loading_pgn = False
        message_box_cls.warning(
            host,
            t().open_pgn_title,
            t().open_pgn_failed.format(exc=exc),
        )


def on_save_pgn(
    host: Any,
    *,
    file_dialog_cls: type[Any],
    message_box_cls: type[Any],
) -> None:
    file_path, _ = file_dialog_cls.getSaveFileName(
        host,
        t().save_pgn_title,
        "game.pgn",
        f"{t().pgn_filter};;{t().pgn_all_files}",
    )
    if not file_path:
        return

    try:
        save_path = save_pgn_file(host, Path(file_path))
        host._status_label.setText(t().status_saved_pgn.format(name=save_path.name))
    except Exception as exc:
        message_box_cls.warning(
            host,
            t().save_pgn_title,
            t().save_pgn_failed.format(exc=exc),
        )


def termination_from_end_reason(reason: GameEndReason) -> str:
    mapping = {
        GameEndReason.NONE: "unterminated",
        GameEndReason.CHECKMATE: "checkmate",
        GameEndReason.STALEMATE: "stalemate",
        GameEndReason.RESIGN: "resignation",
        GameEndReason.FLAG_FALL: "time forfeit",
        GameEndReason.DRAW_AGREED: "draw agreed",
        GameEndReason.DRAW_RULE: "draw rule",
    }
    return mapping.get(reason, "unterminated")


def end_reason_from_termination(termination: str | None) -> GameEndReason:
    if termination is None:
        return GameEndReason.NONE

    normalized = " ".join(
        termination.strip().lower().replace("_", " ").replace("-", " ").split()
    )
    mapping = {
        "checkmate": GameEndReason.CHECKMATE,
        "mate": GameEndReason.CHECKMATE,
        "stalemate": GameEndReason.STALEMATE,
        "resign": GameEndReason.RESIGN,
        "resigned": GameEndReason.RESIGN,
        "resignation": GameEndReason.RESIGN,
        "time forfeit": GameEndReason.FLAG_FALL,
        "flag fall": GameEndReason.FLAG_FALL,
        "time": GameEndReason.FLAG_FALL,
        "draw agreed": GameEndReason.DRAW_AGREED,
        "draw agreement": GameEndReason.DRAW_AGREED,
        "agreement": GameEndReason.DRAW_AGREED,
        "draw rule": GameEndReason.DRAW_RULE,
        "threefold repetition": GameEndReason.DRAW_RULE,
        "fivefold repetition": GameEndReason.DRAW_RULE,
        "50 move rule": GameEndReason.DRAW_RULE,
        "75 move rule": GameEndReason.DRAW_RULE,
        "insufficient material": GameEndReason.DRAW_RULE,
        "unterminated": GameEndReason.NONE,
        "normal": GameEndReason.NONE,
    }
    return mapping.get(normalized, GameEndReason.NONE)
