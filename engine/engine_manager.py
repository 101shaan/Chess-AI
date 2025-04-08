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
import random
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
            return None
        
        # Set the engine difficulty
        self.set_difficulty(difficulty)
        
        # For very low difficulties (0-4), use a more realistic "beginner" approach
        if difficulty < 5:
            return self._get_beginner_move(board, difficulty)
        
        # For normal difficulties, get the best move from the engine directly
        try:
            result = self.engine.play(
                board,
                chess.engine.Limit(time=self._get_time_limit(difficulty)),
                ponder=False
            )
            self._calculated_move = result.move
            return result.move
        except Exception as e:
            print(f"Error getting move: {e}")
            return None
        
    def _get_beginner_move(self, board: chess.Board, difficulty: int) -> Optional[chess.Move]:
        """
        Get a move that simulates a beginner player at the specified difficulty
        
        Args:
            board: Current chess position
            difficulty: Skill level (0-4)
        
        Returns:
            A move chosen to simulate beginner play
        """
        try:
            # For extreme beginner level (level 0), sometimes make very poor moves
            if difficulty == 0 and random.random() < 0.3:
                # Choose a random legal move to simulate a very poor player occasionally
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    random_move = random.choice(legal_moves)
                    self._calculated_move = random_move
                    return random_move
            
            # Get multiple candidate moves with evaluations using MultiPV
            # Use more candidates for lower difficulties to include worse moves
            multipv = max(3, 10 - difficulty * 2)  # 10 for diff 0, 8 for diff 1, etc.
            
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(time=0.5),  # Reduce thinking time for beginner AI
                multipv=multipv
            )
            
            # No legal moves available
            if not info or not len(info):
                return None
            
            # Convert difficulty to a probability of making a mistake
            # Much higher probability of mistakes at lower levels
            mistake_probability = min(0.95, 0.95 - (difficulty * 0.15))  # 0.95 at level 0, 0.8 at level 1, etc.
            
            # Decide whether to make a deliberate mistake
            if random.random() < mistake_probability:
                # Choose a sub-optimal move, but not totally random
                if len(info) > 1:
                    # Get exponentially weighted indices favoring much worse moves at lower difficulties
                    # This creates a more dramatic skill difference between levels
                    num_options = len(info)
                    
                    if difficulty == 0:
                        # At lowest difficulty, strongly favor bad moves
                        weights = [0.5, 0.25, 0.15, 0.05, 0.03, 0.01, 0.01][:num_options]
                        if num_options > len(weights):
                            weights.extend([0.001] * (num_options - len(weights)))
                    elif difficulty == 1:
                        # Slightly better but still bad
                        weights = [0.3, 0.3, 0.2, 0.1, 0.05, 0.03, 0.02][:num_options]
                        if num_options > len(weights):
                            weights.extend([0.01] * (num_options - len(weights)))
                    else:
                        # Basic weighting for higher beginner levels
                        weights = [0.1] * num_options
                        for i in range(num_options):
                            weights[i] = 0.5 / (i + 1)
                    
                    # Normalize weights
                    total = sum(weights)
                    weights = [w/total for w in weights]
                    
                    # Choose a move based on weights (higher weights for worse moves)
                    move_index = random.choices(range(num_options), weights=weights, k=1)[0]
                    
                    # For lowest difficulty, occasionally pick from the bottom of the list
                    if difficulty == 0 and random.random() < 0.4 and num_options > 3:
                        move_index = random.randint(num_options // 2, num_options - 1)
                    
                    chosen_move = info[move_index]["pv"][0]
                else:
                    # Only one candidate move available
                    chosen_move = info[0]["pv"][0]
            else:
                # Play the best move (rarely at low difficulty)
                chosen_move = info[0]["pv"][0]
                
            self._calculated_move = chosen_move
            return chosen_move
                
        except Exception as e:
            print(f"Error getting beginner move: {e}")
            # Fall back to a random legal move for very low difficulty
            if difficulty < 2:
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    random_move = random.choice(legal_moves)
                    self._calculated_move = random_move
                    return random_move
            
            # Otherwise fall back to a normal engine move with lowest skill level
            try:
                result = self.engine.play(
                    board,
                    chess.engine.Limit(time=0.1),
                    ponder=False
                )
                self._calculated_move = result.move
                return result.move
            except Exception as e2:
                print(f"Error getting fallback move: {e2}")
                return None

    def is_move_ready(self) -> bool:
        """
        Check if the engine has finished calculating a move
        
        Returns:
            True if a move is ready, False otherwise
        """
        if hasattr(self, '_calculated_move') and self._calculated_move:
            return True
        return False

    def get_calculated_move(self) -> Optional[chess.Move]:
        """
        Get the calculated move once it's ready
        
        Returns:
            The best move or None if not ready
        """
        if hasattr(self, '_calculated_move') and self._calculated_move:
            try:
                # PlayResult already contains the move directly
                move = self._calculated_move
                # Reset _calculated_move after retrieving the move
                self._calculated_move = None
                return move
            except Exception as e:
                print(f"Error retrieving calculated move: {e}")
                self._calculated_move = None
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
        
        # Configure engine options
        try:
            # For very low skill levels (0-4), use Skill Level without ELO restriction
            if skill_level < 5:
                # Set to minimum skill level and disable UCI_LimitStrength to get more random moves
                engine_skill = max(0, skill_level)  # Ensure non-negative
                self.engine.configure({
                    'Skill Level': engine_skill,
                    'UCI_LimitStrength': False
                })
                print(f"Set engine to beginner level (Skill Level: {engine_skill})")
            else:
                # For skill level 5+, use ELO rating with UCI_LimitStrength
                # Stockfish has a minimum ELO of around 1320
                elo_rating = 1320 + ((skill_level - 5) * 75)
                self.engine.configure({
                    'Skill Level': skill_level,
                    'UCI_LimitStrength': True,
                    'UCI_Elo': elo_rating
                })
                print(f"Set engine to intermediate/advanced (ELO: {elo_rating})")
        except chess.engine.EngineError as e:
            print(f"Warning: Could not set difficulty to {skill_level}: {e}")

    def _get_time_limit(self, difficulty: int) -> float:
        """
        Calculate the time limit for the engine based on difficulty
        
        Args:
            difficulty: Skill level (0-20)
        
        Returns:
            Time limit in seconds
        """
        # Calculate appropriate time limit based on difficulty
        # Higher difficulty gets more time to think
        base_time = 0.1  # Base time in seconds
        time_per_level = 0.05  # Additional time per skill level
        time_limit = base_time + (difficulty * time_per_level)
        
        # Limit for very fast moves in simple positions
        min_time = 0.1
        
        return max(min_time, time_limit)