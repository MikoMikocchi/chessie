"""GameController — the central orchestrator of a chess game.

Coordinates: Players, Clock, GameState, MoveGenerator.
Emits events via simple callbacks so the UI / tests can subscribe.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from chessie.core.enums import Color, GameResult
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.game.clock import Clock, ClockSnapshot
from chessie.game.interfaces import (
    DrawOffer,
    GameEndReason,
    GamePhase,
    IGameController,
    IPlayer,
    TimeControl,
)
from chessie.game.state import GameState

# ── Event definitions ────────────────────────────────────────────────────────

MoveCallback = Callable[[Move, str, "GameState"], None]  # move, san, state
GameOverCallback = Callable[[GameResult], None]
PhaseCallback = Callable[[GamePhase], None]
ClockTickCallback = Callable[[Color, float], None]  # color, remaining


@dataclass
class GameEvents:
    """Observable callbacks. Multiple handlers per event."""

    on_move: list[MoveCallback] = field(default_factory=list)
    on_game_over: list[GameOverCallback] = field(default_factory=list)
    on_phase_changed: list[PhaseCallback] = field(default_factory=list)


# ── Controller ───────────────────────────────────────────────────────────────


class GameController(IGameController):
    """Orchestrates a full chess game: validates moves, manages clock,
    switches turns, notifies listeners.

    Thread-safety: methods are designed to be called from a single thread
    (the main/UI thread).  AI results arrive via ``submit_move`` which
    the ``EngineWorker`` will call (in future) via a signal/slot on the
    main thread.
    """

    __slots__ = (
        "_state",
        "_players",
        "_clock",
        "_clock_history",
        "events",
    )

    def __init__(self) -> None:
        self._state = GameState()
        self._players: dict[Color, IPlayer] = {}
        self._clock: Clock | None = None
        self._clock_history: list[ClockSnapshot] = []
        self.events = GameEvents()

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def clock(self) -> Clock | None:
        return self._clock

    @property
    def current_player(self) -> IPlayer | None:
        color = self._state.side_to_move
        return self._players.get(color)

    def player(self, color: Color) -> IPlayer | None:
        return self._players.get(color)

    # ── IGameController impl ─────────────────────────────────────────────

    def new_game(
        self,
        white: IPlayer,
        black: IPlayer,
        time_control: TimeControl | None = None,
        fen: str | None = None,
    ) -> None:
        self._players = {Color.WHITE: white, Color.BLACK: black}

        if time_control is not None:
            self._clock = Clock(time_control)
        else:
            self._clock = None
        self._clock_history = []

        self._state = GameState()
        self._state.setup(fen)

        self._emit_phase(GamePhase.AWAITING_MOVE)
        self._prompt_current_player()

    def submit_move(self, move: Move) -> bool:
        if self._state.is_game_over:
            return False
        if self._state.phase not in (GamePhase.AWAITING_MOVE, GamePhase.THINKING):
            return False

        # Validate legality
        gen = MoveGenerator(self._state.position)
        legal = gen.generate_legal_moves()
        if move not in legal:
            return False

        # Clock: freeze mover's time, check flag, then apply increment.
        clock_snapshot: ClockSnapshot | None = None
        if self._clock is not None:
            color = self._state.side_to_move
            clock_snapshot = self._clock.snapshot()
            self._clock.stop()
            if self._clock.is_flag_fallen(color):
                self._state.flag_fall(color)
                self._emit_game_over(self._state.result)
                return False
            self._clock.add_increment(color)

        # Apply
        record = self._state.apply_move(move)
        if clock_snapshot is not None:
            self._clock_history.append(clock_snapshot)

        # Notify listeners
        self._emit_move(move, record.san)

        if self._state.is_game_over:
            self._emit_game_over(self._state.result)
            return True

        # Switch clock and prompt next player
        if self._clock is not None:
            self._clock.switch()

        self._prompt_current_player()
        return True

    def resign(self, color: Color) -> None:
        if self._state.is_game_over:
            return
        if self._clock:
            self._clock.stop()
        self._state.resign(color)
        self._emit_game_over(self._state.result)

    def offer_draw(self, color: Color) -> None:
        if self._state.is_game_over:
            return
        if self._state.draw_offer == DrawOffer.OFFERED:
            return
        self._state.draw_offer = DrawOffer.OFFERED
        self._state.draw_offer_by = color

    def accept_draw(self, color: Color) -> None:
        if self._state.draw_offer != DrawOffer.OFFERED:
            return
        if self._state.draw_offer_by in (None, color):
            return
        if self._clock:
            self._clock.stop()
        self._state.draw_offer = DrawOffer.ACCEPTED
        self._state.draw_offer_by = None
        self._state.set_draw(GameEndReason.DRAW_AGREED)
        self._emit_game_over(GameResult.DRAW)

    def claim_draw(self, color: Color) -> bool:
        if self._state.is_game_over:
            return False
        if color != self._state.side_to_move:
            return False
        if self._clock:
            self._clock.stop()
        if not self._state.claim_draw_by_rule():
            if self._clock:
                cp = self.current_player
                if cp is not None and not self._clock.is_running:
                    self._clock.start(cp.color)
            return False
        self._emit_game_over(GameResult.DRAW)
        return True

    def decline_draw(self) -> None:
        self._state.draw_offer = DrawOffer.DECLINED
        self._state.draw_offer_by = None

    def undo_move(self) -> bool:
        if self._state.is_game_over or not self._state.move_history:
            return False

        # Cancel AI if it's thinking
        cp = self.current_player
        if cp and not cp.is_human:
            cp.cancel()

        self._state.undo_last_move()
        if self._clock is not None:
            self._clock.stop()
            if self._clock_history:
                self._clock.restore(self._clock_history.pop())
        self._emit_phase(GamePhase.AWAITING_MOVE)
        self._prompt_current_player()
        return True

    # ── Internal helpers ─────────────────────────────────────────────────

    def _prompt_current_player(self) -> None:
        """Ask the current player to move."""
        cp = self.current_player
        if cp is None:
            return

        if cp.is_human:
            self._state.phase = GamePhase.AWAITING_MOVE
            self._emit_phase(GamePhase.AWAITING_MOVE)
            if self._clock and not self._clock.is_running:
                self._clock.start(cp.color)
        else:
            self._state.phase = GamePhase.THINKING
            self._emit_phase(GamePhase.THINKING)
            if self._clock and not self._clock.is_running:
                self._clock.start(cp.color)
            cp.request_move(self._state.position)

    def _emit_move(self, move: Move, san: str) -> None:
        for cb in self.events.on_move:
            cb(move, san, self._state)

    def _emit_game_over(self, result: GameResult) -> None:
        self._emit_phase(GamePhase.GAME_OVER)
        for cb in self.events.on_game_over:
            cb(result)

    def _emit_phase(self, phase: GamePhase) -> None:
        for cb in self.events.on_phase_changed:
            cb(phase)
