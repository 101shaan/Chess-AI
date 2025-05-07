# Modern Chess AI Application

A complete chess application with an adaptive AI opponent, ELO rating system, and modern PyGame GUI.

## Features

- Modern, sleek interface with animations and visual effects
- Stockfish chess engine integration with adaptive difficulty
- ELO rating system that tracks player progress
- Multiple game modes (player vs AI, player vs player)
- Move history and captured pieces display
- Highlighted legal moves
- Sound effects for various game actions
- Game state detection (check, checkmate, stalemate)
- Animated piece movement

## Dependencies

- Python 3.8+
- PyGame
- python-chess
- Stockfish chess engine
- NumPy

## Installation

1. Clone this repository
2. Install required Python packages:
   ```
   pip install pygame python-chess numpy
   ```
3. Download and install Stockfish:
   - For Windows: Download from [Stockfish website](https://stockfishchess.org/download/)
   - Place the Stockfish executable in the `engine/` directory
   - Rename it to `stockfish.exe` (Windows) or `stockfish` (Linux/Mac)

## Project Structure

```
/chess_app
├── main.py                 # Main game loop and state management
├── config.py               # Settings and constants
├── README.md               # Project documentation
├── engine/
│   └── engine_manager.py   # Stockfish engine wrapper
├── modules/
│   ├── board.py            # Chess rules and state management
│   ├── ui.py               # Modern GUI implementation
│   ├── audio.py            # Sound effects manager
│   └── elo.py              # Rating system
└── assets/
    ├── pieces/             # Chess piece images
    ├── fonts/              # UI fonts
    └── sounds/             # Sound effects
```

## Usage

Run the game with:
```
python main.py
```


## Game Modes

1. **Player vs AI**: Play against the Stockfish chess engine with adaptive difficulty
2. **Local mutiplayer**: Play against another human on the same computer
3. **Practice Mode**: Play with move suggestions and hints

## Customization

Modify `config.py` to change:
- Window size and appearance
- Board colors and styles
- Sound effects volume
- Animation speed
- AI difficulty settings

## Asset Credits

- Chess pieces: Based on standard chess piece designs
- Sound effects: Custom created for this application

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Stockfish team for their excellent chess engine
- The python-chess library developers
- PyGame community for their documentation and examples
