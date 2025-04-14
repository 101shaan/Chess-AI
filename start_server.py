"""
this launches the chess multiplayer server:
- starts the websocket server
- handles matchmaking and game state sync
"""
import asyncio
import sys
import os
from server.chess_server import ChessServer

def print_banner():
    """prints a welcome banner for the server"""
    print("=" * 60)
    print("  Chess AI - Online Multiplayer Server")
    print("=" * 60)
    print("this server handles matchmaking and game state synchronization")
    print("for online multiplayer chess games.")
    print("\npress ctrl+c to stop the server.")
    print("=" * 60)

async def main():
    """starts the chess server"""
    print_banner()
    
    # default host and port
    host = "localhost"
    port = 8765
    
    # check for custom host/port in command-line arguments
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"invalid port number: {sys.argv[2]}")
            sys.exit(1)
    
    print(f"starting server on {host}:{port}")
    
    # create and start the server
    server = ChessServer(host, port)
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)
