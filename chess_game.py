import chess
import chess.svg
import chess.engine
import json
import os
import sys
import random

# Configuration
DATA_FILE = "chess_data.json"
BOARD_SVG = "chess_board.svg"
README_PATH = "README.md"

def load_game_state():
    if not os.path.exists(DATA_FILE):
        return {
            "fen": chess.STARTING_FEN,
            "last_move": "Game Start",
            "stats": {"community_wins": 0, "bot_wins": 0, "draws": 0}
        }
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_game_state(state):
    with open(DATA_FILE, "w") as f:
        json.dump(state, f, indent=2)

def update_readme(stats, last_move_text):
    if not os.path.exists(README_PATH):
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        data = f.read()

    # Stats Block
    stats_content = f"""<!-- CHESS_STATS_START -->
**Community Wins**: {stats['community_wins']} 🏆 | **Bot Wins**: {stats['bot_wins']} 🤖 | **Draws**: {stats['draws']} 🤝
*Last Move*: {last_move_text}
<!-- CHESS_STATS_END -->"""
    
    # Regex replacement
    pattern = r"<!-- CHESS_STATS_START -->.*?<!-- CHESS_STATS_END -->"
    if re.search(pattern, data, flags=re.DOTALL):
        data = re.sub(pattern, stats_content, data, flags=re.DOTALL)
    
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(data)

def play_turn(user_move_uci):
    state = load_game_state()
    board = chess.Board(state["fen"])
    
    # 1. Validate and Push User Move
    try:
        move = chess.Move.from_uci(user_move_uci)
        if move in board.legal_moves:
            board.push(move)
            state["last_move"] = f"Community played {user_move_uci}"
        else:
            print(f"Illegal move: {user_move_uci}")
            sys.exit(1)
    except ValueError:
        print(f"Invalid move format: {user_move_uci}")
        sys.exit(1)
        
    # Check Game Over after User Move
    game_over, result = check_game_over(board)
    if game_over:
        handle_game_over(state, result, board)
        return

    # 2. Bot Move (Random for now, or simple capture)
    # Simple Heuristic: Capture if possible, else random
    legal_moves = list(board.legal_moves)
    bot_move = None
    
    # Try to capture
    for move in legal_moves:
        if board.is_capture(move):
            bot_move = move
            break
            
    if not bot_move:
        bot_move = random.choice(legal_moves)
        
    board.push(bot_move)
    state["last_move"] = f"Bot played {bot_move.uci()} (in response to {user_move_uci})"
    
    # Check Game Over after Bot Move
    game_over, result = check_game_over(board)
    if game_over:
        handle_game_over(state, result, board)
        return

    # 3. Save State & Generate SVG
    state["fen"] = board.fen()
    save_game_state(state)
    generate_svg(board)
    update_readme(state["stats"], state["last_move"])
    print(f"Turn complete. {state['last_move']}")

def check_game_over(board):
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black" # If current turn is Black and is mated, White (Community) won
        return True, winner
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return True, "Draw"
    return False, None

def handle_game_over(state, result, board):
    if result == "White": # Community (assuming user plays white)
        state["stats"]["community_wins"] += 1
        msg = "Checkmate! Community Wins! 🎉"
    elif result == "Black":
        state["stats"]["bot_wins"] += 1
        msg = "Checkmate! Bot Wins! 🤖"
    else:
        state["stats"]["draws"] += 1
        msg = "Game Drawn! 🤝"
        
    state["last_move"] = msg
    state["fen"] = chess.STARTING_FEN # Reset board
    
    save_game_state(state)
    
    # Generate SVG of the final position before reset, or the new blank board?
    # Let's show the final position one last time? 
    # Actually, usually better to reset SVG to start so people can play again immediately.
    # But then they miss the victory screen.
    # Let's keep the final board SVG but reset the FEN in JSON for *next* move validation to start fresh.
    # BUT if we reset FEN in JSON, next run will load start FEN.
    # So we should generate SVG of the *finished* game now. 
    generate_svg(board) 
    
    update_readme(state["stats"], msg)
    print(f"Game Over: {msg}")

def generate_svg(board):
    boardsvg = chess.svg.board(board=board, size=400)
    with open(BOARD_SVG, "w") as f:
        f.write(boardsvg)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chess_game.py <uci_move>")
        sys.exit(1)
    
    import re # Import re here since it's used in update_readme
    
    # Simple input sanitization
    move = sys.argv[1].strip()
    play_turn(move)
