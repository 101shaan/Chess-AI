"""
Handles all chess rules and state
Required Features:
- Legal move validation
- Game state detection (checkmate/stalemate)
- Move history tracking
- FEN/PGN support
"""
import chess
import chess.pgn
import time
from typing import List, Optional, Tuple, Dict

class GameBoard:
    def __init__(self, fen: str = chess.STARTING_FEN) -> None:
        """
        Initialize the chess board
        
        Args:
            fen: Optional FEN string for board position
        """
        # Initialize python-chess board
        self.board = chess.Board(fen)
        
        # Move history
        self.move_history: List[chess.Move] = []
        
        # Captured pieces
        self.captured_pieces: Dict[bool, List[chess.Piece]] = {
            chess.WHITE: [],
            chess.BLACK: []
        }
        
        # Game state
        self.result = None
        self.result_reason = None
        
        print(f"Board initialized with position: {fen}")
        print(f"Board representation:\n{self.board}")
        
        # Verify board setup
        self._verify_board_setup()
    
    def make_move(self, move: chess.Move) -> bool:
        """
        Make a move on the board
        
        Args:
            move: Chess move to execute
            
        Returns:
            True if the move was legal and executed, False otherwise
        """
        if move in self.board.legal_moves:
            # Record captured piece if any
            if self.board.is_capture(move):
                captured_square = move.to_square
                # For en passant captures, the captured pawn is not on the destination square
                if self.board.is_en_passant(move):
                    # Calculate the square where the captured pawn is
                    captured_square = chess.square(chess.square_file(move.to_square), 
                                                  chess.square_rank(move.from_square))
                
                captured_piece = self.board.piece_at(captured_square)
                if captured_piece:
                    # Add to the appropriate captured list
                    self.captured_pieces[not captured_piece.color].append(captured_piece)
            
            # Make the move
            self.board.push(move)
            self.move_history.append(move)
            
            # Update game state
            self._update_game_state()
            
            return True
        return False

    def undo_move(self) -> Optional[chess.Move]:
        """
        Undo the last move
        
        Returns:
            The move that was undone, or None if no moves to undo
        """
        if not self.move_history:
            return None
        
        # Remove from history
        last_move = self.move_history.pop()
        
        # Handle captured pieces when undoing
        if self.board.is_capture(last_move):
            # If the last move was a capture, remove it from captured list
            if self.captured_pieces[self.board.turn]:
                self.captured_pieces[self.board.turn].pop()
        
        # Undo the move on the board
        self.board.pop()
        
        # Remove the move time
        if hasattr(self, 'move_times') and self.move_times:
            self.move_times.pop()
        
        return last_move
    
    def get_game_state(self) -> Dict:
        """
        Get the current game state
        
        Returns:
            Dictionary with game state information
        """
        state = {
            'is_check': self.board.is_check(),
            'is_checkmate': self.board.is_checkmate(),
            'is_stalemate': self.board.is_stalemate(),
            'is_insufficient_material': self.board.is_insufficient_material(),
            'is_game_over': self.board.is_game_over(),
            'result': self.result,
            'reason': self.result_reason,
            'turn': 'white' if self.board.turn else 'black'
        }
        return state
    
    def get_captured_pieces(self, color: bool) -> List[chess.Piece]:
        """
        Get the pieces captured by the specified color
        
        Args:
            color: Color whose captured pieces to return (True for white, False for black)
            
        Returns:
            List of captured pieces
        """
        return self.captured_pieces[color]
    
    def get_all_captured_pieces(self) -> Dict:
        """
        Get captured pieces for both sides
        
        Returns:
            Dictionary with captured pieces for white and black
        """
        return {
            'white': self.captured_pieces[chess.BLACK],
            'black': self.captured_pieces[chess.WHITE]
        }
    
    def is_promotion_move(self, move: chess.Move) -> bool:
        """
        Check if a move is a pawn promotion
        
        Args:
            move: The move to check
            
        Returns:
            True if the move is a promotion, False otherwise
        """
        piece = self.board.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False
            
        # Check if pawn is moving to the last rank
        to_rank = chess.square_rank(move.to_square)
        return (piece.color == chess.WHITE and to_rank == 7) or \
               (piece.color == chess.BLACK and to_rank == 0)
    
    def get_square_info(self, square: chess.Square) -> Dict:
        """
        Get information about a specific square
        
        Args:
            square: The square to get information about
            
        Returns:
            Dictionary with square information
        """
        piece = self.board.piece_at(square)
        return {
            'piece': piece,
            'square': square,
            'color': chess.square_color(square),
            'file': chess.square_file(square),
            'rank': chess.square_rank(square)
        }
    
    def get_legal_moves_for_square(self, square: chess.Square) -> List[chess.Move]:
        """
        Get all legal moves from a specific square
        
        Args:
            square: The square to get moves for
            
        Returns:
            List of legal moves from that square
        """
        legal_moves = []
        for move in self.board.legal_moves:
            if move.from_square == square:
                legal_moves.append(move)
        return legal_moves
    
    def get_legal_moves(self, square: chess.Square) -> List[chess.Move]:
        """
        Get all legal moves from a square
        
        Args:
            square: Source square
            
        Returns:
            List of legal moves from the square
        """
        return [move for move in self.board.legal_moves if move.from_square == square]
    
    def export_pgn(self) -> str:
        """
        Export the game in PGN format
        
        Returns:
            The game in PGN notation
        """
        game = chess.pgn.Game()
        
        # Set up the headers
        game.headers["Event"] = "Chess AI Game"
        game.headers["Date"] = time.strftime("%Y.%m.%d")
        game.headers["White"] = "Player"
        game.headers["Black"] = "Chess AI"
        game.headers["Result"] = self.get_result_string()
        
        # Reconstruct the game from moves
        node = game
        board = chess.Board()
        for move in self.move_history:
            node = node.add_variation(move)
            board.push(move)
        
        return str(game)
    
    def get_result_string(self) -> str:
        """
        Get the result string for PGN export
        
        Returns:
            String representing the game result
        """
        state = self.get_game_state()
        if state['is_checkmate']:
            return "1-0" if not self.board.turn else "0-1"
        elif state['is_stalemate'] or state['is_insufficient_material']:
            return "1/2-1/2"
        else:
            return "*"  # Game still in progress
    
    def get_fen(self) -> str:
        """
        Get the current position in FEN notation
        
        Returns:
            FEN string
        """
        return self.board.fen()
    
    def load_fen(self, fen: str) -> bool:
        """
        Load a position from FEN notation
        
        Args:
            fen: FEN string to load
            
        Returns:
            True if position was loaded successfully, False otherwise
        """
        try:
            self.board = chess.Board(fen)
            self.move_history = []
            self.captured_pieces = {chess.WHITE: [], chess.BLACK: []}
            if hasattr(self, 'move_times'):
                self.move_times = []
            if hasattr(self, 'last_move_time'):
                self.last_move_time = time.time()
            return True
        except ValueError:
            return False
    
    def _update_game_state(self) -> None:
        """Update the game state after a move"""
        if self.board.is_checkmate():
            self.result = '1-0' if not self.board.turn else '0-1'
            self.result_reason = 'checkmate'
        elif self.board.is_stalemate():
            self.result = '1/2-1/2'
            self.result_reason = 'stalemate'
        elif self.board.is_insufficient_material():
            self.result = '1/2-1/2'
            self.result_reason = 'insufficient material'
        elif self.board.can_claim_draw():
            self.result = '1/2-1/2'
            self.result_reason = 'draw'

    def _verify_board_setup(self) -> None:
        """Verify the board is set up correctly with all pieces in starting positions"""
        # Check if all pieces are in their correct starting positions
        expected_pieces = {
            chess.A1: chess.Piece(chess.ROOK, chess.WHITE),
            chess.B1: chess.Piece(chess.KNIGHT, chess.WHITE),
            chess.C1: chess.Piece(chess.BISHOP, chess.WHITE),
            chess.D1: chess.Piece(chess.QUEEN, chess.WHITE),
            chess.E1: chess.Piece(chess.KING, chess.WHITE),
            chess.F1: chess.Piece(chess.BISHOP, chess.WHITE),
            chess.G1: chess.Piece(chess.KNIGHT, chess.WHITE),
            chess.H1: chess.Piece(chess.ROOK, chess.WHITE),
            chess.A8: chess.Piece(chess.ROOK, chess.BLACK),
            chess.B8: chess.Piece(chess.KNIGHT, chess.BLACK),
            chess.C8: chess.Piece(chess.BISHOP, chess.BLACK),
            chess.D8: chess.Piece(chess.QUEEN, chess.BLACK),
            chess.E8: chess.Piece(chess.KING, chess.BLACK),
            chess.F8: chess.Piece(chess.BISHOP, chess.BLACK),
            chess.G8: chess.Piece(chess.KNIGHT, chess.BLACK),
            chess.H8: chess.Piece(chess.ROOK, chess.BLACK)
        }
        
        # Check pawns
        for file_idx in range(8):
            white_pawn_square = chess.square(file_idx, 1)  # 2nd rank
            black_pawn_square = chess.square(file_idx, 6)  # 7th rank
            
            expected_pieces[white_pawn_square] = chess.Piece(chess.PAWN, chess.WHITE)
            expected_pieces[black_pawn_square] = chess.Piece(chess.PAWN, chess.BLACK)
        
        # Verify all pieces are in their expected positions
        for square, expected_piece in expected_pieces.items():
            actual_piece = self.board.piece_at(square)
            if actual_piece != expected_piece:
                print(f"Board setup error at {chess.square_name(square)}: "
                      f"Expected {expected_piece}, got {actual_piece}")
        
        # Verify empty squares
        for rank_idx in range(2, 6):  # Ranks 3-6 should be empty
            for file_idx in range(8):
                square = chess.square(file_idx, rank_idx)
                if self.board.piece_at(square) is not None:
                    print(f"Board setup error: Unexpected piece at {chess.square_name(square)}")
                    
        print("Board setup verification complete")