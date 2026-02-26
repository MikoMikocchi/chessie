"""PGN import/export helpers used by the main window."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from chessie.core.enums import Color, GameResult
from chessie.core.notation import (
    STARTING_FEN,
    build_pgn,
    game_result_from_pgn,
    parse_pgn_game,
    parse_san,
    pgn_result_token,
)
from chessie.game.controller import GameController
from chessie.game.interfaces import GameEndReason, GamePhase, TimeControl
from chessie.game.player import HumanPlayer


class MainWindowPgnHost(Protocol):
    """Subset of MainWindow API required for PGN import/export."""

    _controller: GameController
    _is_loading_pgn: bool
    _pgn_move_comments: list[str | None]

    def _cancel_ai_search(self) -> None: ...

    def _connect_game_events(self) -> None: ...

    def _after_new_game(self) -> None: ...

    def _sync_board_interactivity(self) -> None: ...

    def _update_status(self) -> None: ...

    def _on_game_over(self, result: GameResult) -> None: ...

    def _termination_from_end_reason(self, reason: GameEndReason) -> str: ...

    def _end_reason_from_termination(
        self, termination: str | None
    ) -> GameEndReason: ...


def load_pgn_file(host: MainWindowPgnHost, file_path: Path) -> None:
    """Load a PGN game from disk and apply it to the current controller."""
    pgn_text = file_path.read_text(encoding="utf-8")
    parsed = parse_pgn_game(pgn_text)
    headers = parsed.headers
    result_token = parsed.result_token

    start_fen = STARTING_FEN
    if headers.get("SetUp") == "1" and "FEN" in headers:
        start_fen = headers["FEN"]

    host._cancel_ai_search()
    white = HumanPlayer(Color.WHITE, headers.get("White", "White"))
    black = HumanPlayer(Color.BLACK, headers.get("Black", "Black"))

    host._connect_game_events()
    host._controller.new_game(
        white=white,
        black=black,
        time_control=TimeControl.unlimited(),
        fen=start_fen,
    )
    host._after_new_game()

    host._is_loading_pgn = True
    try:
        for pgn_move in parsed.moves:
            move = parse_san(host._controller.state.position, pgn_move.san)
            if not host._controller.submit_move(move):
                raise ValueError(f"Illegal move in PGN: {pgn_move.san}")

        host._pgn_move_comments = [
            pgn_move.comment or None for pgn_move in parsed.moves
        ]

        declared_result = game_result_from_pgn(result_token)
        if (
            declared_result != GameResult.IN_PROGRESS
            and not host._controller.state.is_game_over
        ):
            state = host._controller.state
            state.result = declared_result
            state.phase = GamePhase.GAME_OVER
            state.end_reason = host._end_reason_from_termination(
                headers.get("Termination")
            )
            host._on_game_over(declared_result)
    finally:
        host._is_loading_pgn = False

    host._sync_board_interactivity()
    host._update_status()


def save_pgn_file(host: MainWindowPgnHost, file_path: Path) -> Path:
    """Save the current game state to a PGN file path."""
    save_path = file_path
    if save_path.suffix.lower() != ".pgn":
        save_path = save_path.with_suffix(".pgn")

    state = host._controller.state
    white_player = host._controller.player(Color.WHITE)
    black_player = host._controller.player(Color.BLACK)
    result_token = pgn_result_token(state.result)

    headers: dict[str, str] = {
        "Event": "Casual Game",
        "Site": "Chessie",
        "Date": datetime.now().strftime("%Y.%m.%d"),
        "Round": "-",
        "White": white_player.name if white_player is not None else "White",
        "Black": black_player.name if black_player is not None else "Black",
        "Result": result_token,
        "Termination": host._termination_from_end_reason(state.end_reason),
    }
    if state.start_fen != STARTING_FEN:
        headers["SetUp"] = "1"
        headers["FEN"] = state.start_fen

    comments = host._pgn_move_comments[: len(state.move_history)]
    if len(comments) < len(state.move_history):
        comments += [None] * (len(state.move_history) - len(comments))

    pgn_text = build_pgn(
        headers=headers,
        sans=[record.san for record in state.move_history],
        result_token=result_token,
        comments=comments,
    )
    save_path.write_text(pgn_text, encoding="utf-8")
    return save_path
