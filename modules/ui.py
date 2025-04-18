"""
this handles the user interface for the chess game:
- manages drawing the board, pieces, and ui elements
- supports animations, themes, and user interactions
"""
import pygame
import chess
import os
import math
from typing import List, Dict, Tuple, Optional, Any, Union
import time

# Import config settings
from config import *

# Board constants
SQUARE_SIZE = 65
BOARD_SIZE = SQUARE_SIZE * 8
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50  # Reduced from 80 to move the board upward

# Window constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Colors
COLOR_LIGHT_SQUARE = (240, 217, 181)
COLOR_DARK_SQUARE = (181, 136, 99)
COLOR_WHITE = (238, 238, 210)  # Light squares
COLOR_BLACK = (118, 150, 86)   # Dark squares
COLOR_HIGHLIGHT = (255, 255, 100, 100)  # Selected square highlight
COLOR_MOVE = (255, 255, 0, 100)  # Valid move highlight
COLOR_SELECTED = (255, 255, 100, 120)  # Selected square highlight
COLOR_MOVE_INDICATOR = (255, 255, 0, 120)  # Valid move highlight with better visibility
COLOR_CHECK_INDICATOR = (255, 0, 0, 100)
COLOR_BACKGROUND = (40, 44, 52)  # Dark background
COLOR_TEXT = (220, 220, 220)  # Light text
COLOR_BUTTON = (60, 66, 80)  # Button color
COLOR_BUTTON_HOVER = (80, 86, 100)  # Button hover color
COLOR_LIGHT_GRAY = (100, 100, 100)

# Background images
BACKGROUND_IMAGES = {
    "default": None,  # Use solid background
    "wooden": "assets/background_images/wooden.jpg",
    "dark": "assets/background_images/dark.png",
    "royal": "assets/background_images/royal.jpg",
    "moonlight": "assets/background_images/moonlight.jpg"
}

# Animation constants
ANIMATION_DURATION = 0.3  # seconds

# Font constants
FONT_SIZE_LARGE = 32
FONT_SIZE_MEDIUM = 24
FONT_SIZE_SMALL = 18

class Button:
    """Button class for UI elements"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int = 24) -> None:
        """
        Initialize a button
        
        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Button width
            height: Button height
            text: Button text
            font_size: Font size for text
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont("Arial", font_size)
        self.color = COLOR_BUTTON
        self.hover_color = COLOR_BUTTON_HOVER
        self.text_color = COLOR_TEXT
        self.hover = False
    
    def update_text(self, text: str) -> None:
        """
        Update the button text
        
        Args:
            text: New button text
        """
        self.text = text
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the button on the surface
        
        Args:
            surface: Surface to draw on
        """
        color = self.hover_color if self.hover else self.color
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect)
        
        # Draw button border
        pygame.draw.rect(surface, (50, 50, 50), self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Update button state based on mouse position
        
        Args:
            mouse_pos: Current mouse position
        """
        self.hover = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, pos: Tuple[int, int]) -> bool:
        """
        Check if button is clicked
        
        Args:
            pos: Click position
            
        Returns:
            True if button is clicked, False otherwise
        """
        return self.rect.collidepoint(pos)

class Animation:
    """Animation class for smooth piece movement"""
    
    def __init__(self, move: chess.Move, board: chess.Board, ui: 'ChessUI') -> None:
        """
        Initialize a new animation
        
        Args:
            move: The chess move being animated
            board: Current board state
            ui: Reference to the UI for coordinate conversion
        """
        self.move = move
        self.board = board
        self.ui = ui
        self.duration = ANIMATION_DURATION
        self.start_time = time.time()
        self.progress = 0.0
        
        # Convert chess squares to pixel coordinates
        self.start_pos = self.ui.square_to_coords(move.from_square)
        self.end_pos = self.ui.square_to_coords(move.to_square)
    
    def update(self) -> float:
        """Update animation progress"""
        elapsed = time.time() - self.start_time
        self.progress = min(1.0, elapsed / self.duration)
        return self.progress
    
    def is_complete(self) -> bool:
        """Check if animation is complete"""
        return self.progress >= 1.0
    
    def get_current_pos(self) -> Tuple[int, int]:
        """Get interpolated position based on animation progress"""
        # Linear interpolation between start and end positions
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * self.progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * self.progress
        
        # Add SQUARE_SIZE/2 to center the piece on the square
        return (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)

