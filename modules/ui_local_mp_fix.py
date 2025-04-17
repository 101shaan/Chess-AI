"""
This file contains the fixed implementation of the local multiplayer UI functions.
It will be used to update the main UI module.
"""

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
    self.draw_local_multiplayer_captured_pieces(surface, board_state)
    
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
    self.in_game_settings_button.update(pygame.mouse.get_pos())
    self.in_game_settings_button.draw(surface)

def draw_local_multiplayer_captured_pieces(self, surface: pygame.Surface, board_state: Any) -> None:
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
    
    # Draw white's captured pieces
    for i, piece in enumerate(white_captured):
        col = i % 8
        row = i // 8
        x = white_label_pos[0] + col * (piece_size + spacing)
        y = white_label_pos[1] + 20 + row * (piece_size + spacing)
        
        # Get the piece image
        piece_img = self.piece_images[piece.piece_type][piece.color]
        piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
        
        # Draw the piece
        surface.blit(piece_img, (x, y))
    
    # Draw black's captured pieces
    for i, piece in enumerate(black_captured):
        col = i % 8
        row = i // 8
        x = black_label_pos[0] + col * (piece_size + spacing)
        y = black_label_pos[1] + 20 + row * (piece_size + spacing)
        
        # Get the piece image
        piece_img = self.piece_images[piece.piece_type][piece.color]
        piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
        
        # Draw the piece
        surface.blit(piece_img, (x, y))
