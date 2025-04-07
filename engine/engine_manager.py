"""
Stockfish wrapper with adaptive difficulty
Required Features:
- Skill levels 0-20 (mapped to ELO 800-2000)
- Move time calculation based on difficulty
- Proper resource cleanup
"""
import chess
import chess.engine
import os
from typing import Dict, Any, Optional

class ChessEngine:
    def __init__(self, engine_path: str = None) -> None:
        """Initialize the chess engine"""
        self.engine = None
        self.engine_path = engine_path or os.path.join(
            os.path.dirname(__file__), 
            "stockfish.exe"
        )
        
    def init_engine(self) -> None:
        """Initialize and configure the Stockfish engine"""
        if not os.path.exists(self.engine_path):
            raise FileNotFoundError(
                f"Stockfish executable not found at {self.engine_path}.\n"
                f"Please download from https://stockfishchess.org/download/ and place in engine/ directory"
            )
            
        try:
            # Initialize engine
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Configure required options
            options = {
                'UCI_Elo': 1350,  # Set above minimum requirement
                'UCI_LimitStrength': True,
                'Skill Level': 10
            }
            
            # Apply configuration
            for option, value in options.items():
                try:
                    self.engine.configure({option: value})
                except chess.engine.EngineError as e:
                    print(f"Warning: Could not set {option}={value}: {e}")
            
            print(f"Engine initialized: {self.engine.id['name']}")
            return True
            
        except Exception as e:
            self.engine = None
            raise RuntimeError(
                f"Failed to initialize engine: {e}\n"
                f"Please ensure you have the latest Stockfish version from https://stockfishchess.org/download/"
            ) from e
    
    def close(self) -> None:
        """Close the engine"""
        if self.engine:
            self.engine.quit()
    
    def get_move(self, board: chess.Board, difficulty: int) -> Optional[chess.Move]:
        """
        Get the best move from the engine for the current position
        
        Args:
            board: Current chess position
            difficulty: Skill level (0-20)
        
        Returns:
            Best move according to the engine
        """
        if not self.engine:
            print("Engine not initialized")
            return None
        
        try:
            # Set the appropriate difficulty
            self.set_difficulty(difficulty)
            
            # Calculate appropriate time limit based on difficulty
            # Higher difficulty gets more time to think
            base_time = 0.1  # Base time in seconds
            time_per_level = 0.05  # Additional time per skill level
            time_limit = base_time + (difficulty * time_per_level)
            
            # Limit for very fast moves in simple positions
            min_time = 0.1
            
            # Non-blocking move calculation
            # This returns immediately and lets the engine calculate in the background
            self.current_result = self.engine.play(
                board,
                chess.engine.Limit(time=max(min_time, time_limit)),
                info=chess.engine.INFO_ALL
            )
            
            # Return None to indicate calculation is in progress
            return None
            
        except Exception as e:
            print(f"Error getting move from engine: {e}")
            return None

    def is_move_ready(self) -> bool:
        """
        Check if the engine has finished calculating a move
        
        Returns:
            True if a move is ready, False otherwise
        """
        if hasattr(self, 'current_result') and self.current_result:
            return True
        return False

    def get_calculated_move(self) -> Optional[chess.Move]:
        """
        Get the calculated move once it's ready
        
        Returns:
            The best move or None if not ready
        """
        if hasattr(self, 'current_result') and self.current_result:
            try:
                # PlayResult already contains the move directly
                move = self.current_result.move
                # Reset current_result after retrieving the move
                self.current_result = None
                return move
            except Exception as e:
                print(f"Error retrieving calculated move: {e}")
                self.current_result = None
        return None

    def analyze_position(self, board: chess.Board, depth: int = 15) -> Dict[str, Any]:
        """
        Analyze the current position at a deeper level for evaluation
        
        Args:
            board: Current chess board state
            depth: Search depth for analysis
            
        Returns:
            Dictionary with analysis results
        """
        # Configure engine for analysis (max strength)
        if "UCI_LimitStrength" in self.engine.options:
            self.engine.configure({"UCI_LimitStrength": False})
        
        # Run analysis
        analysis = self.engine.analyse(
            board, 
            chess.engine.Limit(depth=depth)
        )
        
        # Extract and return relevant information
        result = {
            "score": analysis["score"].white(),
            "depth": analysis["depth"],
            "nodes": analysis.get("nodes", 0),
            "time": analysis.get("time", 0)
        }
        
        return result
    
    def get_elo_from_skill(self, skill_level: int) -> int:
        """Convert skill level to approximate ELO rating"""
        skill_level = max(0, min(20, skill_level))
        return 800 + (skill_level * 60)  # Linear approximation

    def set_difficulty(self, skill_level: int) -> None:
        """
        Set the engine difficulty level
        
        Args:
            skill_level: Skill level (0-20)
        """
        if not self.engine:
            return
        
        # Ensure skill level is within valid range
        skill_level = max(0, min(20, skill_level))
        
        # Calculate ELO rating based on skill level
        # Stockfish has a minimum ELO of 1320, so we need to adjust our scale
        # For very low skill levels, we'll just set the skill level directly without ELO limit
        elo_rating = max(1320, 1320 + ((skill_level - 5) * 75))
        
        # Configure engine options
        try:
            # For very low skill levels (0-4), just use skill level without ELO restriction
            if skill_level < 5:
                self.engine.configure({
                    'Skill Level': skill_level,
                    'UCI_LimitStrength': False
                })
                print(f"Set engine skill level to {skill_level} (beginner mode)")
            else:
                # For skill level 5+, use ELO rating
                self.engine.configure({
                    'Skill Level': skill_level,
                    'UCI_LimitStrength': True,
                    'UCI_Elo': elo_rating
                })
                print(f"Set engine skill level to {skill_level} with ELO: {elo_rating}")
        except chess.engine.EngineError as e:
            print(f"Warning: Could not set difficulty to {skill_level}: {e}")