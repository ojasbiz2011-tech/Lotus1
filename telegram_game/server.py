import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, render_template, request, jsonify
import threading
import json
import os

# --- CONFIGURATION ---
# 1. Get token from @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# 2. You need an HTTPS URL for the Mini App. 
# If testing locally, run 'ngrok http 5000' and paste that URL here.
# If hosted on cloud, paste your cloud URL (e.g., https://my-app.onrender.com)
# DO NOT include a trailing slash (e.g. no / at end)
APP_URL = "https://YOUR-APP-URL.com" 

# --- SETUP ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__, template_folder='.') # Looks for index.html in same folder

# Simple JSON Database for "Cloud" Storage
DB_FILE = "user_data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- FLASK WEB ROUTES (The Game) ---

@app.route('/')
def index():
    # This serves your HTML file
    return render_template('index.html')

@app.route('/api/sync', methods=['POST'])
def sync_data():
    """Receives data from index.html and saves it to JSON file"""
    try:
        data = request.json
        user_id = str(data.get('userId', 'unknown'))
        
        # Load current DB
        db = load_db()
        
        # Update User Data
        db[user_id] = data
        
        # Save back to file
        save_db(db)
        
        return jsonify({"status": "success", "message": "Data saved to cloud"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Returns top 10 players for the leaderboard"""
    db = load_db()
    # Convert dict to list and sort by score
    players = []
    for uid, data in db.items():
        players.append({
            "name": f"User {uid}", # Or use username if you saved it
            "score": data.get('score', 0)
        })
    
    # Sort descending
    players.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(players[:10])

# --- TELEGRAM BOT ROUTES ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    # Create the button that opens the game
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        text="⛏️ Start Mining", 
        web_app=WebAppInfo(url=APP_URL)
    ))
    
    bot.reply_to(message, 
        f"👋 Welcome, {user_name}!\n\n"
        "Start mining now to enter the Weekly Prize Pool.\n"
        "Remember: You must stay in the app to mine!",
        reply_markup=markup
    )

# ... (Keep all your imports and bot logic the same) ...

# --- RUNNING BOTH ---
def run_flask():
    # UPDATE: Use the PORT provided by the cloud, or default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_bot():
    print("Bot is polling...")
    bot.infinity_polling()

if __name__ == "__main__":
    # We use threading to run Flask and Bot at the same time
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    run_bot()
