"""Game state machine — tracks phase transitions and move history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from chessy.core.enums import Color, GameResult
from chessy.core.move_generator import MoveGenerator
from chessy.core.notation import STARTING_FEN, position_from_fen, position_to_fen
from chessy.core.rules import Rules
from chessy.game.interfaces import DrawOffer, GamePhase

if TYPE_CHECKING:
    from chessy.core.move import Move
    from chessy.core.position import Position


@dataclass
class MoveRecord:
    """A single entry in the move history."""

    move: Move
    san: str
    fen_after: str
    was_check: bool = False
    was_capture: bool = False


@dataclass
class GameState:
    """Manages game lifecycle: phase, result, move history, draw offers.

    This is a pure data/logic class — no threading, no UI.
    """

    position: Position = field(init=False)
    phase: GamePhase = field(default=GamePhase.NOT_STARTED, init=False)
    result: GameResult = field(default=GameResult.IN_PROGRESS, init=False)
    draw_offer: DrawOffer = field(default=DrawOffer.NONE, init=False)
    move_history: list[MoveRecord] = field(default_factory=list, init=False)
    start_fen: str = field(default=STARTING_FEN, init=False)

    # ── Initialisation ───────────────────────────────────────────────────

    def setup(self, fen: str | None = None) -> None:
        """Initialise (or reset) the game."""
        self.start_fen = fen or STARTING_FEN
        self.position = position_from_fen(self.start_fen)
        self.phase = GamePhase.AWAITING_MOVE
        self.result = GameResult.IN_PROGRESS
        self.draw_offer = DrawOffer.NONE
        self.move_history.clear()

    # ── Move application ─────────────────────────────────────────────────

    def apply_move(self, move: Move) -> MoveRecord:
        """Apply a validated move and return the history record.

        Caller is responsible for legality check.
        """
        from chessy.core.notation import move_to_san

        board = self.position.board
        was_capture = board[move.to_sq] is not None

        san = move_to_san(self.position, move)
        self.position.make_move(move)

        fen_after = position_to_fen(self.position)
        gen = MoveGenerator(self.position)
        was_check = gen.is_in_check(self.position.side_to_move)

        record = MoveRecord(
            move=move,
            san=san,
            fen_after=fen_after,
            was_check=was_check,
            was_capture=was_capture,
        )
        self.move_history.append(record)

        # Check for game-ending conditions
        self._check_game_over()
        self.draw_offer = DrawOffer.NONE  # any move cancels a pending offer

        return record

    def undo_last_move(self) -> Move | None:
        """Undo the last move. Returns the undone Move, or None if empty."""
        if not self.move_history:
            return None

        record = self.move_history.pop()
        self.position.unmake_move(record.move)

        # Reset result if we un-did a game-ending move
        if self.result != GameResult.IN_PROGRESS:
            self.result = GameResult.IN_PROGRESS
            self.phase = GamePhase.AWAITING_MOVE

        return record.move

    # ── Resignation / draw ───────────────────────────────────────────────

    def resign(self, color: Color) -> None:
        self.result = (
            GameResult.BLACK_WINS if color == Color.WHITE else GameResult.WHITE_WINS
        )
        self.phase = GamePhase.GAME_OVER

    def set_draw(self) -> None:
        self.result = GameResult.DRAW
        self.phase = GamePhase.GAME_OVER

    def flag_fall(self, color: Color) -> None:
        """Time ran out for *color*."""
        self.result = (
            GameResult.BLACK_WINS if color == Color.WHITE else GameResult.WHITE_WINS
        )
        self.phase = GamePhase.GAME_OVER

    # ── Query helpers ────────────────────────────────────────────────────

    @property
    def side_to_move(self) -> Color:
        return self.position.side_to_move

    @property
    def is_game_over(self) -> bool:
        return self.phase == GamePhase.GAME_OVER

    @property
    def ply_count(self) -> int:
        """Number of half-moves played."""
        return len(self.move_history)

    @property
    def fullmove_display(self) -> int:
        """Current full-move number for display."""
        return (self.ply_count // 2) + 1

    def legal_moves(self) -> list[Move]:
        """Legal moves in the current position."""
        gen = MoveGenerator(self.position)
        return gen.generate_legal_moves()

    # ── Internal ─────────────────────────────────────────────────────────

    def _check_game_over(self) -> None:
        result = Rules.game_result(self.position)
        if result != GameResult.IN_PROGRESS:
            self.result = result
            self.phase = GamePhase.GAME_OVER
