"""
Primary application flow with:
- State management (menu/game/result)
- Event handling
- Render pipeline
"""
import os
import sys
import time
import pygame
import chess
import chess.engine
from typing import Optional, Tuple, List, Dict, Any
import threading
import random

# Import custom modules
from config import *
from engine.engine_manager import ChessEngine
from modules.board import GameBoard
from modules.ui import ChessUI, SQUARE_SIZE, BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BACKGROUND, COLOR_TEXT
from modules.audio import AudioManager
from modules.settings import SettingsManager, THEMES

# Game mode constants
GAME_MODE_MENU = 0
GAME_MODE_PLAY = 1
GAME_MODE_RESULT = 2
GAME_MODE_SETTINGS = 3

class ChessGame:
    def __init__(self) -> None:
        """Initialize the chess application with all required modules"""
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Set up display and game clock
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Initialize settings manager
        self.settings = SettingsManager()
        
        # Initialize game components
        self.board = GameBoard()
        self.ui = ChessUI()
        self.audio = AudioManager()
        
        # Apply current settings
        self.apply_settings()
        
        # Game state variables
        self.game_mode = GAME_MODE_MENU
        self.selected_square: Optional[chess.Square] = None
        self.highlighted_squares: List[chess.Square] = []
        self.human_turn = True  # True for white, False for black
        self.ai_skill_level = DEFAULT_SKILL_LEVEL
        self.ai_rating = self.calculate_ai_rating(self.ai_skill_level)
        self.ai_thinking = False
        self.last_ai_move_time = 0
        self.move_in_progress = False
        
        # Initialize engine with error handling
        self.engine = None
        try:
            self.engine = ChessEngine(DEFAULT_ENGINE_PATH)
            if not self.engine.init_engine():
                self.show_error_and_exit(
                    "Failed to initialize chess engine.\n"
                    "Please ensure Stockfish is installed in engine/ directory\n"
                    "Download from: https://stockfishchess.org/download/"
                )
        except Exception as e:
            self.show_error_and_exit(str(e))
        
        # Start background music
        self.start_background_music()
        
        # Game result
        self.game_result: Optional[str] = None
        self.game_result_message: Optional[str] = None
    
    def calculate_ai_rating(self, skill_level: int) -> int:
        """
        Calculate the AI rating based on skill level
        
        Args:
            skill_level: Skill level (0-20)
        
        Returns:
            Calculated AI rating
        """
        if skill_level < 5:
            # For beginners, show a lower rating even though the engine isn't restricted
            return 800 + (skill_level * 100)
        else:
            # For skill level 5+, match the engine's calculation
            return 1320 + ((skill_level - 5) * 75)
    
    def run(self) -> None:
        """Main game loop"""
        running = True
        while running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
    
    def handle_events(self) -> None:
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                
            # Handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                self.handle_mouse_click(pygame.mouse.get_pos())
                
            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Return to menu or quit game
                    if self.game_mode == GAME_MODE_PLAY:
                        self.game_mode = GAME_MODE_MENU
                    elif self.game_mode == GAME_MODE_SETTINGS:
                        self.game_mode = GAME_MODE_MENU
                    elif self.game_mode == GAME_MODE_MENU:
                        self.quit()
                        
                # New game with key press
                if event.key == pygame.K_n:
                    self.new_game()
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        """
        Handle mouse click event
        
        Args:
            pos: (x, y) position of the click
        """
        # Menu screen click handling
        if self.game_mode == GAME_MODE_MENU:
            if self.ui.new_game_button.is_clicked(pos):
                self.new_game()
            elif self.ui.settings_button.is_clicked(pos):
                self.game_mode = GAME_MODE_SETTINGS
            elif self.ui.quit_button.is_clicked(pos):
                self.quit()
            elif self.ui.difficulty_up_button.is_clicked(pos):
                # Increase difficulty (max 20)
                self.ai_skill_level = min(20, self.ai_skill_level + 1)
                self.ai_rating = self.calculate_ai_rating(self.ai_skill_level)
            elif self.ui.difficulty_down_button.is_clicked(pos):
                # Decrease difficulty (min 0)
                self.ai_skill_level = max(0, self.ai_skill_level - 1)
                self.ai_rating = self.calculate_ai_rating(self.ai_skill_level)
    
        # Settings screen click handling
        elif self.game_mode == GAME_MODE_SETTINGS:
            # Theme buttons
            for theme_name, button in self.ui.theme_buttons.items():
                if button.is_clicked(pos):
                    self.settings.set_theme(theme_name)
                    self.apply_settings()
        
            # Music toggle button
            if self.ui.music_toggle_button.is_clicked(pos):
                current_state = self.settings.is_music_enabled()
                self.settings.set_music_enabled(not current_state)
                
                if self.settings.is_music_enabled():
                    self.start_background_music()
                else:
                    self.audio.stop_music()
        
            # Back button
            if self.ui.back_button.is_clicked(pos):
                self.game_mode = GAME_MODE_MENU
    
        # Game result screen click handling
        elif self.game_mode == GAME_MODE_RESULT:
            if self.ui.menu_button.is_clicked(pos):
                self.game_mode = GAME_MODE_MENU
    
        # Game screen click handling
        elif self.game_mode == GAME_MODE_PLAY:
            # Check for in-game settings button
            if self.ui.in_game_settings_button.is_clicked(pos):
                self.game_mode = GAME_MODE_SETTINGS
                return
            
            # Check if position is on the board
            square = self.ui.pos_to_square(pos)
            if square is not None:
                self.handle_board_click(square)
    
    def apply_settings(self) -> None:
        """Apply current settings to the game"""
        theme = self.settings.get_theme()
        theme_colors = self.settings.get_theme_colors()
        
        # Update global color constants with theme colors
        global COLOR_WHITE, COLOR_BLACK, COLOR_BACKGROUND, COLOR_TEXT
        global COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_HIGHLIGHT, COLOR_MOVE_INDICATOR
        
        COLOR_WHITE = theme_colors["light_square"]
        COLOR_BLACK = theme_colors["dark_square"]
        COLOR_BACKGROUND = theme_colors["background"]
        COLOR_TEXT = theme_colors["text"]
        COLOR_HIGHLIGHT = theme_colors["highlight"]
        COLOR_MOVE_INDICATOR = theme_colors["move_indicator"]
        COLOR_BUTTON = theme_colors["button"]
        COLOR_BUTTON_HOVER = theme_colors["button_hover"]
        
        # Set audio volume
        self.audio.set_volume(self.settings.get_volume())
    
    def start_background_music(self) -> None:
        """Start playing background music based on settings"""
        if self.settings.is_music_enabled():
            music_dir = "assets/sounds/background_music"
            music_file = self.settings.get_current_music()
            full_path = os.path.join(music_dir, music_file)
            
            if os.path.exists(full_path):
                self.audio.play_music(full_path)
    
    def handle_board_click(self, square: chess.Square) -> None:
        """Handle clicks on the chess board during gameplay"""
        # If no square is selected yet
        if self.selected_square is None:
            piece = self.board.board.piece_at(square)
            # Only select squares with pieces of the current player's color
            if piece and ((piece.color == chess.WHITE) == self.human_turn):
                self.selected_square = square
                # Highlight legal moves
                self.highlighted_squares = [
                    move.to_square for move in self.board.board.legal_moves
                    if move.from_square == square
                ]
        else:
            # If a square is already selected
            if square in self.highlighted_squares:
                # Make the move
                move = chess.Move(self.selected_square, square)
                # Check if it's a promotion
                if self.board.is_promotion_move(move):
                    # Always promote to queen for simplicity
                    move.promotion = chess.QUEEN
                
                # Execute the move
                self.make_move(move)
            
            # Clear selection even if an invalid square was clicked
            self.selected_square = None
            self.highlighted_squares = []
    
    def make_move(self, move: chess.Move) -> None:
        """Make a move on the board"""
        # Make the move on the board
        self.board.make_move(move)
        
        # Start animation for the move
        self.ui.animate_move(move, self.board.board)
        
        # Play appropriate sound
        if self.board.board.is_capture(move):
            self.audio.play('capture')
        else:
            self.audio.play('move')
            
        # Check if the move resulted in check
        if self.board.board.is_check():
            self.audio.play('check')
            
        # Switch turns
        self.human_turn = not self.human_turn
        
        # Check game state
        self.check_game_end()
    
    def update(self) -> None:
        """Update game state"""
        # Only update if in play mode
        if self.game_mode != GAME_MODE_PLAY:
            return
        
        # Update animations
        if self.ui.update_animations():
            self.move_in_progress = True
            return  # Don't process other updates while animating
        else:
            self.move_in_progress = False
        
        # Check for game end conditions
        if self.check_game_end():
            return
        
        # Handle AI move if it's the AI's turn
        if not self.human_turn and not self.move_in_progress:
            # If AI is not yet thinking, start the move calculation
            if not self.ai_thinking:
                self.ai_thinking = True
                self.last_ai_move_time = time.time()
                self.engine.get_move(self.board.board, self.ai_skill_level)
                return
            
            # Check if AI move is ready
            if self.engine.is_move_ready():
                # Get the calculated move
                ai_move = self.engine.get_calculated_move()
                
                if ai_move:
                    # Make the move on the board
                    self.board.make_move(ai_move)
                    
                    # Start animation for the move
                    self.ui.animate_move(ai_move, self.board.board)
                    
                    # Play move sound
                    self.audio.play("move")
                    
                    # Switch back to human turn
                    self.human_turn = True
                    self.ai_thinking = False
                    
                    # Clear any previous selection
                    self.selected_square = None
                    self.highlighted_squares = []
                    
                    # Check for game end after AI move
                    self.check_game_end()
    
    def check_game_end(self) -> bool:
        """Check if the game has ended"""
        state = self.board.get_game_state()
        
        if state == "checkmate" or state == "stalemate":
            self.game_mode = GAME_MODE_RESULT
            
            if state == "checkmate":
                winner = "Player" if not self.human_turn else "AI"
                self.game_result = "win" if winner == "Player" else "loss"
                self.game_result_message = f"Checkmate! {winner} wins."
            else:
                self.game_result = "draw"
                self.game_result_message = "Stalemate! The game is a draw."
            
            return True
        
        return False
    
    def render(self) -> None:
        """Render the game based on current mode"""
        # Clear the screen
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw based on game mode
        if self.game_mode == GAME_MODE_MENU:
            self.render_menu()
        elif self.game_mode == GAME_MODE_PLAY:
            self.render_game()
        elif self.game_mode == GAME_MODE_RESULT:
            self.render_result()
        elif self.game_mode == GAME_MODE_SETTINGS:
            self.render_settings()
        
        # Update display
        pygame.display.flip()

    def render_menu(self) -> None:
        """Render the main menu"""
        # Clear screen
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw the menu UI
        self.ui.draw_menu(self.screen, self.ai_skill_level, self.ai_rating)
        
        # Flip display
        pygame.display.flip()
    
    def render_game(self) -> None:
        """Render the game board and UI"""
        # Draw the chess board and pieces
        self.ui.draw_board(self.screen, self.board)
        
        # Draw highlighted squares for selection
        self.ui.draw_highlights(
            self.screen, 
            self.selected_square, 
            self.highlighted_squares
        )
        
        # Draw animated pieces on top
        self.ui.draw_animated_pieces(self.screen, self.board)
        
        # Draw game info
        turn_text = "Your Turn" if self.human_turn else "AI Thinking..."
        turn_surface = self.ui.medium_font.render(turn_text, True, COLOR_TEXT)
        self.screen.blit(turn_surface, (BOARD_OFFSET_X + BOARD_SIZE + 20, BOARD_OFFSET_Y))
        
        # Draw captured pieces
        self.ui.draw_captured_pieces(self.screen, self.board)
        
        # Draw AI info if AI is thinking
        if self.ai_thinking:
            thinking_time = time.time() - self.last_ai_move_time
            self.ui.draw_thinking_indicator(self.screen, thinking_time)
        
        # Draw settings button in-game
        mouse_pos = pygame.mouse.get_pos()
        self.ui.in_game_settings_button.update(mouse_pos)
        self.ui.in_game_settings_button.draw(self.screen)
    
    def render_result(self) -> None:
        """Render the game result screen"""
        # Clear screen
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw the result UI
        self.ui.draw_game_result(self.screen, self.game_result_message, self.ai_rating)
        
        # Flip display
        pygame.display.flip()
    
    def render_settings(self) -> None:
        """Render the settings screen"""
        # Clear screen
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw the settings UI
        self.ui.draw_settings(self.screen, self.settings)
        
        # Flip display
        pygame.display.flip()
    
    def new_game(self) -> None:
        """Start a new chess game"""
        # Initialize a new board
        self.board = GameBoard()
        
        # Reset game state
        self.selected_square = None
        self.highlighted_squares = []
        self.human_turn = True  # Player starts as white
        self.game_mode = GAME_MODE_PLAY
        self.game_result = None
        self.game_result_message = None
        self.move_in_progress = False
        self.ai_thinking = False
        self.last_ai_move_time = time.time()
        
        # Configure the engine with the current skill level
        if self.engine:
            self.engine.set_difficulty(self.ai_skill_level)
        
        # Play sound
        self.audio.play('game_start')
    
    def quit(self) -> None:
        """Clean up resources and exit the game"""
        # Close engine
        if self.engine:
            self.engine.close()
        
        # Quit pygame
        pygame.quit()
        
        # Exit program
        sys.exit()
    
    def show_error_and_exit(self, message: str) -> None:
        """Display error message and exit"""
        print(f"ERROR: {message}")
        
        # Try to show error on screen
        try:
            self.screen.fill((0, 0, 0))
            font = pygame.font.SysFont("Arial", 24)
            
            # Split message into lines
            lines = message.split('\n')
            for i, line in enumerate(lines):
                text = font.render(line, True, (255, 0, 0))
                self.screen.blit(text, (50, 50 + i * 30))
            
            pygame.display.flip()
            pygame.time.wait(5000)  # Show for 5 seconds
        except:
            pass
            
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    # Create and run the game
    game = ChessGame()
    game.run()