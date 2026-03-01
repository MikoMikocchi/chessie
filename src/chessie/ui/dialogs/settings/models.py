"""Settings data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppSettings:
    """All user-configurable settings."""

    # General
    language: str = "English"

    # Board
    board_theme: str = "Classic"
    show_coordinates: bool = True
    show_legal_moves: bool = True
    animate_moves: bool = True
    use_figurine_notation: bool = True

    # Sound
    sound_enabled: bool = True
    sound_volume: int = 80  # 0–100

    # Engine
    engine_depth: int = 4
    engine_time_ms: int = 900
    analysis_depth: int = 4
    analysis_time_ms: int = 200
