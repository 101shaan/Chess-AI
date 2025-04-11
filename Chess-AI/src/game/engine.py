class ChessEngine:
    def __init__(self):
        self.board = None  # This will hold the current state of the chessboard
        self.history = []  # To keep track of moves made

    def initialize_board(self):
        """Initialize the chessboard to the starting position."""
        self.board = chess.Board()
        self.history = []

    def generate_moves(self):
        """Generate all legal moves for the current position."""
        return list(self.board.legal_moves)

    def make_move(self, move):
        """Make a move on the board and update history."""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.history.append(move)
            return True
        return False

    def undo_move(self):
        """Undo the last move made."""
        if self.history:
            self.board.pop()
            self.history.pop()

    def evaluate_board(self):
        """Evaluate the board position and return a score."""
        # Placeholder for evaluation logic
        return 0

    def is_checkmate(self):
        """Check if the current position is checkmate."""
        return self.board.is_checkmate()

    def is_stalemate(self):
        """Check if the current position is stalemate."""
        return self.board.is_stalemate()

    def get_game_state(self):
        """Return the current game state."""
        return {
            'is_checkmate': self.is_checkmate(),
            'is_stalemate': self.is_stalemate(),
            'is_insufficient_material': self.board.is_insufficient_material(),
        }