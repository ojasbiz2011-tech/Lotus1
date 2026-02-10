import os
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumina_secret_key_change_this'

# Initialize SocketIO (Async mode for performance)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Telegram Config (As requested)
TELEGRAM_TOKEN = "8587196149:AAHUXp6ihV6lGrGdBiUkD2btujKHK1-I4dM"

# --- Global State (In-Memory for speed) ---
waiting_queue = []  # List of socket_ids waiting for a match
active_games = {}   # {game_id: {white: sid, black: sid, board: fen}}
players = {}        # {sid: {game_id: str, color: str}}

logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return "Lumina Chess Server is Running. Connect via WebSocket."

# --- WebSocket Events ---

@socketio.on('connect')
def on_connect():
    print(f"Player connected: {request.sid}")
    emit('server_stats', {'online': len(players) + 1})

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    print(f"Player disconnected: {sid}")

    # Remove from queue if waiting
    if sid in waiting_queue:
        waiting_queue.remove(sid)

    # Handle active game forfeit
    if sid in players:
        game_id = players[sid]['game_id']
        if game_id in active_games:
            game = active_games[game_id]
            opponent = game['black'] if game['white'] == sid else game['white']
            
            # Notify opponent
            if opponent:
                socketio.emit('opponent_left', room=opponent)
            
            # Clean up
            del active_games[game_id]
        del players[sid]

@socketio.on('find_match')
def find_match(data):
    sid = request.sid
    if sid in waiting_queue:
        return # Already waiting

    if len(waiting_queue) > 0:
        # Match Found!
        opponent_sid = waiting_queue.pop(0)
        game_id = f"game_{sid}_{opponent_sid}"
        
        # Store Game State
        active_games[game_id] = {
            'white': opponent_sid, 
            'black': sid,
            'fen': 'start' # Standard starting position
        }
        
        # Track Players
        players[opponent_sid] = {'game_id': game_id, 'color': 'white'}
        players[sid] = {'game_id': game_id, 'color': 'black'}

        # Notify Players
        socketio.emit('game_start', {'game_id': game_id, 'color': 'white', 'opponent': 'Anonymous'}, room=opponent_sid)
        socketio.emit('game_start', {'game_id': game_id, 'color': 'black', 'opponent': 'Anonymous'}, room=sid)
        
        print(f"Match created: {game_id}")
    else:
        # No one waiting, join queue
        waiting_queue.append(sid)
        emit('status_update', {'msg': 'Searching for opponent...'})

@socketio.on('make_move')
def handle_move(data):
    sid = request.sid
    if sid not in players:
        return

    game_id = players[sid]['game_id']
    game = active_games.get(game_id)
    
    if not game:
        return

    # Determine opponent
    opponent_sid = game['black'] if game['white'] == sid else game['white']
    
    # Relay move to opponent
    socketio.emit('move_relay', {
        'from': data['from'],
        'to': data['to'],
        'promotion': data.get('promotion')
    }, room=opponent_sid)

if __name__ == '__main__':
    # Use PORT env variable for Render.com
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
