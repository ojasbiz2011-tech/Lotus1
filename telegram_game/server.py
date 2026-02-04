import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import uvicorn
import game_engine
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURATION ---
# REPLACE THIS WITH YOUR ACTUAL BOT TOKEN FROM BOTFATHER
BOT_TOKEN = "8587196149:AAHUXp6ihV6lGrGdBiUkD2btujKHK1-I4dM"
BASE_URL = "https://lotus-escape.onrender.com" 

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- DATABASE (In-Memory for MVP - Resets on restart) ---
# In production, use SQLite or PostgreSQL
users_db = {} 
# Structure: { user_id: { "score": 0, "ads_watched": 0, "wallet": 0.0, "payout_method": "" } }

revenue_pool = 0.0
PRIZE_PERCENTAGE = 0.60  # 60% to pool

# --- DATA MODELS ---
class Move(BaseModel):
    id: int
    col: int
    row: int

class GameSubmit(BaseModel):
    user_id: int
    initial_level: List[dict]
    moves: List[Move]

class AdWatch(BaseModel):
    user_id: int

# --- WEB ROUTES (The App) ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/generate_level")
def get_level():
    return game_engine.generate_puzzle()

@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "ads_watched": 0, "wallet": 0.0, "rank": 999}
    
    # Simple Ranking Logic
    sorted_users = sorted(users_db.items(), key=lambda x: x[1]['score'], reverse=True)
    rank = next((i+1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), 999)
    users_db[user_id]['rank'] = rank
    
    return users_db[user_id]

@app.post("/api/ads/confirm")
def confirm_ad(payload: AdWatch):
    user_id = payload.user_id
    if user_id not in users_db: users_db[user_id] = {"score": 0, "ads_watched": 0, "wallet": 0.0}
    
    users_db[user_id]["ads_watched"] += 1
    
    # Fake Revenue Logic
    global revenue_pool
    revenue_pool += 0.10 # Assume $0.10 per ad
    
    return {"status": "ok", "ads_watched": users_db[user_id]["ads_watched"]}

@app.post("/api/submit_game")
def submit_game(payload: GameSubmit):
    # Server-side validation using your Python Logic
    is_valid, moves_count = game_engine.validate_moves(payload.initial_level, payload.moves)
    
    if is_valid:
        user = users_db.get(payload.user_id)
        # Score calculation: 1000 base - (moves * 10). Max 1000.
        score = max(0, 1000 - (moves_count * 10))
        
        if score > user['score']:
            user['score'] = score
            
        return {"valid": True, "score": score, "new_total": user['score']}
    else:
        return {"valid": False, "reason": "Invalid moves detected"}

@app.get("/api/leaderboard")
def get_leaderboard():
    # Sort users by score
    sorted_users = sorted(users_db.items(), key=lambda x: x[1]['score'], reverse=True)
    top_10 = [{"user_id": k, "score": v['score'], "rank": i+1} for i, (k, v) in enumerate(sorted_users[:10])]
    return {"leaderboard": top_10, "prize_pool": revenue_pool * PRIZE_PERCENTAGE}

# --- TELEGRAM BOT ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🌲 **Welcome to Dense Wood Escape, {user.first_name}!**\n\n"
        "🧩 **Play Daily:** Solve the puzzle in fewer moves.\n"
        "💰 **Win Prizes:** Top players share the ad revenue pool.\n\n"
        "👇 Click below to start playing!"
    )
    
    # The Button that launches the Mini App
    keyboard = [[InlineKeyboardButton("🎮 Play Now", web_app=WebAppInfo(url=BASE_URL))]]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.run_polling()

if __name__ == "__main__":
    # We run the Web Server in a separate thread or just run this file
    # For simplicity in this guide, we run the web server here.
    # YOU MUST RUN THE BOT SEPARATELY IN A REAL APP, BUT THIS WORKS FOR MVP
    print("⚠️  To run the Bot, open a separate terminal and run this file modified, or just use the web API for now.")
    print(f"🚀 Server starting on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)