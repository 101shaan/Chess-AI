import socket
import threading
import json

class ChessClient:
    def __init__(self, server_address: str, server_port: int):
        self.server_address = server_address
        self.server_port = server_port
        self.socket = None
        self.username = None
        self.game_state = None

    def connect(self):
        """Connect to the multiplayer server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_address, self.server_port))
        print("Connected to the server.")

        # Start a thread to listen for messages from the server
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        """Listen for messages from the server."""
        while True:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if message:
                    self.handle_message(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def handle_message(self, message: str):
        """Handle incoming messages from the server."""
        data = json.loads(message)
        if data['type'] == 'game_update':
            self.game_state = data['state']
            self.update_game_ui()
        elif data['type'] == 'player_joined':
            print(f"{data['username']} has joined the game.")
        elif data['type'] == 'player_left':
            print(f"{data['username']} has left the game.")

    def send_move(self, move: str):
        """Send a move to the server."""
        message = json.dumps({'type': 'move', 'move': move})
        self.socket.sendall(message.encode('utf-8'))

    def update_game_ui(self):
        """Update the game UI based on the current game state."""
        # This method should be implemented to update the UI accordingly
        pass

    def close(self):
        """Close the connection to the server."""
        if self.socket:
            self.socket.close()
            print("Disconnected from the server.")

# Example usage:
# client = ChessClient('localhost', 12345)
# client.connect()