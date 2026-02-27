"""Internationalisation strings for Chessie UI.

Usage::

    from chessie.ui.i18n import t, set_language

    set_language("Russian")
    print(t().resign)          # "Сдаться"
    print(t().white_wins_by("checkmate"))
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strings:
    # ── Main window ──────────────────────────────────────────────────────
    menu_game: str
    menu_new_game: str
    menu_open_pgn: str
    menu_save_pgn: str
    menu_analyze_game: str
    menu_flip_board: str
    menu_quit: str
    menu_settings: str
    menu_settings_action: str

    status_ready: str
    status_game_over: str  # prefix, e.g. "Game over - "
    status_loaded_pgn: str  # e.g. "Loaded PGN: {name}"
    status_saved_pgn: str  # e.g. "Saved PGN: {name}"
    status_engine_error: str  # e.g. "Engine error: {msg}"
    status_draw_declined: str
    status_analysis_started: str  # e.g. "Analysis started (N moves)..."
    status_analyzing_progress: str  # e.g. "Analyzing move X/Y..."
    status_analysis_done: str  # e.g. "Analysis complete. White ACPL: ... "
    status_analysis_failed: str  # e.g. "Analysis failed: {msg}"
    status_analysis_cancelled: str
    status_analysis_no_moves: str

    # Game-over reasons
    game_over_title: str
    draw_stalemate: str
    draw_agreed: str
    draw_rule: str
    draw_generic: str
    wins_checkmate: str  # "{color} wins by checkmate."
    wins_resign: str  # "{color} wins by resignation."
    wins_time: str  # "{color} wins on time."
    wins_generic: str  # "{color} wins."
    color_white: str
    color_black: str

    # Resign dialog
    resign_title: str
    resign_confirm: str

    # Draw-offer dialog
    draw_offer_title: str
    draw_offer_question: str  # "{color} offers a draw. Accept?"

    # PGN dialogs
    pgn_filter: str
    pgn_all_files: str
    open_pgn_title: str
    open_pgn_failed: str  # "Failed to load PGN:\n{exc}"
    save_pgn_title: str
    save_pgn_failed: str  # "Failed to save PGN:\n{exc}"

    # Phase names (map from GamePhase int name → display)
    phase_not_started: str
    phase_awaiting_move: str
    phase_thinking: str
    phase_game_over: str

    # ── ClockWidget ──────────────────────────────────────────────────────
    clock_white: str
    clock_black: str

    # ── MovePanel ────────────────────────────────────────────────────────
    moves_header: str

    # ── ControlPanel ─────────────────────────────────────────────────────
    btn_new_game: str
    btn_flip: str
    btn_undo: str
    btn_resign: str
    btn_draw: str

    # ── NewGameDialog ────────────────────────────────────────────────────
    new_game_title: str
    new_game_opponent: str
    new_game_human: str
    new_game_ai: str
    new_game_play_as: str
    new_game_white: str
    new_game_black: str
    new_game_time_control: str
    new_game_unlimited: str

    # ── PromotionDialog ──────────────────────────────────────────────────
    promote_title: str
    promote_label: str

    # ── SettingsDialog ───────────────────────────────────────────────────
    settings_title: str
    settings_board: str
    settings_sound: str
    settings_engine: str
    settings_language: str

    # Board page
    settings_board_theme: str
    settings_show_coords: str
    settings_show_legal: str
    settings_animate_moves: str
    settings_move_notation: str
    settings_move_notation_icons: str
    settings_move_notation_letters: str

    # Sound page
    settings_sound_enable: str
    settings_sound_volume: str

    # Engine page
    settings_engine_depth: str
    settings_engine_time: str
    settings_engine_depth_suffix: str
    settings_engine_time_suffix: str
    settings_engine_note: str

    # ── AnalysisDialog ────────────────────────────────────────────────────
    analysis_title: str
    analysis_summary: str
    analysis_hint_jump: str
    analysis_col_move: str
    analysis_col_played: str
    analysis_col_best: str
    analysis_col_cp_loss: str
    analysis_col_verdict: str


# ── Built-in locales ─────────────────────────────────────────────────────────

_EN = Strings(
    menu_game="&Game",
    menu_new_game="&New Game...",
    menu_open_pgn="&Open PGN...",
    menu_save_pgn="&Save PGN...",
    menu_analyze_game="&Analyze Game...",
    menu_flip_board="&Flip Board",
    menu_quit="&Quit",
    menu_settings="&Settings",
    menu_settings_action="&Settings...",
    status_ready="Ready",
    status_game_over="Game over — ",
    status_loaded_pgn="Loaded PGN: {name}",
    status_saved_pgn="Saved PGN: {name}",
    status_engine_error="Engine error: {msg}",
    status_draw_declined="Draw offer declined by Chessie AI.",
    status_analysis_started="Analysis started ({total} moves)...",
    status_analyzing_progress="Analyzing move {done}/{total}...",
    status_analysis_done="Analysis complete. White ACPL: {white_avg}, Black ACPL: {black_avg}",
    status_analysis_failed="Analysis failed: {msg}",
    status_analysis_cancelled="Analysis cancelled.",
    status_analysis_no_moves="No moves to analyze.",
    game_over_title="Game Over",
    draw_stalemate="Draw by stalemate.",
    draw_agreed="Draw by agreement.",
    draw_rule="Draw by rule.",
    draw_generic="Draw.",
    wins_checkmate="{color} wins by checkmate.",
    wins_resign="{color} wins by resignation.",
    wins_time="{color} wins on time.",
    wins_generic="{color} wins.",
    color_white="White",
    color_black="Black",
    resign_title="Resign",
    resign_confirm="Are you sure you want to resign?",
    draw_offer_title="Draw Offer",
    draw_offer_question="{color} offers a draw. Accept?",
    pgn_filter="PGN Files (*.pgn)",
    pgn_all_files="All Files (*)",
    open_pgn_title="Open PGN",
    open_pgn_failed="Failed to load PGN:\n{exc}",
    save_pgn_title="Save PGN",
    save_pgn_failed="Failed to save PGN:\n{exc}",
    phase_not_started="Not started",
    phase_awaiting_move="Awaiting move",
    phase_thinking="Thinking",
    phase_game_over="Game over",
    clock_white="White",
    clock_black="Black",
    moves_header="Moves",
    btn_new_game="New Game",
    btn_flip="⟲ Flip",
    btn_undo="↩ Undo",
    btn_resign="Resign",
    btn_draw="½ Draw",
    new_game_title="New Game",
    new_game_opponent="Opponent:",
    new_game_human="Human",
    new_game_ai="AI",
    new_game_play_as="Play as:",
    new_game_white="♔ White",
    new_game_black="♚ Black",
    new_game_time_control="Time control:",
    new_game_unlimited="Unlimited",
    promote_title="Promote pawn",
    promote_label="Choose promotion piece:",
    settings_title="Settings",
    settings_board="Board",
    settings_sound="Sound",
    settings_engine="Engine",
    settings_language="Language",
    settings_board_theme="Board theme:",
    settings_show_coords="Show coordinates:",
    settings_show_legal="Show legal moves:",
    settings_animate_moves="Animate moves:",
    settings_move_notation="Move notation:",
    settings_move_notation_icons="Figurines",
    settings_move_notation_letters="Letters (SAN)",
    settings_sound_enable="Enable sounds:",
    settings_sound_volume="Volume:",
    settings_engine_depth="Search depth:",
    settings_engine_time="Time limit per move:",
    settings_engine_depth_suffix=" ply",
    settings_engine_time_suffix=" ms",
    settings_engine_note="Changes take effect from the next game.",
    analysis_title="Game Analysis",
    analysis_summary="White ACPL: {white_avg} (blunders: {white_blunders}) | Black ACPL: {black_avg} (blunders: {black_blunders})",
    analysis_hint_jump="Double-click a row to jump to that move on the board.",
    analysis_col_move="Move",
    analysis_col_played="Played",
    analysis_col_best="Best",
    analysis_col_cp_loss="CPL",
    analysis_col_verdict="Verdict",
)

_RU = Strings(
    menu_game="&Игра",
    menu_new_game="&Новая игра...",
    menu_open_pgn="&Открыть PGN...",
    menu_save_pgn="&Сохранить PGN...",
    menu_analyze_game="&Анализ партии...",
    menu_flip_board="&Перевернуть доску",
    menu_quit="&Выход",
    menu_settings="&Настройки",
    menu_settings_action="&Настройки...",
    status_ready="Готово",
    status_game_over="Конец игры — ",
    status_loaded_pgn="Загружен PGN: {name}",
    status_saved_pgn="Сохранён PGN: {name}",
    status_engine_error="Ошибка движка: {msg}",
    status_draw_declined="Предложение ничьей отклонено Chessie AI.",
    status_analysis_started="Анализ запущен ({total} ходов)...",
    status_analyzing_progress="Анализ хода {done}/{total}...",
    status_analysis_done="Анализ завершён. ACPL белых: {white_avg}, ACPL чёрных: {black_avg}",
    status_analysis_failed="Ошибка анализа: {msg}",
    status_analysis_cancelled="Анализ отменён.",
    status_analysis_no_moves="Нет ходов для анализа.",
    game_over_title="Конец игры",
    draw_stalemate="Пат.",
    draw_agreed="Ничья по соглашению.",
    draw_rule="Ничья по правилам.",
    draw_generic="Ничья.",
    wins_checkmate="{color} побеждает матом.",
    wins_resign="{color} побеждает — соперник сдался.",
    wins_time="{color} побеждает по времени.",
    wins_generic="{color} побеждает.",
    color_white="Белые",
    color_black="Чёрные",
    resign_title="Сдаться",
    resign_confirm="Вы уверены, что хотите сдаться?",
    draw_offer_title="Предложение ничьей",
    draw_offer_question="{color} предлагает ничью. Принять?",
    pgn_filter="Файлы PGN (*.pgn)",
    pgn_all_files="Все файлы (*)",
    open_pgn_title="Открыть PGN",
    open_pgn_failed="Не удалось загрузить PGN:\n{exc}",
    save_pgn_title="Сохранить PGN",
    save_pgn_failed="Не удалось сохранить PGN:\n{exc}",
    phase_not_started="Не начата",
    phase_awaiting_move="Ожидание хода",
    phase_thinking="Расчёт",
    phase_game_over="Конец игры",
    clock_white="Белые",
    clock_black="Чёрные",
    moves_header="Ходы",
    btn_new_game="Новая игра",
    btn_flip="⟲ Перевернуть",
    btn_undo="↩ Отмена",
    btn_resign="Сдаться",
    btn_draw="½ Ничья",
    new_game_title="Новая игра",
    new_game_opponent="Соперник:",
    new_game_human="Человек",
    new_game_ai="ИИ",
    new_game_play_as="Играть за:",
    new_game_white="♔ Белые",
    new_game_black="♚ Чёрные",
    new_game_time_control="Контроль времени:",
    new_game_unlimited="Без ограничений",
    promote_title="Превращение пешки",
    promote_label="Выберите фигуру для превращения:",
    settings_title="Настройки",
    settings_board="Доска",
    settings_sound="Звук",
    settings_engine="Движок",
    settings_language="Язык",
    settings_board_theme="Тема доски:",
    settings_show_coords="Показывать координаты:",
    settings_show_legal="Показывать возможные ходы:",
    settings_animate_moves="Анимация ходов:",
    settings_move_notation="Нотация ходов:",
    settings_move_notation_icons="Иконки фигур",
    settings_move_notation_letters="Буквы (SAN)",
    settings_sound_enable="Включить звуки:",
    settings_sound_volume="Громкость:",
    settings_engine_depth="Глубина поиска:",
    settings_engine_time="Лимит времени на ход:",
    settings_engine_depth_suffix=" пл.",
    settings_engine_time_suffix=" мс",
    settings_engine_note="Изменения вступят в силу с начала следующей игры.",
    analysis_title="Анализ партии",
    analysis_summary="ACPL белых: {white_avg} (грубых: {white_blunders}) | ACPL чёрных: {black_avg} (грубых: {black_blunders})",
    analysis_hint_jump="Двойной клик по строке — перейти к ходу на доске.",
    analysis_col_move="Ход",
    analysis_col_played="Сыграно",
    analysis_col_best="Лучший",
    analysis_col_cp_loss="CPL",
    analysis_col_verdict="Оценка",
)

_LOCALES: dict[str, Strings] = {
    "English": _EN,
    "Russian": _RU,
}

LANGUAGES: list[str] = list(_LOCALES.keys())

_current: Strings = _EN


def t() -> Strings:
    """Return the active locale strings."""
    return _current


def set_language(language: str) -> None:
    """Switch the global locale. Unknown names fall back to English."""
    global _current
    _current = _LOCALES.get(language, _EN)
