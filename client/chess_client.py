import asyncio
import websockets
import json

async def connect_to_server():
    """Connect to the chess server and handle communication."""
    try:
        async with websockets.connect(
            "ws://localhost:8765",
            ping_interval=30,  # Send pings every 30 seconds
            ping_timeout=60    # Allow 60 seconds for a pong response
        ) as websocket:
            # Send a "find_game" message to start matchmaking
            await websocket.send(json.dumps({"type": "find_game", "player_name": "Player1"}))
            print("Connected to server and sent matchmaking request.")

            # Listen for messages from the server
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data}")

                # Handle different message types
                if data["type"] == "connection_established":
                    print(f"Connection established. Player ID: {data['player_id']}")
                elif data["type"] == "game_start":
                    print(f"Game started! You are {data['your_color']} against {data['opponent_name']}.")
                    print("Legal moves:", data["game_state"]["legal_moves"])
                elif data["type"] == "move_made":
                    print(f"Opponent moved: {data['move']}")
                    print("Updated board state:", data["game_state"]["board_fen"])
                    print(f"White time: {data['game_state'].get('white_time', 'N/A')} seconds")  # Placeholder
                    print(f"Black time: {data['game_state'].get('black_time', 'N/A')} seconds")  # Placeholder
                elif data["type"] == "game_over":
                    print(f"Game over! Result: {data['result']}, Reason: {data['reason']}")
                    break
                elif data["type"] == "error":
                    print(f"Error: {data['message']}")
                elif data["type"] == "opponent_resigned":
                    print(f"Your opponent, {data['opponent_name']}, has resigned. You win!")
                    break  # Exit the game loop

                # If it's the player's turn, prompt for a move
                if data.get("game_state") and data["game_state"]["your_turn"]:
                    print("Your turn! Legal moves:", data["game_state"]["legal_moves"])
                    print(f"Your remaining time: {data['game_state'].get('white_time' if data['game_state']['your_color'] == 'white' else 'black_time', 'N/A')} seconds")  # Placeholder
                    while True:
                        move = input("Enter your move (e.g., e2e4) or 'resign': ").strip()
                        if move in data["game_state"]["legal_moves"]:
                            await websocket.send(json.dumps({"type": "make_move", "move": move}))
                            break  # Exit the loop after sending a valid move
                        elif move.lower() == "resign":
                            await websocket.send(json.dumps({"type": "resign"}))
                            print("You have resigned the game.")
                            break
                        else:
                            print("Invalid move. Please try again.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Closing connection...")
        # Ensure the WebSocket connection is closed properly
        await websocket.close()

# Run the client
if __name__ == "__main__":
    try:
        asyncio.run(connect_to_server())
    except KeyboardInterrupt:
        print("\nClient interrupted by user. Exiting...")