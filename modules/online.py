"""
WebSocket client module for online multiplayer chess.
Handles connection to server, matchmaking, and game synchronization.
"""
import asyncio
import json
import websockets
import chess
import threading
from typing import Dict, List, Optional, Any, Callable
from queue import Queue
import time

class ChessClient:
    """WebSocket client for chess multiplayer"""
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.player_id = None
        self.game_id = None
        self.player_color = None
        self.opponent_name = "Opponent"
        self.game_state = None
        self.chat_history = []
        self.message_queue = Queue()  # Queue for messages to send
        self.event_handlers = {
            "connection_established": [],
            "matchmaking": [],
            "game_start": [],
            "move_made": [],
            "game_over": [],
            "opponent_resigned": [],
            "chat_message": [],
            "game_state": [],
            "error": [],
            "opponent_update": [],
            "name_updated": [],
            "game_ended": []
        }
        self.connection_thread = None
        self.is_running = False
    
    def connect(self, player_name: str = "Player"):
        """Start connection in a separate thread"""
        if self.connection_thread and self.is_running:
            return  # Already connected or connecting
        
        self.is_running = True
        self.connection_thread = threading.Thread(
            target=self._run_connection, 
            args=(player_name,)
        )
        self.connection_thread.daemon = True
        self.connection_thread.start()
    
    def _run_connection(self, player_name: str):
        """Run WebSocket connection (in thread)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._connect_and_process(player_name))
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.is_running = False
            loop.close()
    
    async def _connect_and_process(self, player_name: str):
        """Connect to WebSocket server and process messages"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                self.websocket = websocket
                self.connected = True
                self._trigger_event("connection_established", {"player_name": player_name})
                
                # Start sender task
                sender_task = asyncio.create_task(self._message_sender())
                
                # Process incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._process_message(data)
                    except json.JSONDecodeError:
                        print("Received invalid JSON message")
                
                # Cancel sender task when connection closes
                sender_task.cancel()
                
        except websockets.exceptions.ConnectionClosed:
            self._trigger_event("error", {"message": "Connection closed"})
        except Exception as e:
            self._trigger_event("error", {"message": f"Connection error: {e}"})
        finally:
            self.connected = False
            self.websocket = None
    
    async def _message_sender(self):
        """Task to send queued messages"""
        while True:
            try:
                if not self.message_queue.empty() and self.websocket:
                    message = self.message_queue.get()
                    await self.websocket.send(json.dumps(message))
                else:
                    await asyncio.sleep(0.1)  # Wait a bit before checking queue again
            except Exception as e:
                print(f"Error sending message: {e}")
                await asyncio.sleep(1)  # Back off on error
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message from server"""
        message_type = data.get("type")
        
        if message_type == "connection_established":
            self.player_id = data.get("player_id")
            
        elif message_type == "game_start":
            self.game_id = data.get("game_id")
            self.player_color = chess.WHITE if data.get("your_color") == "white" else chess.BLACK
            self.opponent_name = data.get("opponent_name", "Opponent")
            self.game_state = data.get("game_state")
            
        elif message_type == "move_made":
            self.game_state = data.get("game_state")
            
        elif message_type == "game_over":
            self.game_state = data.get("game_state")
            
        elif message_type == "chat_message":
            message = data.get("message")
            if message:
                self.chat_history.append(message)
                
        elif message_type == "game_state":
            self.game_state = data.get("game_state")
            
        elif message_type == "opponent_update":
            self.opponent_name = data.get("name", "Opponent")
            
        elif message_type == "game_ended":
            self.game_id = None
            self.player_color = None
            self.game_state = None
            self.chat_history = []
            
        # Trigger registered event handlers
        self._trigger_event(message_type, data)
    
    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered event handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Unregister event handler"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    def find_game(self, player_name: Optional[str] = None):
        """Send request to find a game"""
        if not self.connected:
            return
            
        message = {"type": "find_game"}
        if player_name:
            message["player_name"] = player_name
            
        self.message_queue.put(message)
    
    def make_move(self, move_uci: str):
        """Send move to server"""
        if not self.connected or not self.game_id:
            return
            
        self.message_queue.put({
            "type": "make_move",
            "move": move_uci
        })
    
    def send_chat_message(self, message: str):
        """Send chat message"""
        if not self.connected or not self.game_id:
            return
            
        self.message_queue.put({
            "type": "chat_message",
            "message": message
        })
    
    def update_player_name(self, name: str):
        """Update player name"""
        if not self.connected:
            return
            
        self.message_queue.put({
            "type": "update_name",
            "name": name
        })
    
    def resign_game(self):
        """Resign from current game"""
        if not self.connected or not self.game_id:
            return
            
        self.message_queue.put({
            "type": "resign"
        })
    
    def request_game_state(self):
        """Request current game state from server"""
        if not self.connected or not self.game_id:
            return
            
        self.message_queue.put({
            "type": "request_game_state"
        })
    
    def disconnect(self):
        """Close connection"""
        self.is_running = False
        if self.websocket:
            try:
                # This is a bit hacky but will force the connection to close
                # since the websocket is being used in another thread
                self.message_queue.put({"type": "close_connection"})
            except:
                pass
