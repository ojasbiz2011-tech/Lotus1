import os
import threading
import json
import telebot
from flask import Flask, send_from_directory, request, jsonify
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ==========================================
# 👇 CONFIGURATION
# ==========================================
# 1. Get this from @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" 

# 2. Your Cloud URL (e.g., https://my-app-name.onrender.com)
# DO NOT put a slash (/) at the end.
APP_URL = "https://YOUR-APP-URL.com"
# ==========================================

# Setup: Define the exact folder where this script lives
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Setup Flask: Tell it to look for HTML files in the BASE_DIR
app = Flask(__name__, static_folder=BASE_DIR)

# Setup Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Database File (Saves user data in the same folder)
DB_FILE = os.path.join(BASE_DIR, "squad_data.json")

# --- DATABASE FUNCTIONS ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Database Error: {e}")

# --- WEB ROUTES (The Game) ---

@app.route('/')
def home():
    """Serves the game file"""
    try:
        # This sends the index.html file from the current directory
        return send_from_directory(BASE_DIR, 'index.html')
    except Exception as e:
        return f"<h1>Error: Could not find index.html</h1><p>Debug info: Looking in {BASE_DIR}</p><p>Error: {e}</p>", 500

@app.route('/<path:filename>')
def serve_static(filename):
    """Serves any other static files (images, css, js) if you add them later"""
    return send_from_directory(BASE_DIR, filename)

@app.route('/api/sync', methods=['POST'])
def sync_data():
    """Saves game progress to the server"""
    try:
        data = request.json
        user_id = str(data.get('userId', 'unknown'))
        
        # Simple Logic: Save data to JSON
        db = load_db()
        db[user_id] = data
        save_db(db)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Sync Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- TELEGRAM BOT ROUTES ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_first_name = message.from_user.first_name
        
        # Create the "Play" Button
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton(text="⛏️ Open Squad Miner", web_app=WebAppInfo(url=APP_URL))
        markup.add(btn)
        
        bot.reply_to(message, 
            f"👋 <b>Welcome, {user_first_name}!</b>\n\n"
            "Join your Squad and start mining to win the Weekly Prize Pool.\n"
            "<i>Tap the button below to start.</i>",
            reply_markup=markup,
            parse_mode="HTML"
        )
        print(f"Sent welcome message to {user_first_name}")
    except Exception as e:
        print(f"Bot Error: {e}")

# --- SERVER RUNNER ---

def run_flask():
    # Cloud servers provide a PORT variable. If not found, use 5000.
    port = int(os.environ.get("PORT", 5000))
    # '0.0.0.0' allows external access (required for cloud)
    app.run(host="0.0.0.0", port=port)

def run_bot():
    # Remove webhook to prevent conflicts with polling
    bot.remove_webhook()
    print("Bot started polling...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Start Bot in the main thread
    run_bot()
