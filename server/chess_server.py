"""
Chess game server for online multiplayer functionality.
Handles WebSocket connections, matchmaking, and game state synchronization.
"""
import asyncio
import json
import uuid
import random
import chess
from typing import Dict, List, Set, Optional, Any
import websockets
from websockets.legacy.server import WebSocketServerProtocol  # Updated import

# Game states
WAITING_FOR_OPPONENT = "waiting_for_opponent"
GAME_IN_PROGRESS = "game_in_progress"
GAME_OVER = "game_over"

class Player:
    """Player representation in the server"""
    def __init__(self, websocket: WebSocketServerProtocol, player_id: str):
        self.websocket = websocket
        self.player_id = player_id
        self.game_id: Optional[str] = None
        self.ready = False
        self.name = f"Player_{player_id[:6]}"  # Default name
        self.color: Optional[chess.Color] = None

class Game:
    """Game representation in the server"""
    def __init__(self, game_id: str, white_player: Player, black_player: Player):
        self.game_id = game_id
        self.white_player = white_player
        self.black_player = black_player
        self.board = chess.Board()
        self.state = GAME_IN_PROGRESS
        self.chat_history: List[Dict[str, str]] = []
        self.last_move: Optional[str] = None
        self.turn_start_time = asyncio.get_event_loop().time()
        self.white_time = None  # Placeholder for white's remaining time
        self.black_time = None  # Placeholder for black's remaining time

    def deduct_time(self):
        """Deduct time from the current player's clock (placeholder)"""
        # Future implementation: Deduct time based on elapsed time since last move
        pass

    def is_time_up(self) -> Optional[str]:
        """Check if either player's time has run out (placeholder)"""
        # Future implementation: Return "white" or "black" if time is up, else None
        return None

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        if self.white_player.player_id == player_id:
            return self.white_player
        elif self.black_player.player_id == player_id:
            return self.black_player
        return None
        
    def get_opponent(self, player_id: str) -> Optional[Player]:
        """Get opponent of a player"""
        if self.white_player.player_id == player_id:
            return self.black_player
        elif self.black_player.player_id == player_id:
            return self.white_player
        return None
    
    def is_player_turn(self, player_id: str) -> bool:
        """Check if it's the player's turn"""
        is_white_turn = self.board.turn == chess.WHITE
        return (is_white_turn and self.white_player.player_id == player_id) or \
               (not is_white_turn and self.black_player.player_id == player_id)

    def get_game_state(self, for_player_id: str) -> Dict[str, Any]:
        """Get current game state"""
        player = self.get_player_by_id(for_player_id)
        opponent = self.get_opponent(for_player_id)
        
        if not player or not opponent:
            return {"error": "Player not found in game"}
        
        return {
            "game_id": self.game_id,
            "board_fen": self.board.fen(),
            "your_color": "white" if player.color == chess.WHITE else "black",
            "your_turn": self.is_player_turn(for_player_id),
            "opponent_name": opponent.name,
            "state": self.state,
            "last_move": self.last_move,
            "legal_moves": [move.uci() for move in self.board.legal_moves],
            "chat_history": self.chat_history[-10:],  # Return last 10 messages
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_insufficient_material": self.board.is_insufficient_material(),
            "is_game_over": self.board.is_game_over(),
            "white_time": self.white_time,  # Placeholder for white's remaining time
            "black_time": self.black_time   # Placeholder for black's remaining time
        }

