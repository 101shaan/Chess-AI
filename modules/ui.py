"""
Modern chess interface with:
- Animated piece movement
- Legal move highlighting
- Move history display
- AI rating tracker
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
    """Chess game UI handler"""
    
    def __init__(self):
        """Initialize the UI"""
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
            BOARD_OFFSET_X,
            BOARD_OFFSET_Y + BOARD_SIZE + 10,
            nav_button_size,
            nav_button_size,
            "←",
            font_size=20
        )
        
        self.move_forward_button = Button(
            BOARD_OFFSET_X + nav_button_size + 10,
            BOARD_OFFSET_Y + BOARD_SIZE + 10,
            nav_button_size,
            nav_button_size,
            "→",
            font_size=20
        )
        
        # Main menu buttons - Adjusted positions for better spacing
        self.new_game_button = Button(
            center_x - button_width // 2,
            150,
            button_width,
            button_height,
            "New Game"
        )
        
        self.settings_button = Button(
            center_x - button_width // 2,
            150 + button_height + button_spacing,
            button_width,
            button_height,
            "Settings"
        )
        
        self.quit_button = Button(
            center_x - button_width // 2,
            150 + (button_height + button_spacing) * 2,
            button_width,
            button_height,
            "Quit"
        )
        
        # Difficulty adjustment buttons
        small_button_size = 40
        self.difficulty_up_button = Button(
            center_x + 100,
            350,  # Moved down below quit button
            small_button_size,
            small_button_size,
            "+"
        )
        
        self.difficulty_down_button = Button(
            center_x - 100 - small_button_size,
            350,  # Moved down below quit button
            small_button_size,
            small_button_size,
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
                'Q': os.path.join(pieces_dir, "black_queen.png"),
                'K': os.path.join(pieces_dir, "black_king.png"),
                
                # Black pieces (lowercase in python-chess) - using the "white_" images which actually show black pieces
                'p': os.path.join(pieces_dir, "white_pawn.png"),
                'n': os.path.join(pieces_dir, "white_knight.png"),
                'b': os.path.join(pieces_dir, "white_bishop.png"),
                'r': os.path.join(pieces_dir, "white_rook.png"),
                'q': os.path.join(pieces_dir, "white_queen.png"),
                'k': os.path.join(pieces_dir, "white_king.png")
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
        """
        Draw the chess board with pieces and highlights
        
        Args:
            surface: Pygame surface to draw on
            board_state: GameBoard object containing the chess state
            current_theme: Current theme name
        """
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
        """Draw chess pieces on the board"""
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
        """
        Draw move highlights on the board
        
        Args:
            surface: Pygame surface to draw on
            selected_square: Currently selected square
            highlighted_squares: Legal move squares to highlight
            hint_move: Optional hint move to highlight differently
        """
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
        """Start a new piece animation for a move"""
        self.animations.append(Animation(move, board, self))
    
    def update_animations(self) -> bool:
        """
        Update all animations and remove completed ones
        
        Returns:
            True if there are still animations in progress, False otherwise
        """
        # Update progress for all animations
        for anim in self.animations:
            anim.update()
        
        # Remove completed animations
        self.animations = [anim for anim in self.animations if not anim.is_complete()]
        
        # Return whether there are still animations in progress
        return len(self.animations) > 0
    
    def draw_menu(self, surface: pygame.Surface, difficulty: int, ai_rating: int, current_theme: str = "default") -> None:
        """Draw the main menu interface"""
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
        
        # Calculate AI ELO based on difficulty level
        ai_elo = 800 + (difficulty * 75)  # Approximate ELO based on skill level
        
        # Draw AI rating with background for better visibility
        ai_label = self.medium_font.render(f"AI Rating: {ai_rating}", True, COLOR_TEXT)
        rating_width = ai_label.get_width() + 20
        rating_height = ai_label.get_height() + 10
        rating_x = WINDOW_WIDTH // 2 - rating_width // 2
        rating_y = WINDOW_HEIGHT // 2 + 40
        
        # Draw background box
        pygame.draw.rect(surface, COLOR_BUTTON, 
                        (rating_x, rating_y, rating_width, rating_height))
        pygame.draw.rect(surface, (50, 50, 50), 
                        (rating_x, rating_y, rating_width, rating_height), 1)
        
        # Draw text centered in the box
        surface.blit(ai_label, (WINDOW_WIDTH // 2 - ai_label.get_width() // 2, 
                              rating_y + 5))
        
        # Update difficulty buttons
        self.difficulty_up_button.update(mouse_pos)
        self.difficulty_down_button.update(mouse_pos)
        self.difficulty_up_button.draw(surface)
        self.difficulty_down_button.draw(surface)
        
        # Draw difficulty help text with background
        help_text = self.small_font.render("Use +/- buttons to adjust AI strength", True, COLOR_TEXT)
        help_width = help_text.get_width() + 20
        help_height = help_text.get_height() + 10
        help_x = WINDOW_WIDTH // 2 - help_width // 2
        help_y = WINDOW_HEIGHT // 2 + 80
        
        # Draw background box
        pygame.draw.rect(surface, COLOR_BUTTON, 
                        (help_x, help_y, help_width, help_height))
        pygame.draw.rect(surface, (50, 50, 50), 
                        (help_x, help_y, help_width, help_height), 1)
        
        # Draw text centered in the box
        surface.blit(help_text, (WINDOW_WIDTH // 2 - help_text.get_width() // 2, 
                               help_y + 5))
    
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
            msg_rect = history_msg.get_rect(center=(WINDOW_WIDTH // 2, 30))
            pygame.draw.rect(surface, (40, 40, 40), 
                            (msg_rect.left - 10, msg_rect.top - 5, 
                            msg_rect.width + 20, msg_rect.height + 10))
            surface.blit(history_msg, msg_rect)
    
    def draw_settings(self, surface: pygame.Surface, settings_manager, return_to_game: bool = False) -> None:
        """
        Draw the settings interface
        
        Args:
            surface: Pygame surface to draw on
            settings_manager: Settings manager instance
            return_to_game: Whether to return to game when back is clicked
        """
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
    
    def draw_game_result(self, surface: pygame.Surface, result_message: str, ai_rating: int) -> None:
        """Draw the game result screen"""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with alpha
        surface.blit(overlay, (0, 0))
        
        # Draw result message
        result_surface = self.large_font.render(result_message, True, (255, 255, 255))
        surface.blit(result_surface, 
                    (WINDOW_WIDTH // 2 - result_surface.get_width() // 2, 
                     WINDOW_HEIGHT // 2 - 100))
        
        # Draw updated AI rating
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
        spaced_text = "C  H E C K M A T E"
        
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