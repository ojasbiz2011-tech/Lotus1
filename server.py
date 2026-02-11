import os
import random
import string
import chess
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

# Configuration
app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'your_secret_key'

# SECURITY WARNING: Ideally, keep tokens in environment variables.
BOT_TOKEN = "8587196149:AAHUXp6ihV6lGrGdBiUkD2btujKHK1-I4dM"

# Initialize SocketIO (async_mode='eventlet' is recommended for production)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- In-Memory Storage ---
# Lobbies: { "lobby_id": [user_sid_1, user_sid_2, ...] }
lobbies = {}
# Users: { "sid": {"name": "User X", "lobby": "id", "game_id": None} }
users = {}
# Matchmaking Queue: [sid, sid, ...]
match_queue = []
# Active Games: { "game_id": {"board": chess.Board(), "white": sid, "black": sid} }
games = {}

MAX_LOBBY_SIZE = 128

@app.route('/')
def index():
    return render_template('index.html')

def generate_lobby_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@socketio.on('connect')
def on_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('join_app')
def handle_join_app(data):
    """User clicks Start. Auto-join a lobby."""
    user_name = data.get('username', f"Player {str(request.sid)[:4]}")
    
    # Find a lobby with space or create new
    target_lobby = None
    for lid, members in lobbies.items():
        if len(members) < MAX_LOBBY_SIZE:
            target_lobby = lid
            break
    
    if not target_lobby:
        target_lobby = generate_lobby_id()
        lobbies[target_lobby] = []

    # Join logic
    lobbies[target_lobby].append(request.sid)
    users[request.sid] = {"name": user_name, "lobby": target_lobby, "game_id": None}
    join_room(target_lobby)
    
    # Notify user and lobby
    emit('joined_lobby', {'lobby_id': target_lobby, 'users_count': len(lobbies[target_lobby])})
    emit('update_user_list', {'users': [users[uid]['name'] for uid in lobbies[target_lobby]]}, to=target_lobby)

@socketio.on('find_match')
def handle_find_match():
    """User clicks Play."""
    sid = request.sid
    if sid in match_queue:
        return # Already queuing
        
    match_queue.append(sid)
    emit('match_status', {'status': 'searching'})
    
    # Check if we can pair
    if len(match_queue) >= 2:
        player1 = match_queue.pop(0)
        player2 = match_queue.pop(0)
        
        # Create Game
        game_id = f"game_{player1}_{player2}"
        games[game_id] = {
            "board": chess.Board(),
            "white": player1,
            "black": player2
        }
        
        users[player1]['game_id'] = game_id
        users[player2]['game_id'] = game_id
        
        # Notify Players
        emit('game_start', {'game_id': game_id, 'color': 'white', 'opponent': users[player2]['name']}, room=player1)
        emit('game_start', {'game_id': game_id, 'color': 'black', 'opponent': users[player1]['name']}, room=player2)

@socketio.on('make_move')
def handle_move(data):
    """Handle chess move."""
    sid = request.sid
    game_id = users[sid].get('game_id')
    move_uci = data.get('move') # e.g., "e2e4"
    
    if not game_id or game_id not in games:
        return

    game = games[game_id]
    board = game['board']
    
    # specific turn check
    is_white = (game['white'] == sid)
    if (board.turn == chess.WHITE and not is_white) or (board.turn == chess.BLACK and is_white):
        return # Not your turn

    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            board.push(move)
            
            # Broadcast new FEN (board state) to both players
            fen = board.fen()
            opponent_sid = game['black'] if is_white else game['white']
            
            emit('move_made', {'fen': fen, 'turn': board.turn}, room=sid)
            emit('move_made', {'fen': fen, 'turn': board.turn}, room=opponent_sid)
            
            # Check Game Over
            if board.is_game_over():
                result = board.result()
                emit('game_over', {'result': result}, room=sid)
                emit('game_over', {'result': result}, room=opponent_sid)
                # Cleanup would go here
                
    except Exception as e:
        print(f"Invalid move attempt: {e}")

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in users:
        lobby_id = users[sid]['lobby']
        if lobby_id in lobbies and sid in lobbies[lobby_id]:
            lobbies[lobby_id].remove(sid)
            # Update lobby list
            user_names = [users[uid]['name'] for uid in lobbies[lobby_id]]
            emit('update_user_list', {'users': user_names}, to=lobby_id)
        
        if sid in match_queue:
            match_queue.remove(sid)
            
        del users[sid]
    print(f"Client disconnected: {sid}")

if __name__ == '__main__':
    # Use '0.0.0.0' for external access (e.g. Render)
    socketio.run(app, host='0.0.0.0', port=10000, allow_unsafe_werkzeug=True)
    
