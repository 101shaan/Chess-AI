"""
this is the websocket client for multiplayer chess:
- connects to the server
- handles sending and receiving messages
- manages game state and chat
"""
import asyncio
import websockets
from typing import Dict, Any, Callable
import json

class ChessClient:
    def __init__(self, server_url: str = "ws://localhost:8765"):
        """sets up the client with the server url."""
        self.server_url = server_url
        self.event_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self.message_queue = asyncio.Queue()
        self.connection = None
    
    def connect(self, player_name: str = "Player"):
        """starts the connection in a separate thread."""
        asyncio.get_event_loop().run_until_complete(self._connect_and_process(player_name))
    
    def _run_connection(self, player_name: str):
        """runs the websocket connection in a thread."""
        asyncio.run(self._connect_and_process(player_name))
    
    async def _connect_and_process(self, player_name: str):
        """connects to the server and processes incoming messages."""
        async with websockets.connect(self.server_url) as websocket:
            self.connection = websocket
            await websocket.send(player_name)
            consumer_task = asyncio.create_task(self._message_consumer(websocket))
            sender_task = asyncio.create_task(self._message_sender())
            await asyncio.gather(consumer_task, sender_task)
    
    async def _message_sender(self):
        """sends queued messages to the server."""
        while True:
            message = await self.message_queue.get()
            await self.connection.send(message)
    
    async def _message_consumer(self, websocket):
        """receives messages from the server."""
        async for message in websocket:
            data = json.loads(message)
            await self._process_message(data)
    
    async def _process_message(self, data: Dict[str, Any]):
        """handles incoming messages from the server."""
        event_type = data.get("type")
        if event_type in self.event_handlers:
            handler = self.event_handlers[event_type]
            handler(data)
    
    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """triggers registered event handlers for specific message types."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type](data)
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """registers a handler for a specific event type."""
        self.event_handlers[event_type] = handler