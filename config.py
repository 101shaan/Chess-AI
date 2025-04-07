"""
Configuration settings for the chess application
"""
from typing import Dict, Tuple, Any, Final
import os

# Window settings
WINDOW_WIDTH: Final[int] = 1000
WINDOW_HEIGHT: Final[int] = 800
WINDOW_TITLE: Final[str] = "Chess AI - Professional Edition"
FPS: Final[int] = 60

# Board settings
BOARD_SIZE: Final[int] = 560  # Size of the board in pixels
SQUARE_SIZE: Final[int] = BOARD_SIZE // 8
BOARD_OFFSET_X: Final[int] = (WINDOW_WIDTH - BOARD_SIZE) // 2
BOARD_OFFSET_Y: Final[int] = (WINDOW_HEIGHT - BOARD_SIZE) // 4

# Colors
COLOR_WHITE: Final[Tuple[int, int, int]] = (238, 238, 210)
COLOR_BLACK: Final[Tuple[int, int, int]] = (118, 150, 86)
COLOR_DARK_GRAY: Final[Tuple[int, int, int]] = (40, 40, 40)
COLOR_LIGHT_GRAY: Final[Tuple[int, int, int]] = (60, 60, 60)
COLOR_HIGHLIGHT: Final[Tuple[int, int, int, int]] = (255, 255, 0, 100)  # Yellow with alpha
COLOR_MOVE_INDICATOR: Final[Tuple[int, int, int, int]] = (0, 128, 255, 100)  # Blue with alpha
COLOR_CHECK: Final[Tuple[int, int, int, int]] = (255, 0, 0, 100)  # Red with alpha
COLOR_TEXT: Final[Tuple[int, int, int]] = (220, 220, 220)
COLOR_BUTTON: Final[Tuple[int, int, int]] = (70, 70, 70)
COLOR_BUTTON_HOVER: Final[Tuple[int, int, int]] = (90, 90, 90)

# Engine configuration
DEFAULT_ENGINE_PATH: Final[str] = os.path.join(os.path.dirname(__file__), "engine", "stockfish.exe")
DEFAULT_PLAYER_ELO: Final[int] = 1200
DEFAULT_AI_ELO: Final[int] = 1200

# Stockfish settings
MIN_SKILL_LEVEL: Final[int] = 0   # Corresponds to ~800 ELO
MAX_SKILL_LEVEL: Final[int] = 20  # Corresponds to ~2000 ELO
DEFAULT_SKILL_LEVEL: Final[int] = 10

# Game settings
DEFAULT_TIME_CONTROL: Final[int] = 10  # minutes per player
ANIMATION_SPEED: Final[float] = 0.3  # seconds per animation

# Piece mapping: converts chess.Board piece symbols to image keys
PIECE_MAPPING: Final[Dict[str, str]] = {
    'P': 'wP', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wQ', 'K': 'wK',
    'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
}

# Game modes
GAME_MODE_PLAY: Final[str] = "play"
GAME_MODE_MENU: Final[str] = "menu"
GAME_MODE_RESULT: Final[str] = "result"