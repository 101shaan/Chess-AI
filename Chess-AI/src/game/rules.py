class ChessRules:
    def __init__(self, board):
        self.board = board

    def is_valid_move(self, move):
        # Implement logic to check if a move is valid according to chess rules
        pass

    def is_check(self, color):
        # Implement logic to check if the given color is in check
        pass

    def is_checkmate(self, color):
        # Implement logic to check if the given color is in checkmate
        pass

    def is_stalemate(self, color):
        # Implement logic to check if the game is in stalemate for the given color
        pass

    def is_insufficient_material(self):
        # Implement logic to check if the game is drawn due to insufficient material
        pass

    def get_legal_moves(self, piece_position):
        # Implement logic to return a list of legal moves for a piece at the given position
        pass

    def is_promotion_move(self, move):
        # Implement logic to check if a move is a promotion move
        pass

    def promote_piece(self, move, promotion_type):
        # Implement logic to promote a piece to the specified type (e.g., queen, rook)
        pass