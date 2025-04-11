# Chess AI

## Overview
Chess AI is a chess game that allows players to compete against each other or against an AI. The game features a user-friendly interface, customizable themes, and sound effects to enhance the gaming experience. Additionally, it includes a multiplayer mode for online play.

## Features
- Single-player mode against an AI opponent
- Online multiplayer mode for playing against friends
- Customizable themes and sound effects
- Move history navigation
- Hint system for assistance
- Settings management for audio and visual preferences

## Project Structure
```
Chess-AI
├── src
│   ├── main.py                # Entry point of the game
│   ├── multiplayer             # Multiplayer functionality
│   │   ├── server.py          # Server-side logic
│   │   ├── client.py          # Client-side logic
│   │   └── utils.py           # Utility functions for multiplayer
│   ├── ui                     # User interface components
│   │   ├── menu.py            # Main menu UI
│   │   ├── game.py            # Game screen UI
│   │   └── settings.py        # Settings UI
│   ├── game                   # Game logic components
│   │   ├── board.py           # Chessboard logic
│   │   ├── engine.py          # Chess engine logic
│   │   └── rules.py           # Chess rules
│   └── assets                 # Game assets
│       ├── sounds             # Sound files
│       └── themes             # Theme files
├── requirements.txt           # Project dependencies
├── README.md                  # Project documentation
└── .gitignore                 # Files to ignore in version control
```

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Chess-AI.git
   ```
2. Navigate to the project directory:
   ```
   cd Chess-AI
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To start the game, run the following command:
```
python src/main.py
```

## Multiplayer Mode
To play online, you need to run the server and connect clients:
1. Start the server:
   ```
   python src/multiplayer/server.py
   ```
2. Connect clients by running:
   ```
   python src/multiplayer/client.py
   ```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.

## License
This project is licensed under the MIT License. See the LICENSE file for details.