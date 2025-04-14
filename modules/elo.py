"""
this tracks player and ai ratings:
- adjusts difficulty dynamically
- processes game outcomes
- visualizes rating trends
"""
import math
from typing import Tuple, Dict, List, Optional
import json
import os

class ELOManager:
    def __init__(self, player_elo: int = 1200, ai_elo: int = 1200, save_file: str = "ratings.json") -> None:
        """
        sets up the elo manager with initial ratings and a save file.
        """
        self.player_elo = player_elo
        self.ai_elo = ai_elo
        self.save_file = save_file
        self.k_factor = 32  # Standard K-factor for rating calculations
        self.history: List[Dict] = []
        
        # Load saved ratings if available
        self.load_ratings()
    
    def update_ratings(self, outcome: str) -> Tuple[int, int]:
        """
        updates player and ai ratings based on the game result.
        """
        # Convert outcome to score (1.0 for win, 0.5 for draw, 0.0 for loss)
        player_score = 1.0 if outcome == "win" else (0.5 if outcome == "draw" else 0.0)
        ai_score = 1.0 - player_score  # AI score is opposite of player score
        
        # Calculate expected scores
        expected_player = self._get_expected_score(self.player_elo, self.ai_elo)
        expected_ai = 1.0 - expected_player
        
        # Calculate rating changes
        player_change = int(round(self.k_factor * (player_score - expected_player)))
        ai_change = int(round(self.k_factor * (ai_score - expected_ai)))
        
        # Update ratings
        self.player_elo += player_change
        self.ai_elo += ai_change
        
        # Ensure ratings don't go below a minimum value
        self.player_elo = max(100, self.player_elo)
        self.ai_elo = max(800, self.ai_elo)
        
        # Record the game outcome and rating changes
        self._record_game(outcome, player_change, ai_change)
        
        # Save updated ratings
        self.save_ratings()
        
        return (player_change, ai_change)
    
    def _get_expected_score(self, rating_a: int, rating_b: int) -> float:
        """
        calculates the expected score for a player using the elo formula.
        """
        return 1.0 / (1.0 + pow(10, (rating_b - rating_a) / 400.0))
    
    def get_suggested_ai_level(self) -> int:
        """
        suggests an ai level based on the player's current elo.
        """
        # Map player ELO to AI skill level (approximation)
        # This mapping is designed so that:
        # - Players around 800-1000 ELO face an AI with skill level 0-5
        # - Players around 1200-1400 ELO face an AI with skill level 6-12
        # - Players around 1600-2000 ELO face an AI with skill level 13-20
        
        # Ensure player_elo is within reasonable bounds
        bounded_elo = max(800, min(2000, self.player_elo))
        
        # Linear mapping from ELO 800-2000 to skill level 0-20
        skill_level = int((bounded_elo - 800) * 20 / 1200)
        
        # Ensure we stay within valid range
        return max(0, min(20, skill_level))
    
    def set_player_elo(self, elo: int) -> None:
        """
        updates the player's elo rating and saves it.
        """
        self.player_elo = max(100, elo)
        self.save_ratings()
    
    def set_ai_elo(self, elo: int) -> None:
        """
        updates the ai's elo rating and saves it.
        """
        self.ai_elo = max(800, elo)
        self.save_ratings()
    
    def _record_game(self, outcome: str, player_change: int, ai_change: int) -> None:
        """
        logs the game result and rating changes in the history.
        """
        self.history.append({
            "outcome": outcome,
            "player_elo": self.player_elo,
            "ai_elo": self.ai_elo,
            "player_change": player_change,
            "ai_change": ai_change
        })
        
        # Keep history limited to recent games
        if len(self.history) > 50:
            self.history = self.history[-50:]
    
    def get_win_loss_ratio(self) -> Tuple[int, int, int]:
        """
        calculates the player's win/loss/draw counts from the history.
        """
        wins = sum(1 for game in self.history if game["outcome"] == "win")
        losses = sum(1 for game in self.history if game["outcome"] == "loss")
        draws = sum(1 for game in self.history if game["outcome"] == "draw")
        
        return (wins, losses, draws)
    
    def get_performance_trend(self) -> List[int]:
        """
        gets the player's rating trend over the last 10 games.
        """
        if not self.history:
            return [self.player_elo]
            
        # Get last 10 entries
        recent = self.history[-10:]
        
        # Extract player ELO for each game
        return [game["player_elo"] for game in recent]
    
    def save_ratings(self) -> None:
        """
        saves the current ratings and history to a file.
        """
        try:
            data = {
                "player_elo": self.player_elo,
                "ai_elo": self.ai_elo,
                "history": self.history
            }
            
            with open(self.save_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Could not save ratings: {e}")
    
    def load_ratings(self) -> bool:
        """
        loads ratings and history from a file if it exists.
        """
        if not os.path.exists(self.save_file):
            return False
            
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
                
            self.player_elo = data.get("player_elo", self.player_elo)
            self.ai_elo = data.get("ai_elo", self.ai_elo)
            self.history = data.get("history", [])
            return True
        except Exception as e:
            print(f"Could not load ratings: {e}")
            return False