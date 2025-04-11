"""
Chess multiplayer server launcher
Starts the WebSocket server for online multiplayer functionality
"""
import asyncio
import sys
import os
from server.chess_server import ChessServer

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("  Chess AI - Online Multiplayer Server")
    print("=" * 60)
    print("This server handles matchmaking and game state synchronization")
    print("for online multiplayer chess games.")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 60)

async def main():
    """Start the chess server"""
    print_banner()
    
    # Default host and port
    host = "localhost"
    port = 8765
    
    # Check command line arguments for custom host/port
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port number: {sys.argv[2]}")
            sys.exit(1)
    
    print(f"Starting server on {host}:{port}")
    
    # Create and start the server
    server = ChessServer(host, port)
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)
