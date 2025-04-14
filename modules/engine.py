"""
this is a wrapper for the stockfish engine:
- supports adaptive difficulty
- handles move generation and analysis
- ensures proper cleanup to avoid memory issues
"""
import chess
import subprocess
import os
from typing import Optional, Dict, Any

class ChessEngine:
    def __init__(self, engine_path: str = None) -> None:
        """sets up the chess engine with an optional custom path."""
        self.engine_path = engine_path or "stockfish"
        self.process = None
        self.difficulty = 0
    
    def init_engine(self) -> None:
        """starts and configures the stockfish engine."""
        self.process = subprocess.Popen(
            [self.engine_path],
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.set_difficulty(self.difficulty)
    
    def close(self) -> None:
        """shuts down the engine gracefully."""
        if self.process:
            self.process.stdin.write("quit\n")
            self.process.stdin.flush()
            self.process.terminate()
            self.process = None
    
    def get_move(self, board: chess.Board, difficulty: int) -> Optional[chess.Move]:
        """gets the best move for the current board state at the given difficulty."""
        self.set_difficulty(difficulty)
        self.process.stdin.write(f"position fen {board.fen()}\n")
        self.process.stdin.write("go\n")
        self.process.stdin.flush()
        while not self.is_move_ready():
            pass
        return self.get_calculated_move()
    
    def _get_beginner_move(self, board: chess.Board, difficulty: int) -> Optional[chess.Move]:
        """generates a move for beginner-level ai with intentional mistakes."""
        # Placeholder for beginner move logic
        return self.get_move(board, difficulty)
    
    def is_move_ready(self) -> bool:
        """checks if the engine has finished calculating a move."""
        output = self.process.stdout.readline()
        return "bestmove" in output
    
    def get_calculated_move(self) -> Optional[chess.Move]:
        """retrieves the move calculated by the engine."""
        output = self.process.stdout.readline()
        if "bestmove" in output:
            move_str = output.split("bestmove")[1].strip().split(" ")[0]
            return chess.Move.from_uci(move_str)
        return None
    
    def analyze_position(self, board: chess.Board, depth: int = 15) -> Dict[str, Any]:
        """performs a deeper analysis of the current position."""
        self.process.stdin.write(f"position fen {board.fen()}\n")
        self.process.stdin.write(f"go depth {depth}\n")
        self.process.stdin.flush()
        analysis = {}
        while True:
            output = self.process.stdout.readline()
            if "info depth" in output:
                parts = output.split()
                depth_index = parts.index("depth") + 1
                score_index = parts.index("score") + 2
                analysis["depth"] = int(parts[depth_index])
                analysis["score"] = int(parts[score_index])
            if "bestmove" in output:
                break
        return analysis
    
    def set_difficulty(self, skill_level: int) -> None:
        """adjusts the engine's difficulty level."""
        self.difficulty = skill_level
        self.process.stdin.write(f"setoption name Skill Level value {skill_level}\n")
        self.process.stdin.flush()