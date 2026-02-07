import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, send_from_directory, request, jsonify
import threading
import json
import os

# ==========================================
# 👇 CONFIGURATION (FILL THESE IN CAREFULLY)
# ==========================================
BOT_TOKEN = "8587196149:AAHUXp6ihV6lGrGdBiUkD2btujKHK1-I4dM"  # e.g., "123456:ABC-DEF..."
APP_URL = "https://lotus1.onrender.com" # e.g., "https://my-app.onrender.com"
# ==========================================

# Setup Paths (Fixes "Internal Server Error" by finding the exact file location)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=BASE_DIR)

# Setup Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Database File Path
DB_FILE = os.path.join(BASE_DIR, "user_data.json")

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

# --- FLASK ROUTES ---

@app.route('/')
def index():
    # This tries to send index.html from the SAME folder as this script
    try:
        return send_from_directory(BASE_DIR, 'index.html')
    except Exception as e:
        # If this fails, it will print the exact error in your cloud logs
        print(f"ERROR LOADING FILE: {e}")
        return f"CRITICAL ERROR: Could not find index.html. Details: {e}", 500

@app.route('/api/sync', methods=['POST'])
def sync_data():
    try:
        data = request.json
        user_id = str(data.get('userId', 'unknown'))
        db = load_db()
        db[user_id] = data
        save_db(db)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Sync Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- BOT ROUTES ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_name = message.from_user.first_name
        markup = InlineKeyboardMarkup()
        # The WebApp button
        markup.add(InlineKeyboardButton(text="⛏️ Play Squad Miner", web_app=WebAppInfo(url=APP_URL)))
        
        bot.reply_to(message, 
            f"👋 Welcome {user_name}!\n\nClick below to start mining crypto points.",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Bot Error: {e}")

# --- RUNNER ---

def run_flask():
    # Cloud servers provide a PORT env var. If missing, use 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    bot.remove_webhook() # Clears old issues
    bot.infinity_polling()

if __name__ == "__main__":
    # Run Flask in a separate thread
    t = threading.Thread(target=run_flask)
    t.start()
    
    # Run Bot in main thread
    run_bot()
