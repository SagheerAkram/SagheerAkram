import chess
import chess.svg
import json
import os
import sys

# Configuration
STATE_FILE = "chess_state.json"
BOARD_SVG = "chess_board.svg"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "fen": chess.STARTING_FEN,
        "last_move": "Game Start",
        "turn": "white",
        "history": []
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def generate_svg(fen, last_move_uci=None):
    board = chess.Board(fen)
    
    # Highlight last move if exists
    last_move = None
    if last_move_uci:
        try:
            last_move = chess.Move.from_uci(last_move_uci)
        except:
            pass

    svg_data = chess.svg.board(
        board, 
        lastmove=last_move, 
        size=400,
        colors={"square light": "#f0d9b5", "square dark": "#b58863", "margin": "#212529", "coord": "#ffffff"}
    )
    
    with open(BOARD_SVG, "w") as f:
        f.write(svg_data)
    print(f"Generated {BOARD_SVG}")

def initialize():
    state = load_state()
    # Ensure FEN is valid
    try:
        chess.Board(state["fen"])
    except:
        state["fen"] = chess.STARTING_FEN
        
    generate_svg(state["fen"])
    save_state(state)
    print("Chess board initialized.")

if __name__ == "__main__":
    initialize()
