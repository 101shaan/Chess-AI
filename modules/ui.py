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
BOARD_OFFSET_Y = 80

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
    def __init__(self) -> None:
        """Initialize the Chess UI"""
        # Load piece images
        self.piece_images = self.load_pieces()
        
        # Text rendering
        pygame.font.init()
        
        # Piece animations
        self.animations: List[Animation] = []
        
        # Create font objects
        self.large_font = pygame.font.SysFont("Arial", FONT_SIZE_LARGE)
        self.medium_font = pygame.font.SysFont("Arial", FONT_SIZE_MEDIUM)
        self.small_font = pygame.font.SysFont("Arial", FONT_SIZE_SMALL)
        
        # Calculate button positions
        center_x = WINDOW_WIDTH // 2
        button_width = 200
        button_height = 50
        button_spacing = 20
        
        # Main menu buttons
        self.new_game_button = Button(
            center_x - button_width // 2,
            200,
            button_width,
            button_height,
            "New Game"
        )
        
        self.quit_button = Button(
            center_x - button_width // 2,
            200 + button_height + button_spacing,
            button_width,
            button_height,
            "Quit"
        )
        
        # Difficulty adjustment buttons
        small_button_size = 40
        self.difficulty_up_button = Button(
            center_x + 100,
            300,
            small_button_size,
            small_button_size,
            "+"
        )
        
        self.difficulty_down_button = Button(
            center_x - 100 - small_button_size,
            300,
            small_button_size,
            small_button_size,
            "-"
        )
        
        # Game over screen buttons
        self.menu_button = Button(
            center_x - button_width // 2,
            350,
            button_width,
            button_height,
            "Back to Menu"
        )
        
        # Last square clicked
        self.last_click = None
        
    def load_pieces(self) -> Dict[str, pygame.Surface]:
        """Load chess piece images from assets folder"""
        pieces = {}
        try:
            # Define the mapping between chess notation and filenames
            piece_mapping = {
                'P': 'pawn',
                'N': 'knight',
                'B': 'bishop',
                'R': 'rook',
                'Q': 'queen',
                'K': 'king'
            }
            
            color_mapping = {
                'w': 'white',
                'b': 'black'
            }
            
            # Check if assets directory exists
            pieces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "pieces")
            if not os.path.exists(pieces_dir):
                print(f"Warning: pieces directory not found at {pieces_dir}")
                return pieces
                
            for color_code, color_name in color_mapping.items():
                for piece_code, piece_name in piece_mapping.items():
                    key = color_code + piece_code
                    file_path = os.path.join(pieces_dir, f"{color_name}_{piece_name}.png")
                    
                    if os.path.exists(file_path):
                        # Load and scale image to fit square
                        img = pygame.image.load(file_path)
                        pieces[key] = pygame.transform.scale(
                            img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10)
                        )
                    else:
                        print(f"Warning: Piece image {file_path} not found")
        except Exception as e:
            print(f"Error loading piece images: {e}")
            
        return pieces
    
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
        
        # Create and return square
        return chess.square(file_idx, rank_idx)
    
    def draw_board(self, surface: pygame.Surface, board_state: Any) -> None:
        """
        Draw the chess board with pieces and highlights
        
        Args:
            surface: Pygame surface to draw on
            board_state: GameBoard object containing the chess state
        """
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
                color = COLOR_WHITE if is_light else COLOR_BLACK
                
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
            label = chr(ord('a') + file)
            text = self.small_font.render(label, True, COLOR_TEXT)
            
            # Position below the board squares
            x = BOARD_OFFSET_X + file * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
            y_below = BOARD_OFFSET_Y + BOARD_SIZE + 5
            
            # Draw with better contrast background
            pygame.draw.rect(surface, COLOR_BACKGROUND, 
                             (x-2, y_below-2, text.get_width()+4, text.get_height()+4))
            surface.blit(text, (x, y_below))
        
        # Draw rank labels (1-8) on the left
        for rank in range(8):
            label = str(8 - rank)
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
            'P': 'wP', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wQ', 'K': 'wK',
            'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
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
                key = piece_map.get(symbol)
                
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
            'P': 'wP', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wQ', 'K': 'wK',
            'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
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
            
            # Create a transparent highlight surface
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(COLOR_MOVE_INDICATOR)
            
            # Draw highlight
            surface.blit(highlight, (x, y))
    
    def draw_highlights(self, surface: pygame.Surface, 
                        selected_square: Optional[chess.Square], 
                        highlighted_squares: List[chess.Square]) -> None:
        """Draw highlights for selected square and legal moves"""
        # Highlight selected square
        if selected_square is not None:
            pos = self.square_to_coords(selected_square)
            selected_rect = pygame.Rect(
                pos[0] - SQUARE_SIZE // 2,
                pos[1] - SQUARE_SIZE // 2,
                SQUARE_SIZE, SQUARE_SIZE
            )
            
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(COLOR_SELECTED)
            surface.blit(highlight, selected_rect)
        
        # Highlight legal move targets
        for square in highlighted_squares:
            pos = self.square_to_coords(square)
            target_rect = pygame.Rect(
                pos[0] - SQUARE_SIZE // 2,
                pos[1] - SQUARE_SIZE // 2,
                SQUARE_SIZE, SQUARE_SIZE
            )
            
            # Draw a smaller circle in the center of the square
            circle_pos = pos
            pygame.draw.circle(surface, COLOR_MOVE_INDICATOR[:3], circle_pos, SQUARE_SIZE // 4)
    
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
    
    def draw_menu(self, surface: pygame.Surface, difficulty: int, ai_rating: int) -> None:
        """Draw the main menu interface"""
        # Draw title
        title = self.large_font.render("Chess AI", True, COLOR_TEXT)
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self.new_game_button.update(mouse_pos)
        self.new_game_button.draw(surface)
        self.quit_button.update(mouse_pos)
        self.quit_button.draw(surface)
        
        # Calculate AI ELO based on difficulty level
        ai_elo = 800 + (difficulty * 75)  # Approximate ELO based on skill level
        
        # Draw AI rating selection
        ai_label = self.medium_font.render(f"AI Rating: {ai_rating}", True, COLOR_TEXT)
        surface.blit(ai_label, (WINDOW_WIDTH // 2 - ai_label.get_width() // 2, WINDOW_HEIGHT // 2 + 40))
        
        # Update difficulty buttons
        self.difficulty_up_button.update(mouse_pos)
        self.difficulty_down_button.update(mouse_pos)
        self.difficulty_up_button.draw(surface)
        self.difficulty_down_button.draw(surface)
        
        # Draw difficulty help text
        help_text = self.small_font.render("Use +/- buttons to adjust AI strength", True, COLOR_TEXT)
        surface.blit(help_text, (WINDOW_WIDTH // 2 - help_text.get_width() // 2, WINDOW_HEIGHT // 2 + 80))
        
        # Draw instructions
        instructions = [
            "Click a piece to select it",
            "Click a highlighted square to move",
            "Press ESC to return to menu",
            "Press N for a new game"
        ]
        
        y_offset = WINDOW_HEIGHT // 2 + 150
        for instruction in instructions:
            text = self.small_font.render(instruction, True, COLOR_TEXT)
            surface.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, y_offset))
            y_offset += 30
    
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
                piece_key = PIECE_MAPPING.get(piece.symbol().lower(), None)
                if piece_key and piece_key in self.piece_images:
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
                piece_key = PIECE_MAPPING.get(piece.symbol().upper(), None)
                if piece_key and piece_key in self.piece_images:
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