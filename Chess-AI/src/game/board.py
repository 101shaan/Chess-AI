class GameBoard:
    def __init__(self):
        """Initialize the chessboard with pieces in starting positions."""
        self.board = self.create_initial_board()
        self.move_history = []

    def create_initial_board(self):
        """Create the initial board setup with pieces."""
        board = [[None for _ in range(8)] for _ in range(8)]
        # Place pieces for both players
        # Example for pawns
        for i in range(8):
            board[1][i] = 'P'  # White pawns
            board[6][i] = 'p'  # Black pawns
        # Add other pieces (Rooks, Knights, Bishops, Queens, Kings)
        board[0] = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']  # White pieces
        board[7] = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']  # Black pieces
        return board

    def make_move(self, move):
        """Make a move on the board."""
        from_square = move.from_square
        to_square = move.to_square
        piece = self.board[from_square.row][from_square.col]
        self.board[to_square.row][to_square.col] = piece
        self.board[from_square.row][from_square.col] = None
        self.move_history.append(move)

    def is_valid_move(self, move):
        """Check if a move is valid according to chess rules."""
        # Implement move validation logic
        return True  # Placeholder for actual validation logic

    def get_game_state(self):
        """Return the current game state."""
        return {
            'board': self.board,
            'move_history': self.move_history,
            # Add more state information as needed
        }

    def reset_board(self):
        """Reset the board to the initial state."""
        self.board = self.create_initial_board()
        self.move_history.clear()