class ChessServer:
    """Chess server managing WebSocket connections and games"""
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.players: Dict[str, Player] = {}  # player_id -> Player
        self.games: Dict[str, Game] = {}  # game_id -> Game
        self.waiting_players: Set[str] = set()  # Set of player_ids waiting for a match
        self.server = None  # Store server instance for shutdown
        
    async def start(self):
        """Start the WebSocket server"""
        print(f"Starting Chess Server on {self.host}:{self.port}")
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=30,  # Send pings every 30 seconds
            ping_timeout=60    # Allow 60 seconds for a pong response
        )
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            print("Shutting down Chess Server...")
        finally:
            self.server.close()
            await self.server.wait_closed()
    
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket connection"""
        player_id = None  # Initialize player_id to avoid UnboundLocalError
        try:
            # Retrieve headers using the correct method
            headers = websocket.request_headers if hasattr(websocket, "request_headers") else {}
            player_id = headers.get("Player-ID")  # Check for existing player ID
            
            if player_id and player_id in self.players:
                # Reconnecting player
                player = self.players[player_id]
                player.websocket = websocket
                await self.send_message(websocket, {
                    "type": "reconnected",
                    "player_id": player_id,
                    "game_state": self.games[player.game_id].get_game_state(player_id) if player.game_id else None
                })
            else:
                # New player
                player_id = str(uuid.uuid4())
                player = Player(websocket, player_id)
                self.players[player_id] = player
                await self.send_message(websocket, {
                    "type": "connection_established",
                    "player_id": player_id
                })
            
            try:
                async for message in websocket:
                    await self.process_message(player, message)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed with error: {e}")
            except Exception as e:
                print(f"Unexpected error while processing messages: {e}")
        except Exception as e:
            print(f"Error during connection handling: {e}")
        finally:
            print("Closing connection with client...")
            # Ensure the WebSocket connection is closed properly
            await websocket.close()
            if player_id and player_id in self.players:
                await self.handle_disconnect(self.players[player_id])
    
    async def process_message(self, player: Player, message: str):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "find_game":
                await self.handle_find_game(player, data)
            elif message_type == "make_move":
                await self.handle_make_move(player, data)
            elif message_type == "chat_message":
                await self.handle_chat_message(player, data)
            elif message_type == "update_name":
                await self.handle_update_name(player, data)
            elif message_type == "resign":
                await self.handle_resign(player)
            elif message_type == "request_game_state":
                await self.handle_request_game_state(player)
        except json.JSONDecodeError:
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Invalid JSON message"
            })
    
    async def handle_find_game(self, player: Player, data: Dict[str, Any]):
        """Handle request to find a game"""
        # Remove from waiting list if already there
        if player.player_id in self.waiting_players:
            self.waiting_players.remove(player.player_id)
        
        # Leave current game if in one
        if player.game_id and player.game_id in self.games:
            await self.handle_resign(player)
        
        # Add player to waiting list
        self.waiting_players.add(player.player_id)
        
        # Update player name if provided
        if "player_name" in data:
            player.name = data["player_name"][:20]  # Limit name length
        
        await self.send_message(player.websocket, {
            "type": "matchmaking", 
            "status": WAITING_FOR_OPPONENT
        })
        
        # Try to match with another player
        await self.try_matchmaking()
    
    async def try_matchmaking(self):
        """Try to match waiting players"""
        if len(self.waiting_players) >= 2:
            # Get two players from the waiting list
            player1_id = self.waiting_players.pop()
            player2_id = self.waiting_players.pop()
            
            player1 = self.players[player1_id]
            player2 = self.players[player2_id]
            
            # Create a new game
            game_id = str(uuid.uuid4())
            
            # Randomly assign colors
            if random.choice([True, False]):
                white_player, black_player = player1, player2
            else:
                white_player, black_player = player2, player1
            
            white_player.color = chess.WHITE
            black_player.color = chess.BLACK
            
            game = Game(game_id, white_player, black_player)
            self.games[game_id] = game
            
            # Update player's game_id
            white_player.game_id = game_id
            black_player.game_id = game_id
            
            # Notify players about the game
            for player in [white_player, black_player]:
                opponent = game.get_opponent(player.player_id)
                await self.send_message(player.websocket, {
                    "type": "game_start",
                    "game_id": game_id,
                    "your_color": "white" if player.color == chess.WHITE else "black",
                    "opponent_name": opponent.name if opponent else "Unknown",
                    "game_state": game.get_game_state(player.player_id)
                })
    
    async def handle_make_move(self, player: Player, data: Dict[str, Any]):
        """Handle player's move"""
        game_id = player.game_id
        if not game_id or game_id not in self.games:
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Not in a game"
            })
            return
            
        game = self.games[game_id]

        # Placeholder: Deduct time from the current player's clock
        game.deduct_time()

        # Placeholder: Check if time is up
        time_up = game.is_time_up()
        if time_up:
            game.state = GAME_OVER
            result = "1-0" if time_up == "white" else "0-1"
            reason = "time out"
            for player_id in [game.white_player.player_id, game.black_player.player_id]:
                player = game.get_player_by_id(player_id)
                if player:
                    await self.send_message(player.websocket, {
                        "type": "game_over",
                        "result": result,
                        "reason": reason,
                        "game_state": game.get_game_state(player_id)
                    })
            return

        # Check if it's the player's turn
        if not game.is_player_turn(player.player_id):
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Not your turn"
            })
            return
        
        # Parse the move
        move_uci = data.get("move")
        if not move_uci:
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Move not specified"
            })
            return
            
        try:
            move = chess.Move.from_uci(move_uci)
            if move not in game.board.legal_moves:
                await self.send_message(player.websocket, {
                    "type": "error", 
                    "message": "Illegal move"
                })
                return
                
            # Make the move
            game.board.push(move)
            game.last_move = move_uci
            game.turn_start_time = asyncio.get_event_loop().time()
            
            # Check if game is over
            if game.board.is_game_over():
                game.state = GAME_OVER
                
                # Determine result
                result = "1-0" if game.board.is_checkmate() and not game.board.turn else "0-1" if game.board.is_checkmate() else "1/2-1/2"
                
                # Send game over notification to both players
                for player_id in [game.white_player.player_id, game.black_player.player_id]:
                    player = game.get_player_by_id(player_id)
                    if player:
                        await self.send_message(player.websocket, {
                            "type": "game_over",
                            "result": result,
                            "reason": self.get_game_over_reason(game.board),
                            "game_state": game.get_game_state(player_id)
                        })
            else:
                # Send updated game state to both players
                for player_id in [game.white_player.player_id, game.black_player.player_id]:
                    player = game.get_player_by_id(player_id)
                    if player:
                        await self.send_message(player.websocket, {
                            "type": "move_made",
                            "move": move_uci,
                            "by_player": game.get_opponent(player_id).name if game.get_opponent(player_id) else "Opponent",
                            "game_state": game.get_game_state(player_id)
                        })
                        
        except ValueError:
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Invalid move format"
            })
        except Exception as e:
            print(f"Unexpected error while processing move: {e}")
            await self.send_message(player.websocket, {
                "type": "error",
                "message": "An unexpected error occurred while processing your move."
            })
            
    def get_game_over_reason(self, board: chess.Board) -> str:
        """Get human-readable reason for game end"""
        if board.is_checkmate():
            return "checkmate"
        elif board.is_stalemate():
            return "stalemate"
        elif board.is_insufficient_material():
            return "insufficient material"
        elif board.is_fivefold_repetition():
            return "fivefold repetition"
        elif board.is_seventyfive_moves():
            return "seventyfive moves rule"
        return "game over"
        
    async def handle_chat_message(self, player: Player, data: Dict[str, Any]):
        """Handle chat message"""
        game_id = player.game_id
        if not game_id or game_id not in self.games:
            return
            
        game = self.games[game_id]
        message_text = data.get("message", "").strip()
        
        if not message_text or len(message_text) > 200:  # Limit message length
            return
            
        chat_message = {
            "sender": player.name,
            "message": message_text,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Add to chat history
        game.chat_history.append(chat_message)
        
        # Send to both players
        for player_id in [game.white_player.player_id, game.black_player.player_id]:
            recv_player = game.get_player_by_id(player_id)
            if recv_player:
                await self.send_message(recv_player.websocket, {
                    "type": "chat_message",
                    "message": chat_message
                })
    
    async def handle_update_name(self, player: Player, data: Dict[str, Any]):
        """Handle player name update"""
        new_name = data.get("name", "").strip()
        if not new_name or len(new_name) > 20:  # Validate name
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Invalid name"
            })
            return
            
        player.name = new_name
        
        # If player is in a game, notify opponent of name change
        if player.game_id and player.game_id in self.games:
            game = self.games[player.game_id]
            opponent = game.get_opponent(player.player_id)
            if opponent:
                await self.send_message(opponent.websocket, {
                    "type": "opponent_update",
                    "name": player.name
                })
                
        await self.send_message(player.websocket, {
            "type": "name_updated", 
            "name": player.name
        })
    
    async def handle_resign(self, player: Player):
        """Handle player resignation"""
        try:
            game_id = player.game_id
            if not game_id or game_id not in self.games:
                return

            game = self.games[game_id]
            opponent = game.get_opponent(player.player_id)

            game.state = GAME_OVER

            # Notify opponent of resignation
            if opponent:
                await self.send_message(opponent.websocket, {
                    "type": "opponent_resigned",
                    "opponent_name": player.name
                })

            # Clean up game
            del self.games[game_id]

            # Reset players
            for p in [game.white_player, game.black_player]:
                if p and p.player_id in self.players:
                    p.game_id = None
                    p.color = None
        except KeyError as e:
            print(f"Error during resignation cleanup: {e}")
        except Exception as e:
            print(f"Unexpected error during resignation: {e}")
    
    async def handle_request_game_state(self, player: Player):
        """Send current game state to player"""
        game_id = player.game_id
        if not game_id or game_id not in self.games:
            await self.send_message(player.websocket, {
                "type": "error", 
                "message": "Not in a game"
            })
            return
            
        game = self.games[game_id]
        await self.send_message(player.websocket, {
            "type": "game_state",
            "game_state": game.get_game_state(player.player_id)
        })
        
    async def handle_disconnect(self, player: Player):
        """Handle player disconnection"""
        try:
            # Remove from waiting players if there
            if player.player_id in self.waiting_players:
                self.waiting_players.remove(player.player_id)

            # If in a game, handle as resignation
            if player.game_id:
                await self.handle_resign(player)

            # Remove player
            if player.player_id in self.players:
                del self.players[player.player_id]
        except KeyError as e:
            print(f"Error during disconnect cleanup: {e}")
        except Exception as e:
            print(f"Unexpected error during disconnect: {e}")
            
    async def send_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Send message to WebSocket client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosedError:
            print("Failed to send message: Connection closed.")
        except Exception as e:
            print(f"Unexpected error while sending message: {e}")

async def main():
    """Run the Chess server"""
    server = ChessServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nServer interrupted by user. Exiting...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        print("Server shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer terminated.")
