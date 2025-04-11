def format_message(message_type: str, content: str) -> str:
    """Format a message for sending over the network."""
    return f"{message_type}:{content}"

def parse_message(message: str) -> tuple:
    """Parse a received message into its type and content."""
    try:
        message_type, content = message.split(":", 1)
        return message_type, content
    except ValueError:
        return None, message  # Return None type if parsing fails

def send_data(socket, data: str) -> None:
    """Send data over a socket connection."""
    try:
        socket.sendall(data.encode('utf-8'))
    except Exception as e:
        print(f"Error sending data: {e}")

def receive_data(socket) -> str:
    """Receive data from a socket connection."""
    try:
        data = socket.recv(1024).decode('utf-8')
        return data
    except Exception as e:
        print(f"Error receiving data: {e}")
        return ""  # Return empty string on error

def is_valid_move(move: str) -> bool:
    """Check if the move format is valid."""
    # Example validation: move should be in the format 'e2-e4'
    return len(move) == 5 and move[2] == '-' and move[:2].isalpha() and move[3:].isalpha()