class ChessUI:
    """handles all the ui stuff for the chess game"""
    
    def __init__(self):
        """sets up the ui components and loads assets."""
        # Initialize pygame fonts
        pygame.font.init()
        
        # Board flipping flag - determines if board should be flipped (when playing as black)
        self.board_flipped = False
        
        # Create fonts
        self.title_font = pygame.font.SysFont("Arial", 36)
        self.menu_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.huge_font = pygame.font.SysFont("Arial", 48)
        
        # Load piece images
        self.piece_images = self.load_pieces()
        
        # Load background images
        self.background_images = self.load_backgrounds()
        
        # Piece animations
        self.animations: List[Animation] = []
        
        # Create font objects
        self.large_font = pygame.font.SysFont("Arial", FONT_SIZE_LARGE)
        self.medium_font = pygame.font.SysFont("Arial", FONT_SIZE_MEDIUM)
        self.small_font = pygame.font.SysFont("Arial", FONT_SIZE_SMALL)
        self.huge_font = pygame.font.SysFont("Arial", 48)  # For checkmate/win overlays
        
        # Calculate button positions
        center_x = WINDOW_WIDTH // 2
        button_width = 200
        button_height = 50
        button_spacing = 20
        
        # Universal back button (appears in all screens)
        self.universal_back_button = Button(
            10,  # Left side of screen
            10,  # Top of screen
            80,  # Smaller width
            30,  # Smaller height
            "Back",
            font_size=16
        )
        
        # Move history navigation buttons
        nav_button_size = 40
        self.move_back_button = Button(
            WINDOW_WIDTH // 2 - nav_button_size - 10,  # Centered at the top
            10,  # Top of the screen
            nav_button_size,
            nav_button_size,
            "←",
            font_size=20
        )
        
        self.move_forward_button = Button(
            WINDOW_WIDTH // 2 + 10,  # Centered at the top
            10,  # Top of the screen
            nav_button_size,
            nav_button_size,
            "→",
            font_size=20
        )
        
        # Main menu buttons - Adjusted positions for proper centering
        self.new_game_button = Button(
            WINDOW_WIDTH // 2 - button_width // 2,
            200,
            button_width,
            button_height,
            "New Game"
        )
        
        self.settings_button = Button(
            WINDOW_WIDTH // 2 - button_width // 2,
            200 + button_height + button_spacing,
            button_width,
            button_height,
            "Settings"
        )
        
        self.quit_button = Button(
            WINDOW_WIDTH // 2 - button_width // 2,
            200 + (button_height + button_spacing) * 2,
            button_width,
            button_height,
            "Quit"
        )
        
        # Removed the Local Multiplayer button from the main menu
        
        # Difficulty adjustment buttons (moved from main menu)
        self.difficulty_up_button = Button(
            WINDOW_WIDTH // 2 + 100,
            300,  # Adjusted Y position for Player vs AI screen
            40,
            40,
            "+"
        )
        
        self.difficulty_down_button = Button(
            WINDOW_WIDTH // 2 - 140,
            300,  # Adjusted Y position for Player vs AI screen
            40,
            40,
            "-"
        )
        
        # Color selection buttons
        self.white_button = Button(
            center_x - button_width // 2,
            180,
            button_width,
            button_height,
            "Play as White"
        )
        
        self.black_button = Button(
            center_x - button_width // 2,
            180 + button_height + button_spacing,
            button_width,
            button_height,
            "Play as Black"
        )
        
        self.random_button = Button(
            center_x - button_width // 2,
            180 + (button_height + button_spacing) * 2,
            button_width,
            button_height,
            "Random Color"
        )
        
        # Hint selection buttons
        self.no_hints_button = Button(
            center_x - button_width // 2,
            180,
            button_width,
            button_height,
            "No Hints"
        )
        
        self.one_hint_button = Button(
            center_x - button_width // 2,
            180 + button_height + button_spacing,
            button_width,
            button_height,
            "1 Hint"
        )
        
        self.two_hints_button = Button(
            center_x - button_width // 2,
            180 + (button_height + button_spacing) * 2,
            button_width,
            button_height,
            "2 Hints"
        )
        
        self.three_hints_button = Button(
            center_x - button_width // 2,
            180 + (button_height + button_spacing) * 3,
            button_width,
            button_height,
            "3 Hints"
        )
        
        # In-game hint button
        self.hint_button = Button(
            BOARD_OFFSET_X + BOARD_SIZE + 20,
            400,
            120,
            40,
            "Hint",
            font_size=20
        )
        
        # Confirm button for Player vs AI screen
        self.confirm_button = Button(
            center_x - button_width // 2,
            400,
            button_width,
            button_height,
            "Confirm"
        )
        
        # Settings screen buttons
        self.theme_buttons = {}
        theme_names = ["default", "wooden", "dark", "royal", "moonlight"]
        
        for i, theme in enumerate(theme_names):
            self.theme_buttons[theme] = Button(
                center_x - button_width // 2,
                150 + (button_height + 10) * i,
                button_width,
                button_height,
                theme.capitalize()
            )
        
        self.music_toggle_button = Button(
            center_x - button_width // 2,
            150 + (button_height + 10) * len(theme_names),
            button_width,
            button_height,
            "Music: On"
        )
        
        self.back_button = Button(
            center_x - button_width // 2,
            150 + (button_height + 10) * (len(theme_names) + 2),
            button_width,
            button_height,
            "Back"
        )
        
        # Game over screen buttons
        self.menu_button = Button(
            center_x - button_width // 2,
            350,
            button_width,
            button_height,
            "Back to Menu"
        )
        
        # Settings button for in-game access
        self.in_game_settings_button = Button(
            WINDOW_WIDTH - 120,
            10,
            100,
            30,
            "Settings",
            font_size=16
        )
        
        # Last square clicked
        self.last_click = None

        self.player_vs_ai_button = Button(100, 200, 200, 50, "Player vs AI")
        self.local_multiplayer_button = Button(100, 300, 200, 50, "Local Multiplayer")

        # Message display
        self.show_message = False
        self.message_text = ""
        self.message_start_time = 0
        self.message_duration = 2.0  # Display messages for 2 seconds
    
    def load_pieces(self) -> Dict[str, pygame.Surface]:
        """Load chess piece images from assets folder"""
        pieces = {}
        try:
            # Get asset directory
            pieces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "pieces")
            
            # Direct mapping to python-chess notation
            # The image filenames are incorrect - "white_X" images are actually black pieces and vice versa
            piece_files = {
                # White pieces (uppercase in python-chess) - using the "black_" images which actually show white pieces
                'P': os.path.join(pieces_dir, "black_pawn.png"),
                'N': os.path.join(pieces_dir, "black_knight.png"),
                'B': os.path.join(pieces_dir, "black_bishop.png"),
                'R': os.path.join(pieces_dir, "black_rook.png"),
                'Q': os.path.join(pieces_dir, "black_king.png"),  # FIXED: Swapped king and queen images
                'K': os.path.join(pieces_dir, "black_queen.png"),  # FIXED: Swapped king and queen images
                
                # Black pieces (lowercase in python-chess) - using the "white_" images which actually show black pieces
                'p': os.path.join(pieces_dir, "white_pawn.png"),
                'n': os.path.join(pieces_dir, "white_knight.png"),
                'b': os.path.join(pieces_dir, "white_bishop.png"),
                'r': os.path.join(pieces_dir, "white_rook.png"),
                'q': os.path.join(pieces_dir, "white_king.png"),   # FIXED: Swapped king and queen images
                'k': os.path.join(pieces_dir, "white_queen.png")   # FIXED: Swapped king and queen images
            }
            
            # Load each piece image
            for symbol, file_path in piece_files.items():
                if os.path.exists(file_path):
                    # Load and scale image to fit square
                    img = pygame.image.load(file_path)
                    pieces[symbol] = pygame.transform.scale(
                        img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10)
                    )
                else:
                    print(f"Warning: Piece image {file_path} not found")
                    
        except Exception as e:
            print(f"Error loading piece images: {e}")
            
        return pieces
    
    def load_backgrounds(self) -> Dict[str, Optional[pygame.Surface]]:
        """Load background images"""
        backgrounds = {}
        
        for theme, path in BACKGROUND_IMAGES.items():
            try:
                # Load and scale the background to fit the window
                background = pygame.image.load(path)
                background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
                backgrounds[theme] = background
                print(f"Loaded background for theme: {theme}")
            except Exception as e:
                print(f"Error loading background image for {theme}: {e}")
                backgrounds[theme] = None
        
        return backgrounds
    
    def square_coords_to_pos(self, coords: Tuple[int, int]) -> Tuple[int, int]:
        """
        Convert square coordinates (file, rank) to screen position
        
        Args:
            coords: (file, rank) tuple where file and rank are 0-7
        
        Returns:
            (x, y) tuple of screen coordinates
        """
        file_idx, rank_idx = coords
        
        # Calculate screen position
        x = BOARD_OFFSET_X + (file_idx * SQUARE_SIZE)
        y = BOARD_OFFSET_Y + ((7 - rank_idx) * SQUARE_SIZE)  # Invert rank for drawing
        
        return (x, y)

    def square_to_coords(self, square: chess.Square) -> Tuple[int, int]:
        """
        Convert a chess square to screen coordinates
        
        Args:
            square: Chess square (0-63)
        
        Returns:
            (x, y) coordinates on screen
        """
        # Get file (column) and rank (row) from square
        file_idx = chess.square_file(square)  # 0-7 (a-h)
        rank_idx = chess.square_rank(square)  # 0-7 (1-8)
        
        # Handle board flipping when playing as black
        if self.board_flipped:
            # Flip both file and rank when board is flipped
            file_idx = 7 - file_idx
            rank_idx = 7 - rank_idx
        
        # Convert to screen coordinates
        x = BOARD_OFFSET_X + (file_idx * SQUARE_SIZE)
        y = BOARD_OFFSET_Y + ((7 - rank_idx) * SQUARE_SIZE)  # Flip rank for drawing
        
        return (x, y)

    def pos_to_square(self, pos: Tuple[int, int]) -> Optional[chess.Square]:
        """
        Convert screen position to chess square
        
        Args:
            pos: (x, y) screen coordinates
        
        Returns:
            Chess square or None if position is outside the board
        """
        # Check if position is within board boundaries
        if (pos[0] < BOARD_OFFSET_X or pos[0] >= BOARD_OFFSET_X + BOARD_SIZE or
            pos[1] < BOARD_OFFSET_Y or pos[1] >= BOARD_OFFSET_Y + BOARD_SIZE):
            return None
        
        # Convert to file and rank
        file_idx = (pos[0] - BOARD_OFFSET_X) // SQUARE_SIZE
        rank_idx = 7 - ((pos[1] - BOARD_OFFSET_Y) // SQUARE_SIZE)  # Flip rank for chess coordinates
        
        # Handle board flipping when playing as black
        if self.board_flipped:
            # Flip both file and rank when board is flipped
            file_idx = 7 - file_idx
            rank_idx = 7 - rank_idx
        
        # Create and return square
        return chess.square(file_idx, rank_idx)
    
    def draw_board(self, surface: pygame.Surface, board_state: Any, current_theme: str = "default") -> None:
        """draws the chessboard with the current theme."""
        # Import THEMES and current theme for proper square coloring
        from modules.settings import THEMES
        import os
        
        # Get current theme settings from a settings.json file if it exists
        current_theme = "default"
        if os.path.exists("settings.json"):
            try:
                import json
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    current_theme = settings.get("theme", "default")
            except:
                pass
        
        # Get theme colors
        theme_colors = THEMES.get(current_theme, THEMES["default"])
        light_square_color = theme_colors["light_square"]
        dark_square_color = theme_colors["dark_square"]
        
        # Draw board background
        board_rect = pygame.Rect(
            BOARD_OFFSET_X, BOARD_OFFSET_Y, 
            BOARD_SIZE, BOARD_SIZE
        )
        pygame.draw.rect(surface, COLOR_LIGHT_GRAY, board_rect)
        
        # Draw rank and file labels
        self.draw_board_labels(surface)
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                # Calculate square position
                square_x = BOARD_OFFSET_X + file * SQUARE_SIZE
                square_y = BOARD_OFFSET_Y + rank * SQUARE_SIZE
                square_rect = pygame.Rect(
                    square_x, square_y, 
                    SQUARE_SIZE, SQUARE_SIZE
                )
                
                # Alternate square colors
                is_light = (file + rank) % 2 != 0
                color = light_square_color if is_light else dark_square_color
                
                # Draw square
                pygame.draw.rect(surface, color, square_rect)
                
                # Get chess.Square index
                square_idx = chess.square(file, 7 - rank)  # Invert rank for chess coordinates
                
                # Draw special square highlights
                if hasattr(self, 'last_clicked_square') and square_idx == self.last_clicked_square:
                    # Draw selection highlight
                    highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    highlight.fill(COLOR_HIGHLIGHT)
                    surface.blit(highlight, square_rect)
        
        # Draw non-animated pieces
        self.draw_pieces(surface, board_state)
        
        # Draw animated pieces
        self.draw_animated_pieces(surface, board_state)
        
        # Draw board border
        pygame.draw.rect(surface, COLOR_LIGHT_GRAY, board_rect, 3)
    
    def draw_board_labels(self, surface: pygame.Surface) -> None:
        """
        Draw rank and file labels around the board
        
        Args:
            surface: Pygame surface to draw on
        """
        # Draw file labels (a-h) at the bottom
        for file in range(8):
            # Adjust the file index when board is flipped
            display_file = 7 - file if self.board_flipped else file
            label = chr(ord('a') + display_file)
            text = self.small_font.render(label, True, COLOR_TEXT)
            
            # Position below the board squares
            x = BOARD_OFFSET_X + file * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
            y_below = BOARD_OFFSET_Y + BOARD_SIZE + 10
            
            # Draw with better contrast background
            pygame.draw.rect(surface, COLOR_BACKGROUND, 
                             (x-2, y_below-2, text.get_width()+4, text.get_height()+4))
            surface.blit(text, (x, y_below))
        
        # Draw rank labels (1-8) on the left
        for rank in range(8):
            # Adjust the rank label when board is flipped
            display_rank = rank + 1 if self.board_flipped else 8 - rank
            label = str(display_rank)
            text = self.small_font.render(label, True, COLOR_TEXT)
            
            # Position to the left of the board squares
            y = BOARD_OFFSET_Y + rank * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
            x_left = BOARD_OFFSET_X - 20
            
            # Draw with better contrast background
            pygame.draw.rect(surface, COLOR_BACKGROUND, 
                             (x_left-2, y-2, text.get_width()+4, text.get_height()+4))
            surface.blit(text, (x_left, y))
    
    def draw_pieces(self, surface: pygame.Surface, board_state: Any) -> None:
        """draws the chess pieces on the board."""
        # Skip if no board state
        if not board_state or not hasattr(board_state, 'board'):
            return
        
        # Get the board representation
        board = board_state.board
        
        # Mapping from python-chess piece symbols to our notation
        piece_map = {
            'P': 'P', 'N': 'N', 'B': 'B', 'R': 'R', 'Q': 'Q', 'K': 'K',
            'p': 'p', 'n': 'n', 'b': 'b', 'r': 'r', 'q': 'q', 'k': 'k'
        }
        
        # Draw each piece
        for square in chess.SQUARES:
            # Skip if this square is being animated
            if self.is_piece_animating(square):
                continue
            
            piece = board.piece_at(square)
            if piece:
                # Get piece symbol and convert to our notation
                symbol = piece.symbol()
                
                # Direct mapping - this solves the piece color issue
                if symbol in piece_map:
                    key = piece_map[symbol]
                    
                    if key in self.piece_images:
                        # Calculate position
                        pos = self.square_to_coords(square)
                        
                        # Center the piece on the square
                        img = self.piece_images[key]
                        img_rect = img.get_rect(center=(pos[0] + SQUARE_SIZE // 2, pos[1] + SQUARE_SIZE // 2))
                        surface.blit(img, img_rect)
                    else:
                        print(f"Warning: Missing piece image for {key}")
    
    def is_piece_animating(self, square: chess.Square) -> bool:
        """Check if a piece on a square is currently being animated"""
        for anim in self.animations:
            if anim.move.from_square == square:
                return True
        return False
    
    def draw_animated_pieces(self, surface: pygame.Surface, board_state: Any) -> None:
        """Draw pieces that are being animated"""
        # Skip if no animations
        if not self.animations:
            return
        
        # Mapping from python-chess piece symbols to our notation
        piece_map = {
            'P': 'P', 'N': 'N', 'B': 'B', 'R': 'R', 'Q': 'Q', 'K': 'K',
            'p': 'p', 'n': 'n', 'b': 'b', 'r': 'r', 'q': 'q', 'k': 'k'
        }
        
        # Draw each animated piece
        for anim in self.animations:
            # Get the piece that's moving
            from_square = anim.move.from_square
            piece = anim.board.piece_at(from_square)
            
            if piece:
                # Get piece symbol and convert to our notation
                symbol = piece.symbol()
                key = piece_map.get(symbol)
                
                if key in self.piece_images:
                    # Get current position from the animation
                    x, y = anim.get_current_pos()
                    
                    # Center the piece on the current position
                    img = self.piece_images[key]
                    img_rect = img.get_rect(center=(x, y))
                    surface.blit(img, img_rect)
                else:
                    print(f"Warning: Missing animated piece image for {key}")
    
    def highlight_legal_moves(self, surface: pygame.Surface, board_state: chess.Board, selected_square: chess.Square) -> None:
        """
        Highlight legal moves for the selected piece
        
        Args:
            surface: Pygame surface to draw on
            board_state: Current chess board state
            selected_square: Square that is currently selected
        """
        legal_moves = []
        
        # Get all legal moves for the piece on the selected square
        for move in board_state.legal_moves:
            if move.from_square == selected_square:
                legal_moves.append(move.to_square)
        
        # Draw highlight for each legal move
        for square in legal_moves:
            # Get screen coordinates for this square
            x, y = self.square_to_coords(square)
            
            # Calculate the center of the square
            center_x = x + SQUARE_SIZE // 2
            center_y = y + SQUARE_SIZE // 2
            
            # Draw a circle in the center of the square
            circle_radius = SQUARE_SIZE // 4
            pygame.draw.circle(surface, COLOR_MOVE_INDICATOR, (center_x, center_y), circle_radius)
            
            # Draw a border around the circle for better visibility
            pygame.draw.circle(surface, (50, 50, 0), (center_x, center_y), circle_radius, 2)
    
    def draw_highlights(self, surface: pygame.Surface, 
                        selected_square: Optional[chess.Square], 
                        highlighted_squares: List[chess.Square],
                        hint_move: Optional[chess.Move] = None) -> None:
        """draws highlights for selected squares, legal moves, and hints."""
        # Draw selected square highlight
        if selected_square is not None:
            x, y = self.square_to_coords(selected_square)
            selected_rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
            
            # Create semi-transparent highlight
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(COLOR_SELECTED)
            surface.blit(highlight, selected_rect)
        
        # Draw legal move indicators (circles)
        for square in highlighted_squares:
            if square == selected_square:
                continue  # Skip selected square
            
            # Get coordinates
            x, y = self.square_to_coords(square)
            
            # Determine if this is a hint move square
            is_hint = hint_move and (square == hint_move.from_square or square == hint_move.to_square)
            
            # Draw centered circle for legal move
            circle_color = (255, 255, 0) if not is_hint else (0, 200, 0)  # Yellow for normal, green for hint
            circle_center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
            circle_radius = SQUARE_SIZE // 4
            
            # Draw circle with border for better visibility
            pygame.draw.circle(surface, (0, 0, 0), circle_center, circle_radius + 2)  # Black border
            pygame.draw.circle(surface, circle_color, circle_center, circle_radius)    # Yellow/green fill
    
    def animate_move(self, move: chess.Move, board: chess.Board) -> None:
        """starts an animation for a piece move."""
        self.animations.append(Animation(move, board, self))
    
    def update_animations(self) -> bool:
        """updates ongoing animations and removes completed ones."""
        # Update progress for all animations
        for anim in self.animations:
            anim.update()
        
        # Remove completed animations
        self.animations = [anim for anim in self.animations if not anim.is_complete()]
        
        # Return whether there are still animations in progress
        return len(self.animations) > 0
    
    def draw_menu(self, surface: pygame.Surface, difficulty: int, ai_rating: int, current_theme: str = "default") -> None:
        """Draws the main menu interface."""
        # Draw background based on current theme
        self.draw_theme_background(surface, current_theme)
        
        # Draw title
        title = self.large_font.render("Chess AI", True, COLOR_TEXT)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self.new_game_button.update(mouse_pos)
        self.new_game_button.draw(surface)
        self.settings_button.update(mouse_pos)
        self.settings_button.draw(surface)
        self.quit_button.update(mouse_pos)
        self.quit_button.draw(surface)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
    
    def draw_game(self, surface: pygame.Surface, board_state: Any, 
                  selected_square: Optional[chess.Square], 
                  highlighted_squares: List[chess.Square],
                  human_turn: bool, ai_thinking: bool, thinking_time: float,
                  current_theme: str = "default", hints_remaining: int = 0,
                  hint_move: Optional[chess.Move] = None, viewing_history: bool = False) -> None:
        """
        Draw the complete game interface
        
        Args:
            surface: Pygame surface to draw on
            board_state: GameBoard object containing the chess state
            selected_square: Currently selected square
            highlighted_squares: Legal move squares to highlight
            human_turn: True if it's the human player's turn
            ai_thinking: True if AI is calculating
            thinking_time: Time AI has been thinking
            current_theme: Current theme name
            hints_remaining: Number of hints remaining
            hint_move: Current hint move to highlight
            viewing_history: Whether viewing move history
        """
        # Draw theme background
        self.draw_theme_background(surface, current_theme)
        
        # Draw the chess board and pieces
        self.draw_board(surface, board_state, current_theme=current_theme)
        
        # Draw highlighted squares for selection
        self.draw_highlights(
            surface, 
            selected_square, 
            highlighted_squares,
            hint_move
        )
        
        # Draw animated pieces on top
        self.draw_animated_pieces(surface, board_state)
        
        # Draw game info
        turn_text = "Your Turn" if human_turn else "AI Thinking..."
        turn_surface = self.medium_font.render(turn_text, True, COLOR_TEXT)
        
        # Add a background behind the text for better visibility
        text_bg = pygame.Rect(
            BOARD_OFFSET_X + BOARD_SIZE + 20, 
            BOARD_OFFSET_Y,
            turn_surface.get_width() + 10,
            turn_surface.get_height() + 5
        )
        pygame.draw.rect(surface, COLOR_BUTTON, text_bg)
        pygame.draw.rect(surface, (50, 50, 50), text_bg, 1)
        surface.blit(turn_surface, (BOARD_OFFSET_X + BOARD_SIZE + 25, BOARD_OFFSET_Y + 2))
        
        # Draw captured pieces
        self.draw_captured_pieces(surface, board_state)
        
        # Draw AI info if AI is thinking
        if ai_thinking:
            self.draw_thinking_indicator(surface, thinking_time)
        
        # Draw settings button in-game
        mouse_pos = pygame.mouse.get_pos()
        self.in_game_settings_button.update(mouse_pos)
        self.in_game_settings_button.draw(surface)
        
        # Draw hint button and count if hints are available
        if hints_remaining > 0:
            # Update hint button label to show remaining count
            self.hint_button.update_text(f"Hint ({hints_remaining})")
            self.hint_button.update(mouse_pos)
            self.hint_button.draw(surface)
        
        # Draw move history and navigation buttons - only for Player vs AI mode
        # Draw move history
        self.draw_move_history(surface, board_state)
        
        # Draw move history navigation buttons
        self.move_back_button.update(mouse_pos)
        self.move_back_button.draw(surface)
        
        self.move_forward_button.update(mouse_pos)
        self.move_forward_button.draw(surface)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
        
        # Draw viewing history message if in history mode
        if viewing_history:
            history_msg = self.medium_font.render("Viewing History", True, (220, 150, 50))
            msg_rect = history_msg.get_rect(center=(self.move_back_button.rect.left - 95, self.move_back_button.rect.centery))
            pygame.draw.rect(surface, (40, 40, 40), 
                             (msg_rect.left - 10, msg_rect.top - 5, 
                              msg_rect.width + 20, msg_rect.height + 10))
            surface.blit(history_msg, msg_rect)
    
    def draw_settings(self, surface: pygame.Surface, settings_manager, return_to_game: bool = False) -> None:
        """draws the settings screen."""
        # Draw background based on current theme
        current_theme = settings_manager.get_theme()
        self.draw_theme_background(surface, current_theme)
        
        # Draw title with background
        title = self.large_font.render("Settings", True, COLOR_TEXT)
        title_width = title.get_width() + 20
        title_height = title.get_height() + 10
        title_x = WINDOW_WIDTH // 2 - title_width // 2
        title_y = 50
        
        pygame.draw.rect(surface, COLOR_BUTTON, 
                        (title_x, title_y, title_width, title_height))
        pygame.draw.rect(surface, (50, 50, 50), 
                        (title_x, title_y, title_width, title_height), 1)
        
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, title_y + 5))
        
        # Get mouse position for button updates
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw theme label with background
        theme_title = self.medium_font.render("Board Themes:", True, COLOR_TEXT)
        theme_title_width = theme_title.get_width() + 20
        theme_title_height = theme_title.get_height() + 6
        theme_title_x = WINDOW_WIDTH // 2 - theme_title_width // 2
        theme_title_y = 100
        
        pygame.draw.rect(surface, COLOR_BUTTON, 
                        (theme_title_x, theme_title_y, theme_title_width, theme_title_height))
        pygame.draw.rect(surface, (50, 50, 50), 
                        (theme_title_x, theme_title_y, theme_title_width, theme_title_height), 1)
        
        surface.blit(theme_title, (WINDOW_WIDTH // 2 - theme_title.get_width() // 2, theme_title_y + 3))
        
        # Import THEMES here to avoid circular imports
        from modules.settings import THEMES
        
        # Draw theme buttons with adequate spacing
        button_y_start = 140
        button_spacing = 10
        current_theme = settings_manager.get_theme()
        
        # Adjust button positions
        for i, (theme_name, button) in enumerate(self.theme_buttons.items()):
            # Update button position to ensure proper spacing
            button.rect.y = button_y_start + i * (button.rect.height + button_spacing)
            
            # Highlight the current theme
            if theme_name == current_theme:
                button.color = (100, 120, 160)
            else:
                button.color = COLOR_BUTTON
                
            button.update(mouse_pos)
            button.draw(surface)
            
            # Add a small preview of the theme next to the button
            theme_colors = THEMES[theme_name]
            preview_size = 20
            preview_x = button.rect.right + 20
            preview_y = button.rect.centery - preview_size
            
            # Draw mini-board preview (2x2 squares)
            for i in range(2):
                for j in range(2):
                    is_light = (i + j) % 2 != 0
                    color = theme_colors["light_square"] if is_light else theme_colors["dark_square"]
                    pygame.draw.rect(surface, color, 
                                    (preview_x + i * preview_size, 
                                     preview_y + j * preview_size, 
                                     preview_size, preview_size))
        
        # Calculate music button position
        last_theme_button = list(self.theme_buttons.values())[-1]
        music_button_y = last_theme_button.rect.bottom + 20
        
        # Update music toggle button position
        self.music_toggle_button.rect.y = music_button_y
        
        # Draw music toggle button
        music_state = "On" if settings_manager.is_music_enabled() else "Off"
        self.music_toggle_button.update_text(f"Music: {music_state}")
        self.music_toggle_button.update(mouse_pos)
        self.music_toggle_button.draw(surface)
        
        # Create volume slider if it doesn't exist
        if not hasattr(self, 'volume_slider'):
            slider_width = 150
            slider_height = 15
            slider_x = WINDOW_WIDTH // 2 - slider_width // 2
            slider_y = music_button_y + 50
            self.volume_slider = VolumeSlider(slider_x, slider_y, slider_width, slider_height)
        
        # Only show volume slider if music is enabled
        if settings_manager.is_music_enabled():
            # Draw volume label
            volume_label = self.small_font.render("Volume", True, COLOR_TEXT)
            surface.blit(volume_label, (self.volume_slider.rect.centerx - volume_label.get_width() // 2, 
                                      self.volume_slider.rect.top - 25))
            
            # Draw volume slider
            self.volume_slider.draw(surface)
            
            # Draw volume percentage
            volume_text = self.small_font.render(f"{int(self.volume_slider.value * 100)}%", True, COLOR_TEXT)
            surface.blit(volume_text, (self.volume_slider.rect.centerx - volume_text.get_width() // 2, 
                                      self.volume_slider.rect.bottom + 10))
        
        # Update back button position - ensure it's always visible
        self.back_button.rect.y = music_button_y + (120 if settings_manager.is_music_enabled() else 70)
        
        # Update back button text based on where we should return to
        back_text = "Back to Game" if return_to_game else "Back to Menu"
        self.back_button.update_text(back_text)
        self.back_button.update(mouse_pos)
        self.back_button.draw(surface)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
    
    def draw_player_vs_ai_screen(self, surface: pygame.Surface, difficulty: int, ai_rating: int, selected_color: chess.Color = None) -> None:
        """Draw the Player vs AI game mode selection screen with integrated color selection."""
        # Draw background
        self.draw_theme_background(surface, "default")
        
        # Draw title
        title = self.large_font.render("Player vs AI", True, COLOR_TEXT)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))
        
        # Center position for all elements
        center_x = WINDOW_WIDTH // 2
        
        # Draw AI rating with background for better visibility
        ai_label = self.medium_font.render(f"AI Rating: {ai_rating}", True, COLOR_TEXT)
        rating_width = ai_label.get_width() + 40  # Make it wider to avoid overlap with buttons
        rating_height = ai_label.get_height() + 10
        rating_x = center_x - rating_width // 2
        rating_y = 180  # Moved up to make room for color selection

        # Draw rating background
        pygame.draw.rect(surface, COLOR_BUTTON, 
                        (rating_x, rating_y, rating_width, rating_height))
        pygame.draw.rect(surface, (50, 50, 50), 
                        (rating_x, rating_y, rating_width, rating_height), 1)
        surface.blit(ai_label, (center_x - ai_label.get_width() // 2, 
                              rating_y + 5))
        
        # Position and draw difficulty adjustment buttons
        button_spacing = 20  # Space between rating box and buttons
        self.difficulty_down_button.rect.x = rating_x - self.difficulty_down_button.rect.width - button_spacing
        self.difficulty_down_button.rect.centery = rating_y + rating_height // 2
        
        self.difficulty_up_button.rect.x = rating_x + rating_width + button_spacing
        self.difficulty_up_button.rect.centery = rating_y + rating_height // 2
        
        mouse_pos = pygame.mouse.get_pos()
        self.difficulty_up_button.update(mouse_pos)
        self.difficulty_down_button.update(mouse_pos)
        self.difficulty_up_button.draw(surface)
        self.difficulty_down_button.draw(surface)
        
        # Draw color selection section
        color_section_y = 250
        color_label = self.medium_font.render("Select a Color:", True, COLOR_TEXT)
        surface.blit(color_label, (center_x - color_label.get_width() // 2, color_section_y))
        
        # Position color selection buttons
        button_width = 120
        button_height = 40
        button_spacing = 20
        total_width = (button_width * 3) + (button_spacing * 2)
        start_x = center_x - total_width // 2
        
        # Define button positions
        self.white_button.rect = pygame.Rect(start_x, color_section_y + 40, button_width, button_height)
        self.black_button.rect = pygame.Rect(start_x + button_width + button_spacing, color_section_y + 40, button_width, button_height)
        self.random_button.rect = pygame.Rect(start_x + (button_width + button_spacing) * 2, color_section_y + 40, button_width, button_height)

        # Update button states
        mouse_pos = pygame.mouse.get_pos()
        self.white_button.update(mouse_pos)
        self.black_button.update(mouse_pos)
        self.random_button.update(mouse_pos)

        # Draw buttons with special visuals for the selected one
        if selected_color == chess.WHITE:
            pygame.draw.rect(surface, (255, 255, 255), self.white_button.rect)  # White
        else:
            self.white_button.draw(surface)

        if selected_color == chess.BLACK:
            pygame.draw.rect(surface, (0, 0, 0), self.black_button.rect)  # Black
        else:
            self.black_button.draw(surface)

        if selected_color == -1:  # Random
            # Draw a half-white, half-black box
            pygame.draw.rect(surface, (255, 255, 255), self.random_button.rect)  # White half
            pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(
                self.random_button.rect.x + self.random_button.rect.width // 2,
                self.random_button.rect.y,
                self.random_button.rect.width // 2,
                self.random_button.rect.height
            ))  # Black half
        else:
            self.random_button.draw(surface)

        # Draw confirm button
        button_width = 200
        button_height = 40
        self.confirm_button.rect = pygame.Rect(
            WINDOW_WIDTH // 2 - button_width // 2,
            color_section_y + 100,
            button_width,
            button_height
        )
        self.confirm_button.update(mouse_pos)
        self.confirm_button.draw(surface)

        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
        
        # Display error message if needed
        if self.show_message and time.time() - self.message_start_time < self.message_duration:
            message_font = self.medium_font
            message_surface = message_font.render(self.message_text, True, (255, 50, 50))  # Red text for error
            
            # Create a background for the message
            msg_padding = 10
            msg_bg_rect = pygame.Rect(
                center_x - message_surface.get_width() // 2 - msg_padding,
                color_section_y + 150,
                message_surface.get_width() + msg_padding * 2,
                message_surface.get_height() + msg_padding * 2
            )
            
            # Draw semi-transparent background
            s = pygame.Surface((msg_bg_rect.width, msg_bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))  # Black with alpha
            surface.blit(s, (msg_bg_rect.x, msg_bg_rect.y))
            
            # Draw message
            surface.blit(message_surface, (center_x - message_surface.get_width() // 2, color_section_y + 150 + msg_padding))
    
    def draw_captured_pieces(self, surface: pygame.Surface, board_state: Any) -> None:
        """Draw captured pieces on the side of the board"""
        # Check if board_state is a dictionary or a GameBoard object
        if isinstance(board_state, dict):
            # If it's a dictionary, use it directly
            white_captures = board_state.get('white', [])
            black_captures = board_state.get('black', [])
        else:
            # If it's a GameBoard object, call its method
            captures = board_state.get_all_captured_pieces()
            white_captures = captures['white']
            black_captures = captures['black']
        
        # Clear background for captured pieces area
        captured_area_rect = pygame.Rect(
            BOARD_OFFSET_X + BOARD_SIZE + 10, 
            BOARD_OFFSET_Y,
            200, 
            BOARD_SIZE
        )
        pygame.draw.rect(surface, COLOR_BACKGROUND, captured_area_rect)
        
        # Draw sections for captured pieces
        x_pos = BOARD_OFFSET_X + BOARD_SIZE + 20
        
        # Draw header for pieces captured by player
        y_pos = BOARD_OFFSET_Y + 10
        player_captures_label = self.small_font.render("Captured by You:", True, COLOR_TEXT)
        surface.blit(player_captures_label, (x_pos, y_pos))
        
        # Draw white's captures (black pieces)
        y_pos += 30
        for i, piece in enumerate(black_captures):
            # Make sure we're only showing black pieces here (pieces captured by white player)
            if piece.color == chess.BLACK:
                piece_key = 'p' if piece.symbol().lower() == 'p' else piece.symbol().lower()
                if piece_key in self.piece_images:
                    # Scale down for captured piece display
                    small_piece = pygame.transform.scale(
                        self.piece_images[piece_key], 
                        (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
                    )
                    surface.blit(small_piece, (x_pos + (i % 4) * (SQUARE_SIZE // 2), y_pos + (i // 4) * (SQUARE_SIZE // 2)))
        
        # Draw header for pieces captured by AI
        y_pos = BOARD_OFFSET_Y + BOARD_SIZE // 2
        ai_captures_label = self.small_font.render("Captured by AI:", True, COLOR_TEXT)
        surface.blit(ai_captures_label, (x_pos, y_pos))
        
        # Draw black's captures (white pieces)
        y_pos += 30
        for i, piece in enumerate(white_captures):
            # Make sure we're only showing white pieces here (pieces captured by black player)
            if piece.color == chess.WHITE:
                piece_key = 'P' if piece.symbol().upper() == 'P' else piece.symbol().upper()
                if piece_key in self.piece_images:
                    # Scale down for captured piece display
                    small_piece = pygame.transform.scale(
                        self.piece_images[piece_key], 
                        (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
                    )
                    surface.blit(small_piece, (x_pos + (i % 4) * (SQUARE_SIZE // 2), y_pos + (i // 4) * (SQUARE_SIZE // 2)))
    
    def draw_move_history(self, surface: pygame.Surface, board_state: Any) -> None:
        """Draw the move history sidebar"""
        # Calculate position for move history
        history_x = 20
        history_y = 60
        history_width = BOARD_OFFSET_X - 40
        
        # Draw background
        history_rect = pygame.Rect(history_x, history_y, history_width, BOARD_SIZE)
        pygame.draw.rect(surface, COLOR_LIGHT_GRAY, history_rect, border_radius=5)
        
        # Draw title
        history_title = self.small_font.render("Move History", True, COLOR_TEXT)
        surface.blit(history_title, (history_x + 10, history_y + 10))
        
        # Draw moves
        move_y = history_y + 40
        max_displayed = 15  # Maximum number of moves to display
        
        # Calculate which moves to display based on the total
        move_history = board_state.move_history
        start_idx = max(0, len(move_history) - max_displayed)
        
        for i, move in enumerate(move_history[start_idx:]):
            move_idx = start_idx + i
            move_num = move_idx // 2 + 1
            is_white = move_idx % 2 == 0
            
            # Format the move number and move
            prefix = f"{move_num}." if is_white else "   "
            move_text = prefix + move.uci()
            
            # Render the move text
            text = self.small_font.render(move_text, True, COLOR_TEXT)
            text_y = move_y + i * 20
            
            # Only draw if it fits in the history box
            if text_y < history_y + history_rect.height - 20:
                surface.blit(text, (history_x + 10, text_y))
    
    def draw_game_info(self, surface: pygame.Surface, board_state: Any, 
                       human_turn: bool, ai_level: int, 
                       selected_square: Optional[chess.Square], 
                       highlighted_squares: List[chess.Square]) -> None:
        """Draw game status and highlighted squares"""
        # Draw move highlights
        self.draw_highlights(surface, selected_square, highlighted_squares)
        
        # Draw turn indicator
        turn_text = "Your Turn" if human_turn else "AI Thinking..."
        turn_surface = self.medium_font.render(turn_text, True, COLOR_TEXT)
        surface.blit(turn_surface, (WINDOW_WIDTH - 150, 20))
        
        # Draw game state
        state = board_state.get_game_state()
        if state != "playing":
            state_color = (255, 0, 0) if state == "check" else COLOR_TEXT
            state_surface = self.medium_font.render(state.capitalize(), True, state_color)
            surface.blit(state_surface, (WINDOW_WIDTH - 150, 50))
        
        # Draw captured pieces
        self.draw_captured_pieces(surface, board_state)
        
        # Draw move history
        self.draw_move_history(surface, board_state)
        
        # Draw AI level
        ai_text = f"AI Level: {ai_level}"
        ai_surface = self.small_font.render(ai_text, True, COLOR_TEXT)
        surface.blit(ai_surface, (20, 20))
    
    def draw_game_result(self, surface: pygame.Surface, result_message: str, ai_rating: Optional[int] = None) -> None:
        """draws the game result screen."""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with alpha
        surface.blit(overlay, (0, 0))
        
        # Draw result message
        result_surface = self.large_font.render(result_message, True, (255, 255, 255))
        surface.blit(result_surface, 
                    (WINDOW_WIDTH // 2 - result_surface.get_width() // 2, 
                     WINDOW_HEIGHT // 2 - 100))
        
        # Draw updated AI rating only for AI games (not for local multiplayer)
        if ai_rating is not None:
            ai_surface = self.medium_font.render(
                f"AI Rating: {ai_rating}", 
                True, (255, 255, 255)
            )
            surface.blit(ai_surface, 
                        (WINDOW_WIDTH // 2 - ai_surface.get_width() // 2, 
                         WINDOW_HEIGHT // 2))
        
        # Draw menu button
        mouse_pos = pygame.mouse.get_pos()
        self.menu_button.update(mouse_pos)
        self.menu_button.draw(surface)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
    
    def draw_thinking_indicator(self, surface: pygame.Surface, thinking_time: float) -> None:
        """Draw an animated 'thinking' indicator while AI is calculating"""
        # Draw text and animated dots
        dots = "." * (int(thinking_time * 2) % 4)
        thinking_text = f"AI thinking{dots}"
        
        thinking_surface = self.medium_font.render(thinking_text, True, (220, 220, 0))
        surface.blit(thinking_surface, (WINDOW_WIDTH - 180, WINDOW_HEIGHT - 50))
        
        # Draw time elapsed
        time_text = f"Time: {thinking_time:.1f}s"
        time_surface = self.small_font.render(time_text, True, COLOR_TEXT)
        surface.blit(time_surface, (WINDOW_WIDTH - 180, WINDOW_HEIGHT - 25))
    
    def draw_theme_background(self, surface: pygame.Surface, theme: str) -> None:
        """
        Draw the appropriate background for the current theme
        
        Args:
            surface: Pygame surface to draw on
            theme: Current theme name
        """
        # Fill with default background color first
        surface.fill(COLOR_BACKGROUND)
        
        # If the theme has a background image, draw it
        if theme in self.background_images and self.background_images[theme] is not None:
            surface.blit(self.background_images[theme], (0, 0))
    
    def draw_color_selection(self, surface: pygame.Surface) -> None:
        """Draw the color selection screen"""
        # Draw title
        title = self.large_font.render("Choose Your Color", True, COLOR_TEXT)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))
        
        # Draw description
        description = self.medium_font.render("Select the color you want to play as", True, COLOR_TEXT)
        surface.blit(description, (WINDOW_WIDTH // 2 - description.get_width() // 2, 130))
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self.white_button.update(mouse_pos)
        self.white_button.draw(surface)
        self.black_button.update(mouse_pos)
        self.black_button.draw(surface)
        self.random_button.update(mouse_pos)
        self.random_button.draw(surface)
        
        # Draw piece icons next to buttons
        # White pieces
        white_king = self.piece_images.get('K', None)
        if white_king:
            scaled_white = pygame.transform.scale(white_king, (40, 40))
            surface.blit(scaled_white, (self.white_button.rect.right + 20, self.white_button.rect.centery - 20))
        
        # Black pieces
        black_king = self.piece_images.get('k', None)
        if black_king:
            scaled_black = pygame.transform.scale(black_king, (40, 40))
            surface.blit(scaled_black, (self.black_button.rect.right + 20, self.black_button.rect.centery - 20))
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
    
    def draw_hint_selection(self, surface: pygame.Surface) -> None:
        """Draw the hint selection screen"""
        # Draw title
        title = self.large_font.render("Choose Hint Count", True, COLOR_TEXT)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))
        
        # Draw description
        description = self.medium_font.render("How many hints do you want?", True, COLOR_TEXT)
        surface.blit(description, (WINDOW_WIDTH // 2 - description.get_width() // 2, 130))
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self.no_hints_button.update(mouse_pos)
        self.no_hints_button.draw(surface)
        self.one_hint_button.update(mouse_pos)
        self.one_hint_button.draw(surface)
        self.two_hints_button.update(mouse_pos)
        self.two_hints_button.draw(surface)
        self.three_hints_button.update(mouse_pos)
        self.three_hints_button.draw(surface)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
    
    def draw_checkmate_overlay(self, surface: pygame.Surface) -> None:
        """Draw a CHECKMATE overlay on the game screen"""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        surface.blit(overlay, (0, 0))
        
        # Space out the letters for more visual impact
        spaced_text = "C    H    E    C    K    M    A    T    E"
        
        # Draw CHECKMATE text with larger font for better visibility
        bigger_font = pygame.font.SysFont("Arial", 60)  # Increased from 48
        text = bigger_font.render(spaced_text, True, (255, 50, 50))
        text_width = text.get_width()
        text_x = WINDOW_WIDTH // 2 - text_width // 2
        text_y = WINDOW_HEIGHT // 2 - 50
        
        # Add glow effect
        for offset in range(3, 0, -1):
            glow_text = bigger_font.render(spaced_text, True, (200, 50, 50, 128))
            surface.blit(glow_text, (text_x - offset, text_y - offset))
            surface.blit(glow_text, (text_x + offset, text_y - offset))
            surface.blit(glow_text, (text_x - offset, text_y + offset))
            surface.blit(glow_text, (text_x + offset, text_y + offset))
        
        # Draw main text
        surface.blit(text, (text_x, text_y))

    def draw_result_overlay(self, surface: pygame.Surface, is_winner: bool) -> None:
        """Draw a WIN/LOSE overlay on the game screen"""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # Semi-transparent black
        surface.blit(overlay, (0, 0))
        
        # Space out the letters for more visual impact
        win_text = "Y O U   W I N !"
        lose_text = "Y O U   L O S E !"
        
        # Draw result text based on outcome
        text_content = win_text if is_winner else lose_text
        text_color = (50, 255, 50) if is_winner else (255, 50, 50)  # Green for win, red for lose
        
        # Use larger font for better visibility
        bigger_font = pygame.font.SysFont("Arial", 60)  # Increased from 48
        text = bigger_font.render(text_content, True, text_color)
        text_width = text.get_width()
        text_x = WINDOW_WIDTH // 2 - text_width // 2
        text_y = WINDOW_HEIGHT // 2 - 50
        
        # Add glow effect
        glow_color = (50, 200, 50, 128) if is_winner else (200, 50, 50, 128)
        for offset in range(3, 0, -1):
            glow_text = bigger_font.render(text_content, True, glow_color)
            surface.blit(glow_text, (text_x - offset, text_y - offset))
            surface.blit(glow_text, (text_x + offset, text_y - offset))
            surface.blit(glow_text, (text_x - offset, text_y + offset))
            surface.blit(glow_text, (text_x + offset, text_y + offset))
        
        # Draw main text
        surface.blit(text, (text_x, text_y))
    
    def set_board_orientation(self, player_color: chess.Color) -> None:
        """
        Set the board orientation based on player color
        
        Args:
            player_color: chess.WHITE or chess.BLACK
        """
        # Flip the board when playing as black so player's pieces are at the bottom
        self.board_flipped = (player_color == chess.BLACK)

    def draw_text(self, surface: pygame.Surface, text: str, position: Tuple[int, int], font=None, color=None) -> None:
        """
        Draw text on the surface at the specified position
        
        Args:
            surface: Surface to draw on
            text: Text to draw
            position: (x, y) position to draw at
            font: Font to use (defaults to medium_font)
            color: Color to use (defaults to COLOR_TEXT)
        """
        font = font or self.medium_font
        color = color or COLOR_TEXT
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, position)

    def draw_time_constraint_selection(self, surface: pygame.Surface) -> None:
        """Draw the time constraint selection screen for local multiplayer."""
        # Draw background
        self.draw_theme_background(surface, "default")
        
        # Draw title
        title = self.large_font.render("Select Time Constraint", True, COLOR_TEXT)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 60))
        
        # Load icons
        icons = {}
        icon_paths = {
            "bullet": os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "time_limit", "bullet_chess.png"),
            "blitz": os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "time_limit", "blitz_chess.png"),
            "rapid": os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "time_limit", "rapid_chess.png"),
            "no_time": os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "time_limit", "no_time_constraint.png")
        }
        
        for key, path in icon_paths.items():
            if os.path.exists(path):
                icons[key] = pygame.image.load(path)
                icons[key] = pygame.transform.scale(icons[key], (40, 40))
            else:
                print(f"Warning: Icon {path} not found")
        
        # Calculate positions
        center_x = WINDOW_WIDTH // 2
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = 120
        
        # Create buttons if they don't exist
        if not hasattr(self, 'bullet_button'):
            self.bullet_button = Button(
                center_x - button_width // 2,
                start_y,
                button_width,
                button_height,
                "Bullet Chess - 1 min"
            )
        
        if not hasattr(self, 'blitz_3_button'):
            self.blitz_3_button = Button(
                center_x - button_width // 2,
                start_y + button_height + button_spacing,
                button_width,
                button_height,
                "Blitz Chess - 3 min"
            )
            
        if not hasattr(self, 'blitz_5_button'):
            self.blitz_5_button = Button(
                center_x - button_width // 2,
                start_y + (button_height + button_spacing) * 2,
                button_width,
                button_height,
                "Blitz Chess - 5 min"
            )
            
        if not hasattr(self, 'rapid_button'):
            self.rapid_button = Button(
                center_x - button_width // 2,
                start_y + (button_height + button_spacing) * 3,
                button_width,
                button_height,
                "Rapid Chess - 10 min"
            )
            
        if not hasattr(self, 'no_time_button'):
            self.no_time_button = Button(
                center_x - button_width // 2,
                start_y + (button_height + button_spacing) * 4,
                button_width,
                button_height,
                "No Time Constraint"
            )
        
        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        
        self.bullet_button.update(mouse_pos)
        self.bullet_button.draw(surface)
        
        self.blitz_3_button.update(mouse_pos)
        self.blitz_3_button.draw(surface)
        
        self.blitz_5_button.update(mouse_pos)
        self.blitz_5_button.draw(surface)
        
        self.rapid_button.update(mouse_pos)
        self.rapid_button.draw(surface)
        
        self.no_time_button.update(mouse_pos)
        self.no_time_button.draw(surface)
        
        # Draw icons next to buttons if loaded
        if "bullet" in icons:
            surface.blit(icons["bullet"], (self.bullet_button.rect.x - 50, self.bullet_button.rect.centery - 20))
        
        if "blitz" in icons:
            surface.blit(icons["blitz"], (self.blitz_3_button.rect.x - 50, self.blitz_3_button.rect.centery - 20))
            surface.blit(icons["blitz"], (self.blitz_5_button.rect.x - 50, self.blitz_5_button.rect.centery - 20))
        
        if "rapid" in icons:
            surface.blit(icons["rapid"], (self.rapid_button.rect.x - 50, self.rapid_button.rect.centery - 20))
        
        if "no_time" in icons:
            surface.blit(icons["no_time"], (self.no_time_button.rect.x - 50, self.no_time_button.rect.centery - 20))

        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)

    def draw_local_multiplayer_game(self, surface: pygame.Surface, board_state: Any, 
                               selected_square: Optional[chess.Square], 
                               highlighted_squares: List[chess.Square],
                               current_player: chess.Color,
                               white_time: int, black_time: int,
                               current_theme: str = "default") -> None:
        """Draw the local multiplayer game interface with chess clocks"""
        # Draw the board and pieces
        self.draw_board(surface, board_state, current_theme)
        self.draw_board_labels(surface)
        
        # Draw highlights
        self.draw_highlights(surface, selected_square, highlighted_squares)
        
        # Draw captured pieces with proper labels for local multiplayer
        self.draw_local_multiplayer_captured_pieces(surface, board_state, current_player)
        
        # Only draw clocks if we're not in unlimited time mode (white_time and black_time will be -1)
        if white_time >= 0 and black_time >= 0:
            # Draw player clocks
            white_mins, white_secs = divmod(white_time, 60)
            black_mins, black_secs = divmod(black_time, 60)
            
            # Format time strings without "White:" and "Black:" prefixes
            white_time_str = f"{white_mins:02d}:{white_secs:02d}"
            black_time_str = f"{black_mins:02d}:{black_secs:02d}"
            
            # Determine colors based on current player
            white_color = (50, 200, 50) if current_player == chess.WHITE else COLOR_TEXT
            black_color = (50, 200, 50) if current_player == chess.BLACK else COLOR_TEXT
            
            # Create bold font for time display
            bold_font = pygame.font.SysFont("Arial", FONT_SIZE_MEDIUM, bold=True)
            
            # Draw time indicators with bold font
            white_time_surface = bold_font.render(white_time_str, True, white_color)
            black_time_surface = bold_font.render(black_time_str, True, black_color)
            
            # Position time indicators on the right side of the board
            # White at bottom, Black at top
            right_margin = WINDOW_WIDTH - 100
            surface.blit(white_time_surface, (right_margin, WINDOW_HEIGHT - 100))
            surface.blit(black_time_surface, (right_margin, 100))
        
        # Draw current player indicator
        turn_text = "White's Turn" if current_player == chess.WHITE else "Black's Turn"
        turn_surface = self.medium_font.render(turn_text, True, COLOR_TEXT)
        surface.blit(turn_surface, (BOARD_OFFSET_X + BOARD_SIZE + 20, 50))
        
        # Draw in-game settings button
        mouse_pos = pygame.mouse.get_pos()
        self.in_game_settings_button.update(mouse_pos)
        self.in_game_settings_button.draw(surface)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(surface)
        
    def draw_local_multiplayer_captured_pieces(self, surface: pygame.Surface, board_state: Any, player_color: chess.Color) -> None:
        """Draw captured pieces with proper labels for local multiplayer mode"""
        # Get captured pieces
        white_captured = board_state.get_captured_pieces(chess.WHITE)
        black_captured = board_state.get_captured_pieces(chess.BLACK)
        
        # Draw labels for captured pieces
        white_label = self.small_font.render("Captured by White", True, COLOR_TEXT)
        black_label = self.small_font.render("Captured by Black", True, COLOR_TEXT)
        
        # Position for captured pieces display
        white_label_pos = (BOARD_OFFSET_X + BOARD_SIZE + 20, 200)
        black_label_pos = (BOARD_OFFSET_X + BOARD_SIZE + 20, 300)
        
        # Draw the labels
        surface.blit(white_label, white_label_pos)
        surface.blit(black_label, black_label_pos)
        
        # Draw the captured pieces
        piece_size = 30
        spacing = 5
        
        # Helper function to get piece symbol
        def get_piece_symbol(piece):
            # Convert piece to symbol (e.g., white pawn -> 'P', black knight -> 'n')
            symbols = {
                chess.PAWN: 'P', 
                chess.KNIGHT: 'N', 
                chess.BISHOP: 'B',
                chess.ROOK: 'R', 
                chess.QUEEN: 'Q', 
                chess.KING: 'K'
            }
            symbol = symbols.get(piece.piece_type, '')
            # Make lowercase for black pieces
            if piece.color == chess.BLACK:
                symbol = symbol.lower()
            return symbol
        
        # Draw white's captured pieces
        for i, piece in enumerate(white_captured):
            col = i % 8
            row = i // 8
            x = white_label_pos[0] + col * (piece_size + spacing)
            y = white_label_pos[1] + 20 + row * (piece_size + spacing)
            
            # Get the piece image
            try:
                symbol = get_piece_symbol(piece)
                if symbol in self.piece_images:
                    piece_img = self.piece_images[symbol]
                    piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                    surface.blit(piece_img, (x, y))
                else:
                    raise KeyError(f"Symbol {symbol} not found in piece_images")
            except KeyError as e:
                print(f"Warning: {e}")
                continue
        
        # Draw black's captured pieces
        for i, piece in enumerate(black_captured):
            col = i % 8
            row = i // 8
            x = black_label_pos[0] + col * (piece_size + spacing)
            y = black_label_pos[1] + 20 + row * (piece_size + spacing)
            
            # Get the piece image
            try:
                symbol = get_piece_symbol(piece)
                if symbol in self.piece_images:
                    piece_img = self.piece_images[symbol]
                    piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                    surface.blit(piece_img, (x, y))
                else:
                    raise KeyError(f"Symbol {symbol} not found in piece_images")
            except KeyError as e:
                print(f"Warning: {e}")
                continue

    def draw_mode_selection(self, screen) -> None:
        """Draw the game mode selection screen."""
        # Draw background
        self.draw_theme_background(screen, "default")
        
        # Draw title
        title = self.large_font.render("Select Game Mode", True, COLOR_TEXT)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))
        
        # Center-align buttons
        mouse_pos = pygame.mouse.get_pos()
        self.player_vs_ai_button.rect.centerx = WINDOW_WIDTH // 2
        self.local_multiplayer_button.rect.centerx = WINDOW_WIDTH // 2
        
        # Update and draw buttons
        self.player_vs_ai_button.update(mouse_pos)
        self.player_vs_ai_button.draw(screen)
        self.local_multiplayer_button.update(mouse_pos)
        self.local_multiplayer_button.draw(screen)
        
        # Draw universal back button
        self.universal_back_button.update(mouse_pos)
        self.universal_back_button.draw(screen)

    def draw_promotion_menu(self, surface: pygame.Surface, player_color: chess.Color) -> None:
        """Draw the promotion selection menu."""
        menu_width = 300
        menu_height = 100
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (WINDOW_HEIGHT - menu_height) // 2

        # Draw menu background
        pygame.draw.rect(surface, COLOR_BACKGROUND, (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(surface, COLOR_TEXT, (menu_x, menu_y, menu_width, menu_height), 2)

        # Draw promotion options
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        piece_names = ["Queen", "Rook", "Bishop", "Knight"]
        piece_images = ["Q", "R", "B", "N"] if player_color == chess.WHITE else ["q", "r", "b", "n"]

        button_width = menu_width // len(piece_types)
        for i, (piece_type, name, image_key) in enumerate(zip(piece_types, piece_names, piece_images)):
            button_x = menu_x + i * button_width
            button_rect = pygame.Rect(button_x, menu_y, button_width, menu_height)

            # Draw button background
            pygame.draw.rect(surface, COLOR_BUTTON, button_rect)
            pygame.draw.rect(surface, COLOR_TEXT, button_rect, 2)

            # Draw piece image
            if image_key in self.piece_images:
                piece_image = self.piece_images[image_key]
                piece_rect = piece_image.get_rect(center=button_rect.center)
                surface.blit(piece_image, piece_rect)

            # Draw piece name
            text_surface = self.medium_font.render(name, True, COLOR_TEXT)
            text_rect = text_surface.get_rect(center=(button_x + button_width // 2, menu_y + menu_height - 20))
            surface.blit(text_surface, text_rect)

    def get_promotion_selection(self, pos: Tuple[int, int]) -> Optional[chess.PieceType]:
        """
        Get the selected promotion piece based on the mouse click.

        Args:
            pos: The (x, y) position of the mouse click.

        Returns:
            The selected chess.PieceType or None if no selection was made.
        """
        menu_width = 300
        menu_height = 100
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (WINDOW_HEIGHT - menu_height) // 2

        # Define promotion options
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        button_width = menu_width // len(piece_types)

        for i, piece_type in enumerate(piece_types):
            button_x = menu_x + i * button_width
            button_rect = pygame.Rect(button_x, menu_y, button_width, menu_height)
            if button_rect.collidepoint(pos):
                return piece_type

        return None

    # Second implementation of draw_local_multiplayer_captured_pieces was removed

class VolumeSlider:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_rect = pygame.Rect(x, y, 15, height + 10)
        self.value = 0.7  # Default volume
        self.dragging = False
        self.update_knob_position()
    
    def update_knob_position(self):
        # Position knob based on value
        self.knob_rect.centerx = self.rect.left + int(self.value * self.rect.width)
        self.knob_rect.centery = self.rect.centery
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.knob_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Calculate new value based on mouse position
            mouse_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.value = (mouse_x - self.rect.left) / self.rect.width
            self.value = max(0.0, min(1.0, self.value))  # Clamp between 0 and 1
            self.update_knob_position()
    
    def draw(self, surface):
        # Draw slider track
        pygame.draw.rect(surface, (80, 80, 80), self.rect)
        pygame.draw.rect(surface, (120, 120, 120), self.rect, 1)
        
        # Draw filled portion
        filled_rect = pygame.Rect(self.rect.left, self.rect.top, 
                                int(self.rect.width * self.value), self.rect.height)
        pygame.draw.rect(surface, (60, 120, 180), filled_rect)
        
        # Draw knob
        pygame.draw.rect(surface, (200, 200, 200), self.knob_rect)
        pygame.draw.rect(surface, (100, 100, 100), self.knob_rect, 1)
