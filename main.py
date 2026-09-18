import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Top Up")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инвентарь пользователя (скины, которые он отдает)
USER_INVENTORY = [
    {"id": "u1", "name": "P250 | Sand Dune", "price": 10.0, "img": "🔫"},
    {"id": "u2", "name": "AK-47 | Uncharted", "price": 25.0, "img": "🔫"},
    {"id": "u3", "name": "AWP | Atheris", "price": 60.0, "img": "🎯"},
    {"id": "u4", "name": "USP-S | Cyrex", "price": 120.0, "img": "🔫"},
]

# Доступные цели для апгрейда
TARGET_ITEMS = [
    {"id": "t1", "name": "AK-47 | Redline", "price": 100.0, "img": "🔥"},
    {"id": "t2", "name": "M4A4 | Neo-Noir", "price": 250.0, "img": "🦄"},
    {"id": "t3", "name": "AWP | Asiimov", "price": 500.0, "img": "⚡"},
    {"id": "t4", "name": "Knife | Doppler", "price": 1200.0, "img": "🔪"},
]

HOUSE_EDGE = 0.95  # Комиссия платформы 5%

class UpgradeRequest(BaseModel):
    user_item_id: str
    target_item_id: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Файл index.html не найден</h1>"

@app.get("/api/items")
async def get_items():
    return {
        "user_inventory": USER_INVENTORY,
        "target_items": TARGET_ITEMS
    }

@app.post("/api/upgrade")
async def upgrade(req: UpgradeRequest):
    user_item = next((i for i in USER_INVENTORY if i["id"] == req.user_item_id), None)
    target_item = next((i for i in TARGET_ITEMS if i["id"] == req.target_item_id), None)

    if not user_item or not target_item:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    if user_item["price"] >= target_item["price"]:
        raise HTTPException(status_code=400, detail="Цель должна быть дороже вашего скина")

    # Расчет шанса победы
    win_chance = (user_item["price"] / target_item["price"]) * 100 * HOUSE_EDGE
    win_chance = round(min(win_chance, 80.0), 2)

    roll = random.uniform(0, 100)
    is_win = roll <= win_chance

    winning_angle_max = (win_chance / 100) * 360

    if is_win:
        stop_angle = random.uniform(2, max(2, winning_angle_max - 2))
    else:
        stop_angle = random.uniform(winning_angle_max + 2, 358)

    return {
        "success": True,
        "is_win": is_win,
        "win_chance": win_chance,
        "roll": round(roll, 2),
        "stop_angle": round(stop_angle, 2),
        "user_item": user_item,
        "target_item": target_item
    }
