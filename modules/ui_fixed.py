    def draw_local_multiplayer_game(self, surface: pygame.Surface, board_state: Any, 
                                selected_square: Optional[chess.Square], 
                                highlighted_squares: List[chess.Square],
                                current_player: chess.Color,
                                white_time: int, black_time: int, time_constraint: int,
                                current_theme: str = "default") -> None:
        """Draw the local multiplayer game interface with chess clocks"""
        # Draw the board and pieces
        self.draw_board(surface, board_state, current_theme)
        self.draw_board_labels(surface)
        
        # Draw highlights
        self.draw_highlights(surface, selected_square, highlighted_squares)
        
        # Draw captured pieces
        self.draw_captured_pieces(surface, board_state)
        
        # Draw move history
        self.draw_move_history(surface, board_state)
        
        # Draw player clocks
        white_mins, white_secs = divmod(white_time, 60)
        black_mins, black_secs = divmod(black_time, 60)
        
        white_time_str = f"White: {white_mins:02d}:{white_secs:02d}"
        black_time_str = f"Black: {black_mins:02d}:{black_secs:02d}"
        
        # Determine colors based on current player
        white_color = (50, 200, 50) if current_player == chess.WHITE else COLOR_TEXT
        black_color = (50, 200, 50) if current_player == chess.BLACK else COLOR_TEXT
        
        # Draw time indicators
        white_time_surface = self.medium_font.render(white_time_str, True, white_color)
        black_time_surface = self.medium_font.render(black_time_str, True, black_color)
        
        # Position for time display
        surface.blit(white_time_surface, (BOARD_OFFSET_X + BOARD_SIZE + 20, WINDOW_HEIGHT - 100))
        surface.blit(black_time_surface, (BOARD_OFFSET_X + BOARD_SIZE + 20, 100))
