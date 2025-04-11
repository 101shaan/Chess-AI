import socket
import threading
import chess
import json

class ChessServer:
    def __init__(self, host='localhost', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)  # Allow two players to connect
        self.clients = []
        self.game_state = chess.Board()
        self.lock = threading.Lock()

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message)
            except Exception as e:
                print(f"Error sending message to client: {e}")

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                self.process_message(message, client_socket)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
        self.clients.remove(client_socket)
        client_socket.close()

    def process_message(self, message, client_socket):
        data = json.loads(message.decode('utf-8'))
        if data['action'] == 'move':
            move = chess.Move.from_uci(data['move'])
            with self.lock:
                if move in self.game_state.legal_moves:
                    self.game_state.push(move)
                    self.broadcast(message)
                else:
                    client_socket.send(json.dumps({'error': 'Invalid move'}).encode('utf-8'))

    def start(self):
        print("Server started. Waiting for players to connect...")
        while len(self.clients) < 2:
            client_socket, addr = self.server.accept()
            print(f"Player connected from {addr}")
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        print("Two players connected. Starting the game...")
        self.broadcast(json.dumps({'action': 'start', 'fen': self.game_state.fen()}).encode('utf-8'))

if __name__ == "__main__":
    server = ChessServer()
    server.start()