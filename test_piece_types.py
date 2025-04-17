"""
Test script to verify piece type constants and movement rules
"""
import chess
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the game's board module
from modules.board import GameBoard

def print_piece_types():
    """Print the piece type constants from python-chess"""
    print("Python-chess piece type constants:")
    print(f"PAWN = {chess.PAWN}")
    print(f"KNIGHT = {chess.KNIGHT}")
    print(f"BISHOP = {chess.BISHOP}")
    print(f"ROOK = {chess.ROOK}")
    print(f"QUEEN = {chess.QUEEN}")
    print(f"KING = {chess.KING}")
    print()

def test_king_queen_moves():
    """Test the movement rules for king and queen"""
    # Create a board with only a king and queen in the center
    board = GameBoard("8/8/8/3QK3/8/8/8/8 w - - 0 1")
    
    # Get legal moves for the king (e5)
    king_square = chess.E5
    king_moves = board.get_legal_moves_for_square(king_square)
    print(f"King at {chess.square_name(king_square)} has {len(king_moves)} legal moves:")
    for move in king_moves:
        print(f"  {move}")
    
    # Get legal moves for the queen (d5)
    queen_square = chess.D5
    queen_moves = board.get_legal_moves_for_square(queen_square)
    print(f"Queen at {chess.square_name(queen_square)} has {len(queen_moves)} legal moves:")
    for move in queen_moves:
        print(f"  {move}")
    
    # Print the piece types at each square to verify
    king_piece = board.board.piece_at(king_square)
    queen_piece = board.board.piece_at(queen_square)
    print(f"\nPiece at e5: {king_piece} (Type: {king_piece.piece_type})")
    print(f"Piece at d5: {queen_piece} (Type: {queen_piece.piece_type})")

if __name__ == "__main__":
    print_piece_types()
    test_king_queen_moves()
