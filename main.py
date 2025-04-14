"""
main application flow for the chess game.
handles:
- state management (menu, gameplay, results)
- event handling for user input
- rendering the game interface
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

# import custom modules
from config import *
from engine.engine_manager import ChessEngine
from modules.board import GameBoard
from modules.ui import ChessUI, SQUARE_SIZE, BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BACKGROUND, COLOR_TEXT
from modules.audio import AudioManager
from modules.settings import SettingsManager, THEMES

# game mode constants
GAME_MODE_MENU = 0
GAME_MODE_PLAY = 1
GAME_MODE_RESULT = 2
GAME_MODE_SETTINGS = 3

class ChessGame:
    def __init__(self) -> None:
        """initialize the chess game and all its components"""
        # initialize pygame
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        # set up display and game clock
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # initialize settings manager
        self.settings = SettingsManager()

        # always start with default theme
        self.settings.set_theme("default")

        # initialize game components
        self.board = GameBoard()
        self.ui = ChessUI()
        self.audio = AudioManager()

        # apply current settings
        self.apply_settings()

        # game state variables
        self.game_mode = GAME_MODE_MENU
        self.previous_mode = GAME_MODE_MENU  # used to track where to return from settings
        self.selected_square: Optional[chess.Square] = None
        self.highlighted_squares: List[chess.Square] = []
        self.human_turn = True  # true for white, false for black
        self.human_color = chess.WHITE  # default - will be set during new game
        self.ai_skill_level = DEFAULT_SKILL_LEVEL
        self.ai_rating = self.calculate_ai_rating(self.ai_skill_level)
        self.ai_thinking = False
        self.last_ai_move_time = 0
        self.move_in_progress = False

        # move history navigation
        self.viewing_history = False
        self.history_position = 0
        self.history_board = None

        # color selection state
        self.show_color_selection = False
        self.color_selected = None

        # hint system
        self.hints_remaining = 0
        self.max_hints = 3
        self.show_hint_selection = False
        self.hint_selected = False
        self.hint_move = None

        # game over animation
        self.game_over_start_time = 0
        self.game_over_phase = 0  # 0: none, 1: "checkmate", 2: "you win/lose"

        # initialize engine with error handling
        self.engine = None
        try:
            self.engine = ChessEngine(DEFAULT_ENGINE_PATH)
            if not self.engine.init_engine():
                self.show_error_and_exit(
                    "failed to initialize chess engine.\n"
                    "please ensure stockfish is installed in engine/ directory\n"
                    "download from: https://stockfishchess.org/download/"
                )
        except Exception as e:
            self.show_error_and_exit(str(e))

        # start background music
        self.start_background_music()

        # game result
        self.game_result: Optional[str] = None
        self.game_result_message: Optional[str] = None

    def calculate_ai_rating(self, skill_level: int) -> int:
        """
        estimate the ai's elo rating based on its skill level

        args:
            skill_level: ai skill level (0-20)

        returns:
            the estimated elo rating
        """
        if skill_level == 0:
            # "martin" level - complete beginner (like on chess.com)
            return 300
        elif skill_level == 1:
            return 400
        elif skill_level == 2:
            return 500
        elif skill_level == 3:
            return 650
        elif skill_level == 4:
            return 800
        elif skill_level < 10:
            # medium skill levels
            return 900 + ((skill_level - 5) * 100)
        else:
            # advanced skill levels (10-20)
            return 1400 + ((skill_level - 10) * 150)

    def run(self) -> None:
        """run the main game loop"""
        running = True
        while running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

    def handle_events(self) -> None:
        """process user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            # volume slider handling (for settings screen)
            if self.game_mode == GAME_MODE_SETTINGS and hasattr(self.ui, 'volume_slider'):
                self.ui.volume_slider.handle_event(event)
                # update actual volume when slider changes
                self.audio.set_volume(self.ui.volume_slider.value)

            # handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)

            # handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # return to menu or quit game
                    if self.game_mode == GAME_MODE_PLAY:
                        self.game_mode = GAME_MODE_MENU
                    elif self.game_mode == GAME_MODE_SETTINGS:
                        self.game_mode = self.previous_mode
                    elif self.game_mode == GAME_MODE_MENU:
                        self.quit()

                # new game with key press
                if event.key == pygame.K_n:
                    self.new_game()
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        """
        so this handles mouse click events.

        args:
            pos: the (x, y) position of the mouse click.
        """
        # first, let's check if the universal back button was clicked
        if self.ui.universal_back_button.is_clicked(pos):
            self.handle_back_button()
            return
        
        # for gameplay, check if the move navigation buttons were clicked
        if self.game_mode == GAME_MODE_PLAY:
            if self.ui.move_back_button.is_clicked(pos):
                self.navigate_move_history(-1)  # go back one move
                return
                
            if self.ui.move_forward_button.is_clicked(pos):
                self.navigate_move_history(1)  # go forward one move
                return
        
        # if we're on the color selection screen, handle those buttons
        if self.show_color_selection:
            if self.ui.white_button.is_clicked(pos):
                self.start_game_with_color(chess.WHITE)
            elif self.ui.black_button.is_clicked(pos):
                self.start_game_with_color(chess.BLACK)
            elif self.ui.random_button.is_clicked(pos):
                # randomly pick a color for the player
                player_color = chess.WHITE if random.choice([True, False]) else chess.BLACK
                self.start_game_with_color(player_color)
            return
        
        # if we're on the hint selection screen, handle hint buttons
        if self.show_hint_selection:
            if self.ui.no_hints_button.is_clicked(pos):
                self.set_hints(0)
            elif self.ui.one_hint_button.is_clicked(pos):
                self.set_hints(1)
            elif self.ui.two_hints_button.is_clicked(pos):
                self.set_hints(2)
            elif self.ui.three_hints_button.is_clicked(pos):
                self.set_hints(3)
            return
        
        # handle clicks on the menu screen
        if self.game_mode == GAME_MODE_MENU:
            if self.ui.new_game_button.is_clicked(pos):
                self.new_game()
            elif self.ui.settings_button.is_clicked(pos):
                self.previous_mode = GAME_MODE_MENU
                self.game_mode = GAME_MODE_SETTINGS
            elif self.ui.quit_button.is_clicked(pos):
                self.quit()
            elif self.ui.difficulty_up_button.is_clicked(pos):
                # increase difficulty, but don't go above 20
                self.ai_skill_level = min(20, self.ai_skill_level + 1)
                self.engine.set_difficulty(self.ai_skill_level)
                self.ai_rating = self.calculate_ai_rating(self.ai_skill_level)
            elif self.ui.difficulty_down_button.is_clicked(pos):
                # decrease difficulty, but don't go below 0
                self.ai_skill_level = max(0, self.ai_skill_level - 1)
                self.engine.set_difficulty(self.ai_skill_level)
                self.ai_rating = self.calculate_ai_rating(self.ai_skill_level)
        
        # if we're in the settings screen, handle those clicks
        elif self.game_mode == GAME_MODE_SETTINGS:
            # check if any theme buttons were clicked
            for theme_name, button in self.ui.theme_buttons.items():
                if button.is_clicked(pos):
                    self.settings.set_theme(theme_name)
                    self.apply_settings()
            
            # handle the music toggle button
            if self.ui.music_toggle_button.is_clicked(pos):
                current_state = self.settings.is_music_enabled()
                self.settings.set_music_enabled(not current_state)
                
                if self.settings.is_music_enabled():
                    self.start_background_music()
                else:
                    self.audio.stop_music()
            
            # handle the back button
            if self.ui.back_button.is_clicked(pos):
                # go back to the previous mode (menu or game)
                self.game_mode = self.previous_mode
        
        # handle clicks on the game result screen
        elif self.game_mode == GAME_MODE_RESULT:
            if self.ui.menu_button.is_clicked(pos):
                self.game_mode = GAME_MODE_MENU
        
        # handle clicks during gameplay
        elif self.game_mode == GAME_MODE_PLAY:
            # skip if the game over animation is still running
            if self.game_over_phase > 0:
                return
                
            # check if the in-game settings button was clicked
            if self.ui.in_game_settings_button.is_clicked(pos):
                self.previous_mode = GAME_MODE_PLAY
                self.game_mode = GAME_MODE_SETTINGS
                return
            
            # check if the hint button was clicked (and if hints are available)
            if self.ui.hint_button.is_clicked(pos) and self.hints_remaining > 0 and self.human_turn:
                self.show_hint()
                return
                
            # skip if it's not the human's turn or if a move is in progress
            if not self.human_turn or self.move_in_progress or self.ai_thinking:
                return
                
            # check if the click was on the board
            square = self.ui.pos_to_square(pos)
            if square is not None:
                self.handle_board_click(square)
    
    def navigate_move_history(self, direction: int) -> None:
        """
        lets you navigate through the move history.

        args:
            direction: -1 to go back, 1 to go forward.
        """
        # if this is the first time entering history mode, save the current board state
        if not self.viewing_history:
            self.history_board = self.board.board.copy()
            self.viewing_history = True
            self.history_position = len(self.board.move_history)
        
        # calculate the new position in the history
        new_position = self.history_position + direction
        
        # make sure the new position is within valid bounds
        if new_position < 0 or new_position > len(self.board.move_history):
            return
        
        # update the history position
        self.history_position = new_position
        
        # reset the board to its initial state
        self.board.board = chess.Board()
        
        # apply moves up to the current history position
        for i in range(self.history_position):
            if i < len(self.board.move_history):
                self.board.board.push(self.board.move_history[i])
        
        # clear any selections or highlights
        self.selected_square = None
        self.highlighted_squares = []
        
        # if we're back at the current position, exit history mode
        if self.history_position == len(self.board.move_history):
            self.viewing_history = False
            self.board.board = self.history_board
            self.history_board = None
    
    def handle_back_button(self) -> None:
        """handles what happens when the universal back button is clicked."""
        if self.game_mode == GAME_MODE_SETTINGS:
            # go back to the previous mode (menu or game)
            self.game_mode = self.previous_mode
        elif self.game_mode == GAME_MODE_PLAY and self.viewing_history:
            # exit history view mode
            self.viewing_history = False
            self.board.board = self.history_board
            self.history_board = None
        elif self.game_mode == GAME_MODE_PLAY:
            # for now, just go back to the menu
            self.game_mode = GAME_MODE_MENU
        elif self.game_mode == GAME_MODE_RESULT:
            self.game_mode = GAME_MODE_MENU
        elif self.show_color_selection:
            self.show_color_selection = False
            self.game_mode = GAME_MODE_MENU
        elif self.show_hint_selection:
            self.show_hint_selection = False
            self.show_color_selection = True
    
    def apply_settings(self) -> None:
        """Apply the current settings to the game."""
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
        """Play background music if enabled in settings."""
        if self.settings.is_music_enabled():
            music_dir = "assets/sounds/background_music"
            
            # Get all music files in the directory
            music_files = []
            for file in os.listdir(music_dir):
                if file.endswith('.mp3') or file.endswith('.ogg') or file.endswith('.wav'):
                    music_files.append(file)
            
            if music_files:
                # Choose a random music file
                random_music = random.choice(music_files)
                full_path = os.path.join(music_dir, random_music)
                
                if os.path.exists(full_path):
                    self.audio.play_music(full_path)
                    print(f"Playing music: {random_music}")
    
    def handle_board_click(self, square: chess.Square) -> None:
        """Handle clicks on the chessboard during gameplay."""
        # If no square is selected yet
        if self.selected_square is None:
            piece = self.board.board.piece_at(square)
            # Only select squares with pieces of the player's color and only during the player's turn
            if piece and piece.color == self.human_color and self.human_turn:
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
        """Execute a move on the board."""
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
        """Update the game state and animations."""
        # Update animations
        animation_complete = not self.ui.update_animations()
        if animation_complete:
            # If animations are finished, set move_in_progress to False
            self.move_in_progress = False
            
            # If it's AI's turn and AI is not already thinking, start AI move calculation
            if not self.human_turn and not self.ai_thinking and not self.move_in_progress and self.game_mode == GAME_MODE_PLAY:
                # If AI is not yet thinking, start the move calculation
                if not self.ai_thinking:
                    self.ai_thinking = True
                    self.last_ai_move_time = time.time()
                    self.engine.get_move(self.board.board, self.ai_skill_level)
        
        # If AI is thinking, check if move is ready
        if self.ai_thinking and self.game_mode == GAME_MODE_PLAY:
            # Check if AI move is ready
            if self.engine.is_move_ready():
                # Get the calculated move
                ai_move = self.engine.get_calculated_move()
                
                if ai_move:
                    # Make the move on the board
                    self.board.make_move(ai_move)
                    
                    # Start animation for the move
                    self.ui.animate_move(ai_move, self.board.board)
                    self.move_in_progress = True
                    
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

        # Check for game over
        if self.game_mode == GAME_MODE_PLAY:
            # Get current game state dictionary
            game_state_dict = self.board.get_game_state()
            
            # Check for endgame conditions
            if game_state_dict['is_checkmate'] or game_state_dict['is_stalemate'] or game_state_dict['is_insufficient_material']:
                # Record the time when game over was detected
                if self.game_over_phase == 0:
                    self.game_over_start_time = time.time()
                    self.game_over_phase = 1  # Start with "CHECKMATE" animation
                    
                    if game_state_dict['is_checkmate']:
                        # Play checkmate sound
                        self.audio.play('checkmate')
                    else:
                        # Play draw sound
                        self.audio.play('game_over')
                
                # Phase 1: Show CHECKMATE for 5 seconds
                if self.game_over_phase == 1 and time.time() - self.game_over_start_time >= 5.0:
                    self.game_over_phase = 2  # Switch to "YOU WIN/LOSE" animation
                    self.game_over_start_time = time.time()  # Reset timer for next phase
                
                # Phase 2: Show YOU WIN/LOSE for 3 seconds
                elif self.game_over_phase == 2 and time.time() - self.game_over_start_time >= 3.0:
                    # Switch to result screen after animations
                    self.game_over_phase = 0  # Reset for next game
                    
                    # Set result and message
                    if game_state_dict['is_checkmate']:
                        winner_color = chess.WHITE if self.board.board.outcome().winner else chess.BLACK
                        winner_name = "White" if winner_color == chess.WHITE else "Black"
                        player_won = (winner_color == self.human_color)
                        self.game_result = "checkmate"
                        self.game_result_message = f"You Win!" if player_won else "You Lose!"
                    else:
                        # It's a draw
                        self.game_result = "draw"
                        if game_state_dict['is_stalemate']:
                            self.game_result_message = "Game Drawn by Stalemate"
                        elif game_state_dict['is_insufficient_material']:
                            self.game_result_message = "Game Drawn by Insufficient Material"
                        else:
                            self.game_result_message = "Game Drawn"
                    
                    self.game_mode = GAME_MODE_RESULT
    
    def check_game_end(self) -> bool:
        """Check if the game has ended and handle the result."""
        # Get the game state (which is a dictionary, not a string)
        state_dict = self.board.get_game_state()
        
        # Check for game ending conditions
        if state_dict['is_checkmate'] or state_dict['is_stalemate'] or state_dict['is_insufficient_material']:
            # Start the game over animation sequence
            if self.game_over_phase == 0:
                self.game_over_start_time = time.time()
                self.game_over_phase = 1  # Start with "CHECKMATE" animation
                
                if state_dict['is_checkmate']:
                    # Play checkmate sound
                    self.audio.play('checkmate')
                else:
                    # Play draw sound
                    self.audio.play('game_over')
        
            # Let the update method handle the animation sequence
            return True
    
        return False
    
    def render(self) -> None:
        """Render the game interface based on the current mode."""
        # Clear the screen
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw based on game mode
        if self.game_mode == GAME_MODE_MENU:
            if self.show_color_selection:
                self.render_color_selection()
            elif self.show_hint_selection:
                self.render_hint_selection()
            else:
                self.render_menu()
        elif self.game_mode == GAME_MODE_PLAY:
            self.render_game()
        elif self.game_mode == GAME_MODE_RESULT:
            self.render_result()
        elif self.game_mode == GAME_MODE_SETTINGS:
            self.render_settings()
        
        # Update display
        pygame.display.flip()

    def render_color_selection(self) -> None:
        """Render the screen for selecting player color."""
        # Draw background with current theme
        self.ui.draw_theme_background(self.screen, self.settings.get_theme())
        
        # Have the UI draw the color selection interface
        self.ui.draw_color_selection(self.screen)

    def render_hint_selection(self) -> None:
        """Render the screen for selecting the number of hints."""
        # Draw background with current theme
        self.ui.draw_theme_background(self.screen, self.settings.get_theme())
        
        # Have the UI draw the hint selection interface
        self.ui.draw_hint_selection(self.screen)

    def render_game(self) -> None:
        """Render the chessboard and in-game UI."""
        # Use the updated draw_game method with theme support
        self.ui.draw_game(
            self.screen,
            self.board,
            self.selected_square,
            self.highlighted_squares,
            self.human_turn,
            self.ai_thinking,
            time.time() - self.last_ai_move_time if self.ai_thinking else 0,
            self.settings.get_theme(),
            self.hints_remaining,
            self.hint_move,
            self.viewing_history
        )
        
        # Draw game over animation if in progress
        if self.game_over_phase > 0:
            if self.game_over_phase == 1:
                # Draw CHECKMATE text overlay
                self.ui.draw_checkmate_overlay(self.screen)
            elif self.game_over_phase == 2:
                # Draw WIN/LOSE text overlay
                is_winner = False
                if self.board.board.outcome():
                    is_winner = (self.board.board.outcome().winner == self.human_color)
                self.ui.draw_result_overlay(self.screen, is_winner)
    
    def render_menu(self) -> None:
        """Render the main menu screen."""
        # Draw the menu UI with current theme
        self.ui.draw_menu(self.screen, self.ai_skill_level, self.ai_rating, self.settings.get_theme())

    def render_result(self) -> None:
        """Render the game result screen."""
        # Clear screen
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw the result UI
        self.ui.draw_game_result(self.screen, self.game_result_message, self.ai_rating)

    def render_settings(self) -> None:
        """Render the settings screen."""
        # Determine if we should return to game when back is clicked
        return_to_game = (self.previous_mode == GAME_MODE_PLAY)
        
        # Draw the settings UI
        self.ui.draw_settings(self.screen, self.settings, return_to_game)
    
    def new_game(self) -> None:
        """Start a new chess game."""
        # Show color selection first
        self.show_color_selection = True
        self.show_hint_selection = False
        self.color_selected = None
        self.hint_selected = False
    
        # Disable other controls until selections are made
        self.game_mode = GAME_MODE_MENU

    def start_game_with_color(self, color: chess.Color) -> None:
        """Begin a new game with the selected player color."""
        # Initialize a new board
        self.board = GameBoard()
        
        # Store player color and set initial turn
        self.human_color = color
        self.human_turn = (color == chess.WHITE)
        
        # Set the board orientation based on player color
        # When playing as black, the board will be flipped so player's pieces are at the bottom
        self.ui.set_board_orientation(color)
        
        # Reset game state
        self.selected_square = None
        self.highlighted_squares = []
        self.move_in_progress = False
        self.ai_thinking = False
        self.game_result = None
        self.game_result_message = None
        self.game_over_phase = 0
        
        # Reset engine
        if self.engine:
            self.engine.set_difficulty(self.ai_skill_level)
        
        # Show hint selection
        self.show_hint_selection = True
        self.show_color_selection = False

    def set_hints(self, num_hints: int) -> None:
        """Set the number of hints available to the player."""
        self.hints_remaining = num_hints
        self.hint_selected = True
        self.show_hint_selection = False
        
        # Start the actual game
        self.game_mode = GAME_MODE_PLAY
        
        # Make AI move if AI plays first (player is black)
        if not self.human_turn:
            self.make_ai_move()

    def show_hint(self) -> None:
        """Display a hint for the player's next move."""
        if not self.engine or not self.human_turn or self.hints_remaining <= 0:
            return
        
        # Deselect any currently selected piece
        self.selected_square = None
        
        # Clear any previous hints
        self.hint_move = None
        self.highlighted_squares = []
        
        # Start the engine calculation
        self.engine.get_move(self.board.board, self.ai_skill_level)
        
        # We need to wait for the move calculation to complete
        # This is a simplified synchronous approach for hints
        waiting_start = time.time()
        waiting_timeout = 1.0  # Maximum waiting time for a hint (in seconds)
        
        # Wait for the move calculation to complete or timeout
        while not self.engine.is_move_ready() and time.time() - waiting_start < waiting_timeout:
            # Check for pygame events while waiting to keep the UI responsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
        
            # Brief pause to prevent CPU hogging
            time.sleep(0.05)

        # Check if we got a move within the timeout
        if self.engine.is_move_ready():
            # Get the calculated best move
            best_move = self.engine.get_calculated_move()
            
            if best_move:
                self.hint_move = best_move
                self.hints_remaining -= 1
                
                # Highlight hint move
                self.highlighted_squares = [best_move.from_square, best_move.to_square]
                self.audio.play('move')  # Play hint sound
        else:
            print("Hint calculation timed out")

    def make_ai_move(self) -> None:
        """Make a move for the AI."""
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
                self.move_in_progress = True
                
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

    def quit(self) -> None:
        """Clean up resources and exit the game."""
        # Close engine
        if self.engine:
            self.engine.close()
        
        # Quit pygame
        pygame.quit()
        
        # Exit program
        sys.exit()
    
    def show_error_and_exit(self, message: str) -> None:
        """Display an error message and exit the application."""
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