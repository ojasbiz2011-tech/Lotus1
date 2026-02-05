from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import game_engine
from typing import List, Dict

app = FastAPI()

# --- DATABASE (In-Memory) ---
users = {}

# GLOBAL STATE
# CHANGED: Starts at 0.00 now. Community builds it up!
GLOBAL_POOL = 0.00 
RECENT_LOGS = [] 

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/generate_level")
def get_level():
    return game_engine.generate_puzzle()

@app.post("/api/submit_game")
async def submit_game(req: Request):
    return {"status": "ok"}

@app.post("/api/ads/confirm")
async def confirm_ad(req: Request):
    global GLOBAL_POOL
    data = await req.json()
    uid = data.get("user_id")
    name = data.get("first_name", f"User {uid}") 

    if uid not in users:
        users[uid] = {"wallet": 0.0, "ads_watched": 0, "name": name}
    
    users[uid]["ads_watched"] += 1
    
    added_amount = 0.10
    GLOBAL_POOL += added_amount
    
    log_entry = f"{name} added ₹{added_amount:.2f}"
    RECENT_LOGS.insert(0, log_entry) 
    if len(RECENT_LOGS) > 20:
        RECENT_LOGS.pop()
        
    return {"status": "ok", "new_pool": GLOBAL_POOL}

@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    sorted_users = sorted(users.values(), key=lambda x: x['ads_watched'], reverse=True)
    user_data = users.get(user_id, {"wallet": 0.0, "ads_watched": 0, "name": "You"})
    try:
        rank = sorted_users.index(user_data) + 1
    except:
        rank = "-"

    return {
        "ads_watched": user_data["ads_watched"],
        "rank": rank,
        "global_pool": round(GLOBAL_POOL, 2),
        "recent_logs": RECENT_LOGS,
        "top_players": sorted_users[:5] 
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
