import chess
class GameBoard:
    def __init__(self):
        """sets up the chessboard with all the pieces in their starting positions."""
        self.board = self.create_initial_board()
        self.move_history = []

    def create_initial_board(self):
        """creates the initial setup of the board with all the pieces."""
        board = [[None for _ in range(8)] for _ in range(8)]
        # adding pawns for both players
        for i in range(8):
            board[1][i] = 'P'  # white pawns
            board[6][i] = 'p'  # black pawns
        # adding the rest of the pieces (rooks, knights, bishops, queens, kings)
        board[0] = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']  # white pieces
        board[7] = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']  # black pieces
        return board

    def is_en_passant_move(self, move: chess.Move) -> bool:
        """checks if the move is an en passant capture."""
        return self.board.is_en_passant(move)

    def is_promotion_move(self, move: chess.Move) -> bool:
        """checks if the move is a pawn promotion."""
        piece = self.board.piece_at(move.from_square)
        return piece and piece.piece_type == chess.PAWN and chess.square_rank(move.to_square) in [0, 7]

    def is_castling_move(self, move: chess.Move) -> bool:
        """checks if the move is a castling move."""
        return self.board.is_castling(move)

    def is_threefold_repetition(self) -> bool:
        """checks if the current position has occurred three times (threefold repetition)."""
        return self.board.is_repetition(3)

    def is_fifty_move_rule(self) -> bool:
        """checks if the 50-move rule applies (no pawn moves or captures in the last 50 moves)."""
        return self.board.halfmove_clock >= 50

    def make_move(self, move: chess.Move) -> None:
        """executes a move on the board."""
        if self.is_castling_move(move):
            # handle castling
            self.board.push(move)
        elif self.is_en_passant_move(move):
            # handle en passant capture
            self.board.push(move)
        elif self.is_promotion_move(move):
            # handle pawn promotion (defaulting to queen for now)
            move.promotion = chess.QUEEN
            self.board.push(move)
        else:
            # handle regular moves
            self.board.push(move)

    def is_valid_move(self, move):
        """checks if a move is valid according to chess rules."""
        # placeholder for the actual validation logic
        return True

    def get_game_state(self):
        """returns the current state of the game."""
        return {
            'board': self.board,
            'move_history': self.move_history,
            # can add more state details here if needed
        }

    def reset_board(self):
        """resets the board back to its initial state."""
        self.board = self.create_initial_board()
        self.move_history.clear()