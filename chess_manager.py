import chess
import chess.svg
import chess.engine
import json
import os
import sys
import random

# Configuration
STATE_FILE = "chess_state.json"
BOARD_SVG = "chess_board.svg"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")
ISSUE_TITLE = os.environ.get("ISSUE_TITLE")
ISSUE_USER = os.environ.get("ISSUE_USER")
REPO_OWNER = "SagheerAkram" # Hardcoded for simplicity, or os.environ['GITHUB_REPOSITORY'].split('/')[0]

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

def comment_on_issue(body):
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        print("Skipping issue comment (local run)")
        return
        
    import requests
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_OWNER}/issues/{ISSUE_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    requests.post(url, json={"body": body}, headers=headers)

def close_issue():
    if not GITHUB_TOKEN or not ISSUE_NUMBER:
        return
    import requests
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_OWNER}/issues/{ISSUE_NUMBER}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    requests.patch(url, json={"state": "closed"}, headers=headers)

def get_ai_move(board):
    # Simple random move for now, or basic capture logic
    # In future: import chess.engine and use Stockfish if available
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    return random.choice(legal_moves)

def main():
    if not ISSUE_TITLE or not ISSUE_TITLE.startswith("Chess Move:"):
        print("Not a chess move issue.")
        return

    # 1. Parse Move
    # Title format: "Chess Move: e2e4"
    try:
        user_move_uci = ISSUE_TITLE.split(":")[1].strip()
    except:
        comment_on_issue("Invalid move format. Please use 'Chess Move: e2e4'.")
        close_issue()
        return

    # 2. Load State
    state = load_state()
    board = chess.Board(state["fen"])

    # 3. Apply User Move
    try:
        move = chess.Move.from_uci(user_move_uci)
        if move in board.legal_moves:
            board.push(move)
            state["history"].append(user_move_uci)
        else:
            comment_on_issue(f"Illegal move: {user_move_uci}. Please try again.")
            close_issue()
            return
    except:
        comment_on_issue(f"Invalid move UCI: {user_move_uci}.")
        close_issue()
        return

    # 4. Check Game Over
    game_over_msg = ""
    if board.is_game_over():
        game_over_msg = f"\n\n**Game Over!** Result: {board.result()}"
        # Reset? Maybe not yet.

    # 5. AI Move
    if not board.is_game_over():
        ai_move = get_ai_move(board)
        if ai_move:
            board.push(ai_move)
            state["history"].append(ai_move.uci())
            state["last_move"] = ai_move.uci()
            
            if board.is_game_over():
                game_over_msg = f"\n\n**Game Over!** Result: {board.result()}"
        else:
             game_over_msg = "\n\n**Game Over!** No legal moves."

    # 6. Save State and SVG
    state["fen"] = board.fen()
    save_state(state)
    generate_svg(state["fen"], state.get("last_move"))

    # 7. Reply
    board_img_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_OWNER}/main/chess_board.svg?token={random.randint(0,10000)}" # Cache bust
    reply = f"Move processed! {user_move_uci} -> AI plays {state.get('last_move')}.\n\n![Current Board]({board_img_url})\n{game_over_msg}\n\n[Make another move](https://{REPO_OWNER}.github.io/{REPO_OWNER}/chess/)"
    
    comment_on_issue(reply)
    close_issue()

if __name__ == "__main__":
    # If running locally without issue context, just generate SVG
    if not ISSUE_TITLE:
        state = load_state()
        generate_svg(state["fen"])
    else:
        main()
